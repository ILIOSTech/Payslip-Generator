#!/usr/bin/env python3
"""Local web UI for the payslip generator.

Run with `python3 app.py` and open http://127.0.0.1:5050 in a browser.
Lets you manage employees.csv via web forms and generate/download payslips
without touching the command line.
"""
from __future__ import annotations

import csv
import datetime
import io
import zipfile
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from main import REQUIRED_COLUMNS, VALID_EMPLOYEE_TYPES, generate_month, load_company, load_employees, slugify
from payslip.fy_utils import MONTH_NAMES, current_month_year, normalize_month_name
from payslip.importer import parse_employee_workbook

BASE_DIR = Path(__file__).resolve().parent
EMPLOYEES_PATH = BASE_DIR / "employees.csv"
COMPANY_PATH = BASE_DIR / "company_config.json"
OUTPUT_DIR = BASE_DIR / "output"

NUMERIC_FIELDS = ["pay_days", "basic", "sp_allowance", "ptax"]

app = Flask(__name__)
app.secret_key = "payslip-generator-local"


def read_employee_rows():
    if not EMPLOYEES_PATH.exists():
        return []
    with EMPLOYEES_PATH.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_employee_rows(rows):
    with EMPLOYEES_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def validate_employee_data(data: dict) -> str | None:
    for field in NUMERIC_FIELDS:
        try:
            float(data.get(field, ""))
        except ValueError:
            return "Pay Days, Basic, Sp Allowance and P.Tax must be numbers."
    if data.get("employee_type") not in VALID_EMPLOYEE_TYPES:
        return f"Employee Type must be one of: {', '.join(VALID_EMPLOYEE_TYPES)}."
    return None


def list_generated_months():
    months = []
    if not OUTPUT_DIR.exists():
        return months
    for fy_dir in OUTPUT_DIR.iterdir():
        if not fy_dir.is_dir():
            continue
        for month_dir in fy_dir.iterdir():
            if not month_dir.is_dir():
                continue
            try:
                sort_date = datetime.datetime.strptime(month_dir.name, "%b-%Y")
            except ValueError:
                continue
            register = sorted(month_dir.glob("Salary_Register_*.pdf"))
            payslip_dir = month_dir / "Payslips"
            payslips = sorted(payslip_dir.glob("*.pdf")) if payslip_dir.exists() else []
            months.append({
                "fy_label": fy_dir.name,
                "month_label": month_dir.name,
                "display": sort_date.strftime("%B %Y"),
                "sort_date": sort_date,
                "register": register[0].relative_to(OUTPUT_DIR).as_posix() if register else None,
                "payslips": [(p.stem, p.relative_to(OUTPUT_DIR).as_posix()) for p in payslips],
            })
    months.sort(key=lambda m: m["sort_date"], reverse=True)
    return months


@app.route("/")
def index():
    employees = read_employee_rows()
    company = load_company(COMPANY_PATH) if COMPANY_PATH.exists() else {"name": "", "address": ""}
    default_month, default_year = current_month_year()
    return render_template(
        "index.html",
        employees=employees,
        company=company,
        generated_months=list_generated_months(),
        month_names=MONTH_NAMES,
        default_month=default_month,
        default_year=default_year,
    )


@app.route("/employees/add", methods=["POST"])
def add_employee():
    rows = read_employee_rows()
    data = {col: request.form.get(col, "").strip() for col in REQUIRED_COLUMNS}

    if not data["employee_id"] or not data["name"]:
        flash("Name and Employee ID are required.", "error")
        return redirect(url_for("index"))
    if any(r["employee_id"] == data["employee_id"] for r in rows):
        flash(f"Employee ID '{data['employee_id']}' already exists.", "error")
        return redirect(url_for("index"))

    error = validate_employee_data(data)
    if error:
        flash(error, "error")
        return redirect(url_for("index"))

    rows.append(data)
    write_employee_rows(rows)
    flash(f"Added {data['name']}.", "success")
    return redirect(url_for("index"))


@app.route("/employees/upload", methods=["POST"])
def upload_employees():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Please choose an Excel file to upload.", "error")
        return redirect(url_for("index"))

    try:
        imported = parse_employee_workbook(io.BytesIO(file.read()), file.filename)
    except Exception as exc:
        flash(f"Could not read '{file.filename}': {exc}", "error")
        return redirect(url_for("index"))

    rows = read_employee_rows()
    existing_ids = {r["employee_id"] for r in rows}
    added, skipped = [], []
    for record in imported:
        if record["employee_id"] in existing_ids:
            skipped.append(record["employee_id"])
            continue
        rows.append(record)
        existing_ids.add(record["employee_id"])
        added.append(record["name"])
    write_employee_rows(rows)

    message = f"Imported {len(added)} employee(s) from {file.filename}."
    if skipped:
        message += f" Skipped (Employee ID already exists): {', '.join(skipped)}."
    flash(message, "success" if added else "error")
    return redirect(url_for("index"))


@app.route("/employees/<employee_id>/edit", methods=["GET", "POST"])
def edit_employee(employee_id):
    rows = read_employee_rows()
    row = next((r for r in rows if r["employee_id"] == employee_id), None)
    if row is None:
        flash(f"Employee '{employee_id}' not found.", "error")
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("edit_employee.html", employee=row)

    data = {col: request.form.get(col, "").strip() for col in REQUIRED_COLUMNS}
    data["employee_id"] = employee_id

    error = validate_employee_data(data)
    if error:
        flash(error, "error")
        return redirect(url_for("edit_employee", employee_id=employee_id))

    for i, r in enumerate(rows):
        if r["employee_id"] == employee_id:
            rows[i] = data
            break
    write_employee_rows(rows)
    flash(f"Updated {data['name']}.", "success")
    return redirect(url_for("index"))


@app.route("/employees/<employee_id>/delete", methods=["POST"])
def delete_employee(employee_id):
    rows = read_employee_rows()
    remaining = [r for r in rows if r["employee_id"] != employee_id]
    if len(remaining) == len(rows):
        flash(f"Employee '{employee_id}' not found.", "error")
    else:
        write_employee_rows(remaining)
        flash("Employee deleted.", "success")
    return redirect(url_for("index"))


@app.route("/generate", methods=["POST"])
def generate():
    try:
        month_name = normalize_month_name(request.form.get("month_name", ""))
        year = int(request.form["year"])
    except (KeyError, ValueError) as exc:
        flash(f"Invalid month/year: {exc}", "error")
        return redirect(url_for("index"))

    try:
        company = load_company(COMPANY_PATH)
        employees = load_employees(EMPLOYEES_PATH)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("index"))

    generate_month(company, employees, month_name, year, OUTPUT_DIR)
    flash(f"Generated payslips for {month_name} {year}.", "success")
    return redirect(url_for("index"))


def _safe_output_path(relpath: str) -> Path:
    output_root = OUTPUT_DIR.resolve()
    candidate = (OUTPUT_DIR / relpath).resolve()
    if candidate != output_root and output_root not in candidate.parents:
        raise ValueError("Invalid path")
    if not candidate.is_file():
        raise FileNotFoundError(relpath)
    return candidate


@app.route("/download/<path:relpath>")
def download(relpath):
    try:
        path = _safe_output_path(relpath)
    except (ValueError, FileNotFoundError):
        flash("File not found.", "error")
        return redirect(url_for("index"))
    return send_file(path, as_attachment=True)


@app.route("/download-zip/<fy_label_value>/<month_label>")
def download_zip(fy_label_value, month_label):
    output_root = OUTPUT_DIR.resolve()
    month_dir = (OUTPUT_DIR / fy_label_value / month_label).resolve()
    if output_root not in month_dir.parents or not month_dir.is_dir():
        flash("Generated month not found.", "error")
        return redirect(url_for("index"))

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in month_dir.rglob("*.pdf"):
            zf.write(file_path, file_path.relative_to(month_dir))
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"{month_label}.zip", mimetype="application/zip")


if __name__ == "__main__":
    app.run(debug=True, port=5050)

#!/usr/bin/env python3
"""Automated payslip generator.

Reads employee master data (Basic, Sp Allowance, P.Tax and Pay Days are the
user inputs) from a CSV file and generates payslips for a single month:

  - one PDF per employee containing that month's payslip, and
  - one "Salary Register" PDF summarising every employee for that month.

Since attendance (Pay Days) and pay can change from month to month, this
generates one month at a time rather than a whole financial year in one
batch - update employees.csv (or use the web UI) before each month's run.
"""
import argparse
import csv
import json
import re
from pathlib import Path

from payslip.fy_utils import current_month_year, fy_label, fy_start_year_for_month, normalize_month_name
from payslip.models import LABOUR, PERMANENT, Employee, compute_payslip
from payslip.pdf_writer import build_employee_pdf, build_register_pdf

REQUIRED_COLUMNS = [
    "name", "designation", "employee_id", "employee_type", "date_of_joining", "uan",
    "pay_days", "basic", "sp_allowance", "ptax",
]
VALID_EMPLOYEE_TYPES = (PERMANENT, LABOUR)


def load_employees(csv_path: Path) -> list:
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = [col for col in REQUIRED_COLUMNS if col not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{csv_path} is missing required column(s): {', '.join(missing)}")
        employees = []
        for row in reader:
            if not row.get("name", "").strip():
                continue
            employee_type = row["employee_type"].strip()
            if employee_type not in VALID_EMPLOYEE_TYPES:
                raise ValueError(
                    f"{csv_path}: employee '{row['name']}' has employee_type "
                    f"'{employee_type}', expected one of {VALID_EMPLOYEE_TYPES}"
                )
            employees.append(Employee(
                name=row["name"].strip(),
                designation=row["designation"].strip(),
                employee_id=row["employee_id"].strip(),
                employee_type=employee_type,
                date_of_joining=row["date_of_joining"].strip(),
                uan=row["uan"].strip(),
                pay_days=float(row["pay_days"]),
                basic=float(row["basic"]),
                sp_allowance=float(row["sp_allowance"]),
                ptax=float(row["ptax"]),
            ))
        if not employees:
            raise ValueError(f"No employee rows found in {csv_path}")
        return employees


def load_company(json_path: Path) -> dict:
    with json_path.open(encoding="utf-8") as f:
        company = json.load(f)
    for key in ("name", "address"):
        if key not in company:
            raise ValueError(f"{json_path} is missing required key: {key}")
    return company


def slugify(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")


def generate_month(company: dict, employees: list, month_name: str, year: int, out_dir: Path) -> Path:
    fy_start_year = fy_start_year_for_month(month_name, year)
    month_dir = out_dir / fy_label(fy_start_year) / f"{month_name[:3]}-{year}"
    payslips_dir = month_dir / "Payslips"
    payslips_dir.mkdir(parents=True, exist_ok=True)

    results = [compute_payslip(emp) for emp in employees]

    for employee, result in zip(employees, results):
        build_employee_pdf(company, [(month_name, year, result)], payslips_dir / f"{slugify(employee.name)}.pdf")

    register_path = month_dir / f"Salary_Register_{month_name[:3]}-{year}.pdf"
    build_register_pdf([(month_name, year, results)], register_path)
    return month_dir


def main():
    parser = argparse.ArgumentParser(description="Generate payslips for a single month.")
    parser.add_argument("--employees", default="employees.csv", help="Path to the employee master CSV.")
    parser.add_argument("--company", default="company_config.json", help="Path to the company config JSON.")
    parser.add_argument("--month", default=None, help="Month name, e.g. April. Defaults to the current month.")
    parser.add_argument("--year", type=int, default=None, help="Calendar year, e.g. 2025. Defaults to the current year.")
    parser.add_argument("--out", default="output", help="Output directory (default: output).")
    args = parser.parse_args()

    default_month, default_year = current_month_year()
    month_name = normalize_month_name(args.month) if args.month else default_month
    year = args.year if args.year is not None else default_year
    out_dir = Path(args.out)

    company = load_company(Path(args.company))
    employees = load_employees(Path(args.employees))

    month_dir = generate_month(company, employees, month_name, year, out_dir)
    print(f"Generated {month_name} {year} -> {month_dir}")


if __name__ == "__main__":
    main()

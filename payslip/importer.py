"""Scrape employee master data out of an uploaded Excel register (.xls/.xlsx).

Expects a sheet with a header row containing column names such as
"Employee Name", "Designation", "Employee ID", "Date of Joining", "Pay Days",
"UAN Number", "Basic", "Sp Allowance" and "P.Tax" - i.e. the same layout as
the existing "Sheet1" salary register tab. Computed columns (Gross, PF,
ESIC, Net, Bonus, CTC) are ignored since this tool recalculates them.
"""
import datetime
import io

import openpyxl
import xlrd

HEADER_ALIASES = {
    "employee name": "name",
    "name": "name",
    "designation": "designation",
    "employee id": "employee_id",
    "employee type": "employee_type",
    "date of joining": "date_of_joining",
    "pay days": "pay_days",
    "uan number": "uan",
    "uan": "uan",
    "basic": "basic",
    "sp allowance": "sp_allowance",
    "special allowance": "sp_allowance",
    "p.tax": "ptax",
    "ptax": "ptax",
}

NUMERIC_FIELDS = {"pay_days", "basic", "sp_allowance", "ptax"}
REQUIRED_FOR_ROW = ("name", "employee_id")


def _normalize(text) -> str:
    return str(text).strip().lower() if text is not None else ""


def _sheet_rows_openpyxl(file_obj):
    wb = openpyxl.load_workbook(file_obj, data_only=True, read_only=True)
    for ws in wb.worksheets:
        yield [[cell for cell in row] for row in ws.iter_rows(values_only=True)]


def _sheet_rows_xlrd(file_obj):
    wb = xlrd.open_workbook(file_contents=file_obj.read())
    for sheet in wb.sheets():
        yield [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]


def _find_header(rows):
    for row_idx, row in enumerate(rows):
        normalized = [_normalize(v) for v in row]
        if "employee name" in normalized and "basic" in normalized:
            columns = {}
            for col_idx, header in enumerate(normalized):
                field = HEADER_ALIASES.get(header)
                if field:
                    columns[field] = col_idx
            if "name" in columns and "employee_id" in columns:
                return row_idx, columns
    return None, None


def _clean_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.strftime("%d.%m.%Y")
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return str(value).strip()


def _clean_number(value):
    if value is None or value == "":
        return 0.0
    if isinstance(value, str):
        value = value.replace(",", "").strip()
        if value == "":
            return 0.0
    return float(value)


def parse_employee_workbook(file_obj, filename: str) -> list:
    """Returns a list of employee dicts (matching main.REQUIRED_COLUMNS, minus
    employee_type which defaults to "Permanent" unless present in the sheet)."""
    if filename.lower().endswith(".xls"):
        sheets = _sheet_rows_xlrd(file_obj)
    elif filename.lower().endswith(".xlsx"):
        sheets = _sheet_rows_openpyxl(file_obj)
    else:
        raise ValueError("Please upload a .xls or .xlsx file.")

    for rows in sheets:
        header_row_idx, columns = _find_header(rows)
        if header_row_idx is None:
            continue

        records = []
        for row in rows[header_row_idx + 1:]:
            if not any(row):
                continue
            record = {}
            for field, col_idx in columns.items():
                value = row[col_idx] if col_idx < len(row) else None
                record[field] = _clean_number(value) if field in NUMERIC_FIELDS else _clean_text(value)
            if not all(record.get(field) for field in REQUIRED_FOR_ROW):
                continue
            record.setdefault("employee_type", "Permanent")
            for field in ("designation", "date_of_joining", "uan"):
                record.setdefault(field, "")
            for field in NUMERIC_FIELDS:
                record.setdefault(field, 0.0)
            if record["employee_type"] not in ("Permanent", "Labour"):
                record["employee_type"] = "Permanent"
            records.append(record)
        if records:
            return records

    raise ValueError(
        "Could not find a recognizable employee table in this file "
        "(expected columns like 'Employee Name', 'Designation', 'Basic', ...)."
    )

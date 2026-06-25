# Payslip Generator

An automated payslip generator for ILIOS Technology. Manage employees, then generate that month's payslips (and a salary register) as properly aligned PDFs — either from the command line or a local web UI.

## Features

- **Two employee categories** — Permanent staff (26 standard working days/month) and Labour (30 days, no-work-no-pay). Pay Days below the standard automatically prorate Basic, Sp Allowance, and everything calculated from them.
- **Month-by-month generation** — generates one month at a time (not a whole year in a batch), since attendance and pay can change every month. Previously generated months are never overwritten.
- **PDF output** — one PDF per employee per month, plus a Salary Register PDF summarising everyone for that month, all properly boxed/aligned and branded with the company logo.
- **Web UI** — add/edit/delete employees, import a batch of employees from an existing Excel register, generate a month, and download the results — all without touching the command line.
- **Excel import** — upload an `.xls`/`.xlsx` register (Employee Name, Designation, Employee ID, Date of Joining, Pay Days, UAN Number, Basic, Sp Allowance, P.Tax) and it scrapes the rows straight into your employee list.
- **Optional login** — the web app can be locked behind a username/password for deployment; locally it stays open by default.

## Payroll formulas

For each employee, per month:

```
standard_days     = 26 (Permanent) or 30 (Labour)
attendance_ratio  = min(Pay Days, standard_days) / standard_days

Basic (earned)        = Basic input        × attendance_ratio
Sp Allowance (earned) = Sp Allowance input × attendance_ratio
Gross                  = Basic (earned) + Sp Allowance (earned)

PF   Employee's Contribution = 12%   × Basic (earned)
PF   Employer's Contribution = 13%   × Basic (earned)
ESIC Employee's Contribution = 0.75% × Gross
ESIC Employer's Contribution = 3.25% × Gross

Net = Gross − PF (Employee) − ESIC (Employee) − P.Tax
CTC = Gross + PF (Employer) + ESIC (Employer)
```

Basic, Sp Allowance, P.Tax, Employee Type, and Pay Days are all per-employee inputs you control via the CSV or the web UI.

## Project structure

```
app.py                  Flask web UI (local server)
main.py                 CLI entry point + employee/company CSV-JSON loading
employees.csv           Employee master data (editable directly or via the web UI)
company_config.json     Company name & address shown on payslips
requirements.txt         Python dependencies
static/                 Logo + stylesheet for the web UI
templates/              Web UI pages (Jinja2)
payslip/
  models.py             Employee/PayslipResult dataclasses + the payroll formulas
  fy_utils.py           Month/financial-year helpers
  money_utils.py        Indian digit grouping, amount-in-words
  pdf_writer.py         Builds the payslip & salary register PDFs (reportlab)
  importer.py           Scrapes employee rows out of an uploaded Excel register
  excel_writer.py        (legacy) Excel-based payslip/register writer, unused by default
output/                 Generated PDFs land here, organised as FY<year>-<year+1>/<Mon>-<year>/
```

## Setup

```bash
cd "Payslip Generator"
pip3 install -r requirements.txt
```

## Usage

### Web UI (recommended)

```bash
python3 app.py
```

Open **http://127.0.0.1:5050**. From there you can:

- Add, edit, or delete employees, or **import** them from an existing Excel register.
- Pick a **Month** and **Year**, then click **Generate** to produce that month's payslips and salary register.
- Download individual PDFs, or **Download All (.zip)** for a given month.

### Command line

```bash
python3 main.py --month April --year 2025
```

Omit `--month`/`--year` to default to the current month. Useful flags:

| Flag | Default | Purpose |
|---|---|---|
| `--employees` | `employees.csv` | Path to the employee master CSV |
| `--company` | `company_config.json` | Path to the company info JSON |
| `--month` | current month | Month name, e.g. `April` |
| `--year` | current year | Calendar year, e.g. `2025` |
| `--out` | `output` | Output directory |

## Employee data (`employees.csv`)

| Column | Meaning |
|---|---|
| `name`, `designation`, `employee_id`, `date_of_joining`, `uan` | Employee details |
| `employee_type` | `Permanent` or `Labour` |
| `pay_days` | Days actually present this month (out of 26 or 30) |
| `basic`, `sp_allowance` | Full monthly entitlement at 100% attendance |
| `ptax` | Professional Tax for the month |

## Deploying (e.g. Render)

This is a Flask web app, not a static site — pick **Web Service**, not "Static Site" (no Publish Directory needed).

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Environment variables:**
  - `SECRET_KEY` — any random string
  - `APP_USERNAME` / `APP_PASSWORD` — set both to require login; omit either to leave the site open
  - `DATA_DIR` — path to a mounted persistent disk (e.g. `/var/data`) so `employees.csv` and generated PDFs survive redeploys; defaults to the project folder if unset

After the first deploy with a fresh disk, re-add your employees via the web UI's Excel import (or recreate `employees.csv` at `DATA_DIR`).

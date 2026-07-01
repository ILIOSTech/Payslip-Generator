# Payslip Generator

> Automated monthly payslip generation for **ILIOS Technology** — manage employees, generate legally-structured PDFs for any month, and download them individually or as a ZIP archive.

Built with Python · Flask · ReportLab · openpyxl

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Getting Started](#getting-started)
4. [Running the Web UI](#running-the-web-ui)
5. [Using the CLI](#using-the-cli)
6. [Configuration Files](#configuration-files)
   - [company_config.json](#company_configjson)
   - [employees.csv](#employeescsv)
7. [Payroll Calculations](#payroll-calculations)
8. [Output Structure](#output-structure)
9. [Environment Variables](#environment-variables)
10. [Deployment on Render](#deployment-on-render)
11. [Project Structure](#project-structure)
12. [Troubleshooting](#troubleshooting)

---

## Features

| Feature | Description |
|---|---|
| **Month-by-month generation** | Generate payslips for one month at a time. Previously generated months are never overwritten, so each month can have its own Pay Days (attendance). |
| **Two employee categories** | `Permanent` (26 standard days/month) and `Labour` (30 days, no-work-no-pay). Absences prorate Basic, Sp Allowance, PF, and ESIC automatically. |
| **PDF payslips** | Each employee gets a branded, boxed, print-ready PDF with logo, stamp, and Authorised Signatory line. |
| **Salary Register PDF** | One landscape summary PDF per month covering all employees, with column totals. |
| **Web UI** | Full dashboard — add/edit/delete employees, bulk import from Excel, generate, and download. No command line needed. |
| **Excel import** | Upload a `.xls`/`.xlsx` register and the app scrapes employee rows directly into your employee list. |
| **Optional login** | Set `APP_USERNAME`/`APP_PASSWORD` env vars to gate the site behind a login page. Locally those are unset, so the site stays open. |
| **Cloud-ready** | Runs on Render (or any Python host) via gunicorn. Persistent disk support for data survival across redeploys. |

---

## Tech Stack

| Component | Library / Version |
|---|---|
| Web framework | Flask 3.1.3 |
| PDF generation | ReportLab 5.0.0 |
| Excel read/write | openpyxl 3.1.5 (xlsx) · xlrd 2.0.2 (xls) |
| Image handling | Pillow 11.3.0 |
| Production server | gunicorn 23.0.0 |
| PDF font (Unicode ₹) | DejaVu Sans (bundled — no system font dependency) |
| Runtime | Python 3.9+ |

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- `pip3`

### Installation

```bash
git clone https://github.com/ILIOSTech/Payslip-Generator.git
cd "Payslip Generator"
pip3 install -r requirements.txt
```

That's it — no database, no Docker, no build step.

---

## Running the Web UI

```bash
python3 app.py
```

Open **http://127.0.0.1:5050** in your browser.

### Web UI Walkthrough

#### 1 — Employees

Manage your employee roster before generating each month's payslips.

| Action | How |
|---|---|
| Add one employee | Fill in the **Add Employee** form and click **Add Employee** |
| Edit an employee | Click **Edit** on any row, change the fields, click **Save Changes** |
| Delete one employee | Click **Delete** on that row |
| Delete all employees | Click **Delete All** (confirmation required) |
| Import a batch | Click **Choose file**, select a `.xls`/`.xlsx` register, click **Upload & Import** |

> **Pay Days** is the most important field to update each month. It represents the number of days the employee actually worked. For Permanent staff the max is 26; for Labour the max is 30. A lower value proportionally reduces Gross, PF, and ESIC.

#### 2 — Generate Payslips

Select a **Month** and **Year**, then click **Generate**.

The app:
1. Reads the current employee list and all their pay values.
2. Calculates Gross, PF, ESIC, Net, and CTC for every employee.
3. Writes one PDF per employee and one Salary Register PDF into `output/`.

Each monthly run is independent. Regenerating June does not touch May's files.

#### 3 — Generated Months

Download links appear for each generated month:

- **Salary Register** — landscape PDF listing all employees for that month with totals.
- **[Employee Name]** — individual payslip PDF for that employee.
- **Download All (.zip)** — everything for that month in a single archive.

---

## Using the CLI

Generate payslips without starting the web server:

```bash
python3 main.py --month April --year 2025
```

Defaults to the current calendar month and year if omitted.

### CLI Flags

| Flag | Default | Description |
|---|---|---|
| `--month` | Current month | Month name — e.g. `April`, `january` (case-insensitive), or abbreviation `Apr` |
| `--year` | Current year | Calendar year as an integer — e.g. `2025` |
| `--employees` | `employees.csv` | Path to the employee master CSV |
| `--company` | `company_config.json` | Path to the company info JSON |
| `--out` | `output` | Root output directory |

### Examples

```bash
# Generate current month with default files
python3 main.py

# Generate a specific past month
python3 main.py --month March --year 2025

# Use a different employee file and output location
python3 main.py --month June --year 2026 \
    --employees /data/employees.csv \
    --out /data/output
```

---

## Configuration Files

### `company_config.json`

Holds the company name and address printed at the top of every payslip.

```json
{
  "name": "ILIOS TECHNOLOGY",
  "address": "9 RAJ KUMAR BOSE LANE KOLKATA 700013"
}
```

Edit this file to change the header on all future payslips. Existing generated PDFs are not affected.

---

### `employees.csv`

One row per employee. This file is the single source of truth — the web UI reads and writes it directly.

#### Column reference

| Column | Type | Description |
|---|---|---|
| `name` | string | Employee's full name |
| `designation` | string | Job title / designation |
| `employee_id` | string | Unique employee ID (e.g. `IT2223-001`) |
| `employee_type` | `Permanent` or `Labour` | Determines standard working days (26 or 30) |
| `date_of_joining` | string | Formatted as `DD.MM.YYYY` |
| `uan` | string | Universal Account Number (PF) |
| `pay_days` | number | Days present this month. Cap: 26 for Permanent, 30 for Labour |
| `basic` | number | Full monthly Basic salary at 100% attendance |
| `sp_allowance` | number | Full monthly Special Allowance at 100% attendance |
| `ptax` | number | Professional Tax amount for the month |

#### Example row

```
Samim Ali Mondal,Sr Project Manager,IT2223-001,Permanent,12.12.2022,101205089994,26,17382,17382,130
```

> **Important:** `basic` and `sp_allowance` represent the full-month entitlement. If `pay_days` is less than the standard, both values are prorated automatically — do **not** pre-adjust them for absences.

#### Importing from Excel

You can upload an existing register spreadsheet (`.xls` or `.xlsx`) instead of filling the CSV manually. The importer looks for a row containing column headers like `Employee Name`, `Basic`, `P.Tax`, etc., and maps them automatically. Duplicate Employee IDs are skipped; new employees default to `Permanent` — edit the type afterward if any are Labour.

---

## Payroll Calculations

All calculations happen in `payslip/models.py`. The formulas are:

```
standard_days    = 26  if employee_type == "Permanent"
                 = 30  if employee_type == "Labour"

attendance_ratio = min(pay_days, standard_days) / standard_days

basic_earned     = basic        × attendance_ratio
sp_earned        = sp_allowance × attendance_ratio
gross            = basic_earned + sp_earned

PF  (Employee)   = 12%    × basic_earned
PF  (Employer)   = 13%    × basic_earned
ESIC (Employee)  = 0.75%  × gross
ESIC (Employer)  = 3.25%  × gross

net              = gross − PF(Employee) − ESIC(Employee) − ptax
ctc              = gross + PF(Employer) + ESIC(Employer)
```

### Worked example

Employee: Samim Ali Mondal · Permanent · Pay Days 24 / 26

| Item | Calculation | Amount |
|---|---|---|
| Attendance ratio | 24 ÷ 26 | 0.9231 |
| Basic earned | 17,382 × 0.9231 | ₹16,044.92 |
| Sp Allowance earned | 17,382 × 0.9231 | ₹16,044.92 |
| **Gross** | 16,044.92 + 16,044.92 | **₹32,089.84** |
| PF (Employee) | 12% × 16,044.92 | ₹1,925.39 |
| PF (Employer) | 13% × 16,044.92 | ₹2,085.84 |
| ESIC (Employee) | 0.75% × 32,089.84 | ₹240.67 |
| ESIC (Employer) | 3.25% × 32,089.84 | ₹1,042.92 |
| P.Tax | (user input) | ₹130.00 |
| **Net Pay** | 32,089.84 − 1,925.39 − 240.67 − 130.00 | **₹29,793.78** |
| **Monthly CTC** | 32,089.84 + 2,085.84 + 1,042.92 | **₹35,218.60** |

---

## Output Structure

Generated PDFs are organised under `output/` by financial year and month:

```
output/
└── FY2025-2026/
    ├── Apr-2025/
    │   ├── Salary_Register_Apr-2025.pdf
    │   └── Payslips/
    │       ├── Samim_Ali_Mondal.pdf
    │       ├── Dipali_Mondal.pdf
    │       └── Debraj_Podder.pdf
    ├── May-2025/
    │   └── ...
    └── Mar-2026/
        └── ...
```

Indian financial years run **April to March**. January 2026 is therefore filed under `FY2025-2026`. Each monthly folder is independent — regenerating one month never affects the others.

---

## Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `PORT` | No | `5050` | Port the Flask dev server listens on |
| `SECRET_KEY` | Recommended in production | `payslip-generator-local` | Flask session signing key — set to a random string when deploying |
| `APP_USERNAME` | No | *(unset)* | Username for login gate. **Both** `APP_USERNAME` and `APP_PASSWORD` must be set to enable auth |
| `APP_PASSWORD` | No | *(unset)* | Password for login gate |
| `DATA_DIR` | No | Project folder | Directory for `employees.csv` and `output/`. Point this at a persistent disk in production so data survives redeploys |

### Setting variables locally (for testing)

```bash
# Mac/Linux
APP_USERNAME=admin APP_PASSWORD=mysecret python3 app.py

# Windows PowerShell
$env:APP_USERNAME="admin"; $env:APP_PASSWORD="mysecret"; python3 app.py
```

---

## Deployment on Render

> This is a **Flask web application**, not a static site. When creating the Render service, choose **Web Service** — not "Static Site" (there is no Publish Directory).

### Step-by-step

1. Push your code to GitHub (already done — `ILIOSTech/Payslip-Generator`).

2. On [render.com](https://render.com), click **New → Web Service** and connect your repo.

3. Fill in the build and start settings:

   | Field | Value |
   |---|---|
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `gunicorn app:app --timeout 120` |

   > The `--timeout 120` gives the worker 2 minutes per request. The default 30 seconds is too short when generating payslips for a large number of employees.

4. Add **Environment Variables** in the Render dashboard:

   | Key | Value |
   |---|---|
   | `SECRET_KEY` | Any long random string (e.g. generate with `python3 -c "import secrets; print(secrets.token_hex(32))"`) |
   | `APP_USERNAME` | Your chosen login username |
   | `APP_PASSWORD` | Your chosen login password |
   | `DATA_DIR` | `/var/data` (or wherever you mount the disk below) |

5. Add a **Persistent Disk** under your service's Disks tab:

   - Mount path: `/var/data` (match what you set for `DATA_DIR`)
   - Size: 1 GB is more than enough

6. Deploy. After the first deploy, use the web UI's **Upload & Import** to reload your employee data — the fresh disk starts empty.

### Updating the deployment

Merge changes to your `main` branch — Render auto-deploys. `employees.csv` and `output/` live on the persistent disk and are not touched by redeploys.

---

## Project Structure

```
Payslip Generator/
│
├── app.py                  Flask web application — routes, login gate,
│                           employee CRUD, upload, generate, download
│
├── main.py                 CLI entry point. Also contains load_employees(),
│                           load_company(), generate_month(), slugify()
│                           (imported by app.py)
│
├── employees.csv           Employee master data. Edited via the web UI
│                           or directly with any text/spreadsheet editor.
│
├── company_config.json     Company name and address for payslip headers.
│
├── requirements.txt        Python dependencies (pip install -r requirements.txt)
│
├── static/
│   ├── logo.png            Company logo — shown in the web UI top bar
│   │                       and embedded in every payslip PDF.
│   ├── stamp.jpg           Company seal/stamp — printed above "Authorised
│   │                       Signatory" on each payslip.
│   └── style.css           Web UI stylesheet (design system with CSS variables).
│
├── templates/
│   ├── base.html           Shared layout — sticky top bar, session-aware
│   │                       logout link.
│   ├── index.html          Main dashboard — employee table, forms,
│   │                       generate section, downloads.
│   ├── edit_employee.html  Single-employee edit form.
│   └── login.html          Login page (shown when APP_USERNAME/PASSWORD set).
│
└── payslip/                Core Python package
    ├── models.py           Employee and PayslipResult dataclasses.
    │                       Contains all payroll formulas (PF, ESIC, Net, CTC).
    │
    ├── fy_utils.py         Month/financial-year helpers:
    │                       normalize_month_name(), current_month_year(),
    │                       fy_start_year_for_month(), fy_label().
    │
    ├── money_utils.py      Indian digit-grouping formatter (₹12,34,567.00),
    │                       amount_in_words() for the payslip footer line.
    │
    ├── pdf_writer.py       Builds payslip and salary register PDFs using
    │                       ReportLab. Fonts are bundled (fonts/ subfolder)
    │                       for consistent rendering on any OS.
    │
    ├── importer.py         Parses uploaded .xls/.xlsx register files and
    │                       returns a list of employee dicts for import.
    │
    ├── fonts/              Bundled DejaVu Sans TTF files (open-license).
    │                       Used so the ₹ Rupee symbol renders correctly on
    │                       both macOS and Linux deployment servers.
    │
    └── excel_writer.py     Legacy Excel-based payslip writer (kept for
                            reference; not used in the default PDF workflow).
```

---

## Troubleshooting

### Internal Server Error when generating a large number of payslips

**Cause:** gunicorn's default worker timeout is 30 seconds. Generating payslips for many employees — especially the first run when images are first cached — can exceed this.

**Fix:** Add `--timeout 120` (or higher) to the Start Command on Render:

```
gunicorn app:app --timeout 120
```

For very large organisations (500+ employees), use `--timeout 300`.

---

### The Rupee symbol (₹) shows as a box or "Rs." in PDFs

**Cause:** This happened when PDFs were generated on a server that didn't have the macOS Georgia font, which was the original fallback. The project now bundles **DejaVu Sans** (`payslip/fonts/`) specifically to avoid any OS-level font dependency.

**Fix:** Make sure `payslip/fonts/DejaVuSans.ttf` (and the `-Bold`, `-Oblique` variants) are committed to the repository and deployed. Run `pip install -r requirements.txt` and redeploy.

---

### `employees.csv` or generated PDFs disappear after a Render redeploy

**Cause:** Render's filesystem is ephemeral — it resets on every deploy unless a Persistent Disk is attached.

**Fix:** Attach a Persistent Disk in Render (Disks tab) and set the `DATA_DIR` environment variable to its mount path (e.g. `/var/data`). See [Deployment on Render](#deployment-on-render) for the full setup.

---

### `ValueError: 'xyz' is not a valid month name`

The CLI and web UI both accept full month names (`April`) or three-letter abbreviations (`Apr`), case-insensitive. Valid names: `April`, `May`, `June`, `July`, `August`, `September`, `October`, `November`, `December`, `January`, `February`, `March`.

---

### Port 5050 already in use

Another process is holding the port. Either stop it:

```bash
lsof -ti:5050 | xargs kill -9
```

Or run the app on a different port:

```bash
PORT=8080 python3 app.py
```

---

*ILIOS Technology · Payslip Generator · Python 3.9+*

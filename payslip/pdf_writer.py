from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .money_utils import amount_in_words, indian_currency

LOGO_PATH = Path(__file__).resolve().parent.parent / "static" / "logo.png"
LOGO_HEIGHT_PT = 30
STAMP_PATH = Path(__file__).resolve().parent.parent / "static" / "stamp.jpg"
STAMP_HEIGHT_PT = 85

# Helvetica (a base-14 PDF font) has no glyph for the Rupee sign (U+20B9), so it
# renders as a missing-glyph box. DejaVu Sans (bundled here, not relying on
# whatever happens to be installed on the host OS) does have the glyph, so it's
# used for all PDF text - this also keeps rendering identical locally and on
# any deployment server.
FONTS_DIR = Path(__file__).resolve().parent / "fonts"
pdfmetrics.registerFont(TTFont("DejaVuSans", str(FONTS_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", str(FONTS_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-Oblique", str(FONTS_DIR / "DejaVuSans-Oblique.ttf")))

HEADER_FILL = HexColor("#DDEBF7")
COMPANY_COLOR = HexColor("#ED7D31")
ADDRESS_COLOR = HexColor("#2E5496")
GRID_COLOR = colors.black
GRID_WIDTH = 0.5

COMPANY_STYLE = ParagraphStyle("company", fontName="DejaVuSans-Bold", fontSize=18, textColor=COMPANY_COLOR, leading=22)
ADDRESS_STYLE = ParagraphStyle("address", fontName="DejaVuSans-Bold", fontSize=10.5, textColor=ADDRESS_COLOR,
                                alignment=1, leading=14)
TITLE_STYLE = ParagraphStyle("title", fontName="DejaVuSans-Bold", fontSize=10.5, alignment=1, leading=16)
LABEL_STYLE = ParagraphStyle("label", fontName="DejaVuSans-Bold", fontSize=9, leading=12)
VALUE_STYLE = ParagraphStyle("value", fontName="DejaVuSans", fontSize=9, leading=12)
VALUE_RIGHT_STYLE = ParagraphStyle("value_right", parent=VALUE_STYLE, alignment=2)
LABEL_RIGHT_STYLE = ParagraphStyle("label_right", parent=LABEL_STYLE, alignment=2)
HEADER_CELL_STYLE = ParagraphStyle("header_cell", fontName="DejaVuSans-Bold", fontSize=9, alignment=1)
NET_PAY_STYLE = ParagraphStyle("net_pay", fontName="DejaVuSans-Bold", fontSize=15, alignment=1)
WORDS_STYLE = ParagraphStyle("words", fontName="DejaVuSans-Oblique", fontSize=9, alignment=1)
SIGNATORY_STYLE = ParagraphStyle("signatory", fontName="DejaVuSans-Bold", fontSize=9, alignment=2)


def _money(value):
    return Paragraph(indian_currency(value), VALUE_RIGHT_STYLE)


def _money_bold(value):
    return Paragraph(indian_currency(value), LABEL_RIGHT_STYLE)


def _image_at_height(path: Path, height_pt: float):
    if not path.exists():
        return None
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        ratio = im.width / im.height
    return Image(str(path), width=height_pt * ratio, height=height_pt)


def _logo_image():
    return _image_at_height(LOGO_PATH, LOGO_HEIGHT_PT)


def _header_block(company, month_name, year, col_widths):
    content_width = sum(col_widths)
    logo = _logo_image()
    if logo is not None:
        header_table = Table(
            [[logo, Paragraph(company["name"], COMPANY_STYLE)]],
            colWidths=[LOGO_HEIGHT_PT * 1.3, content_width - LOGO_HEIGHT_PT * 1.3],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ]))
    else:
        header_table = Table([[Paragraph(company["name"], COMPANY_STYLE)]], colWidths=[content_width])

    title_table = Table(
        [[Paragraph(f"Payslip for the Month of {month_name.upper()}, {year}", TITLE_STYLE)]],
        colWidths=[content_width],
    )
    title_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), GRID_WIDTH, GRID_COLOR),
        ("LINEBELOW", (0, 0), (-1, 0), GRID_WIDTH, GRID_COLOR),
        ("TOPPADDING", (0, 0), (-1, 0), 4),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
    ]))

    return [
        header_table,
        Spacer(1, 2),
        Paragraph(company["address"], ADDRESS_STYLE),
        Spacer(1, 4),
        title_table,
        Spacer(1, 8),
    ]


def _detail_and_net_pay_block(result, col_widths):
    emp = result.employee
    detail_rows = [
        ("Employee Name", emp.name),
        ("Designation", emp.designation),
        ("Employee ID", emp.employee_id),
        ("Employee Type", emp.employee_type),
        ("Date of Joining", emp.date_of_joining),
        ("Pay Days", f"{emp.pay_days:g} / {result.standard_days}"),
        ("UAN Number", emp.uan),
    ]
    n = len(detail_rows)

    data = [["Employee Pay Summary", "", "Employee Net Pay", ""]]
    for label, value in detail_rows:
        data.append([Paragraph(label, LABEL_STYLE), Paragraph(str(value), VALUE_STYLE), "", ""])
    data[1][2] = Paragraph(indian_currency(result.net), NET_PAY_STYLE)

    table = Table(data, colWidths=col_widths)
    style = [
        ("SPAN", (0, 0), (1, 0)),
        ("SPAN", (2, 0), (3, 0)),
        ("SPAN", (2, 1), (3, n)),
        ("BACKGROUND", (2, 0), (3, 0), HEADER_FILL),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (2, 0), (2, 0), "CENTER"),
        ("VALIGN", (2, 1), (3, n), "MIDDLE"),
        ("ALIGN", (2, 1), (3, n), "CENTER"),
        ("GRID", (0, 0), (-1, -1), GRID_WIDTH, GRID_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]
    table.setStyle(TableStyle(style))
    return table


def _earnings_deductions_block(result, col_widths):
    emp = result.employee
    earnings = [("Basic", result.basic_earned), ("Special Allowance", result.sp_allowance_earned)]
    deductions = [
        ("PF Employee's Contribution", result.pf_employee),
        ("PF Employer's Contribution", result.pf_employer),
        ("ESIC Employee's Contribution", result.esic_employee),
        ("ESIC Employer's Contribution", result.esic_employer),
        ("P.Tax", emp.ptax),
    ]
    body_rows = max(len(earnings), len(deductions))
    total_deductions = result.pf_employee + result.esic_employee + emp.ptax

    data = [[
        Paragraph("EARNINGS", HEADER_CELL_STYLE), Paragraph("AMOUNT", HEADER_CELL_STYLE),
        Paragraph("DEDUCTIONS", HEADER_CELL_STYLE), Paragraph("AMOUNT", HEADER_CELL_STYLE),
    ]]
    for i in range(body_rows):
        row = ["", "", "", ""]
        if i < len(earnings):
            label, amount = earnings[i]
            row[0], row[1] = Paragraph(label, VALUE_STYLE), _money(amount)
        if i < len(deductions):
            label, amount = deductions[i]
            row[2], row[3] = Paragraph(label, VALUE_STYLE), _money(amount)
        data.append(row)
    data.append([
        Paragraph("Gross Earnings", LABEL_STYLE), _money_bold(result.gross),
        Paragraph("Total Deductions", LABEL_STYLE), _money_bold(total_deductions),
    ])

    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
        ("GRID", (0, 0), (-1, -1), GRID_WIDTH, GRID_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _net_pay_ctc_block(result, col_widths):
    emp = result.employee
    total_deduction_employee = result.pf_employee + result.esic_employee + emp.ptax
    net_pay_items = [("Gross Earnings", result.gross), ("Total Deduction (Employee)", total_deduction_employee)]
    ctc_items = [
        ("Gross Earnings", result.gross),
        ("PF Employer's Contribution", result.pf_employer),
        ("ESIC Employer's Contribution", result.esic_employer),
    ]
    body_rows = max(len(net_pay_items), len(ctc_items))

    data = [[
        Paragraph("NET PAY", LABEL_STYLE), "",
        Paragraph("CTC", LABEL_STYLE), "",
    ]]
    for i in range(body_rows):
        row = ["", "", "", ""]
        if i < len(net_pay_items):
            label, amount = net_pay_items[i]
            row[0], row[1] = Paragraph(label, VALUE_STYLE), _money(amount)
        if i < len(ctc_items):
            label, amount = ctc_items[i]
            row[2], row[3] = Paragraph(label, VALUE_STYLE), _money(amount)
        data.append(row)
    data.append([
        Paragraph("Total Net Payable", LABEL_STYLE), _money_bold(result.net),
        Paragraph("Monthly CTC", LABEL_STYLE), _money_bold(result.ctc),
    ])

    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("SPAN", (2, 0), (3, 0)),
        ("BACKGROUND", (0, 0), (1, 0), HEADER_FILL),
        ("BACKGROUND", (2, 0), (3, 0), HEADER_FILL),
        ("GRID", (0, 0), (-1, -1), GRID_WIDTH, GRID_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def _signature_block(col_widths):
    content_width = sum(col_widths)
    sig_width = col_widths[2] + col_widths[3]
    stamp = _image_at_height(STAMP_PATH, STAMP_HEIGHT_PT)
    table = Table(
        [
            ["", stamp if stamp is not None else ""],
            ["", Paragraph("Authorised Signatory", SIGNATORY_STYLE)],
        ],
        colWidths=[content_width - sig_width, sig_width],
    )
    table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("BOTTOMPADDING", (1, 0), (1, 0), 2),
        ("LINEABOVE", (1, 1), (1, 1), GRID_WIDTH, GRID_COLOR),
        ("TOPPADDING", (1, 1), (1, 1), 4),
    ]))
    return table


def _payslip_flowables(company, month_name, year, result, col_widths):
    flowables = _header_block(company, month_name, year, col_widths)
    flowables.append(_detail_and_net_pay_block(result, col_widths))
    flowables.append(Spacer(1, 10))
    flowables.append(_earnings_deductions_block(result, col_widths))
    flowables.append(Spacer(1, 10))
    flowables.append(_net_pay_ctc_block(result, col_widths))
    flowables.append(Spacer(1, 12))
    words_text = f"Total Net Payable {indian_currency(result.net)} ({amount_in_words(result.net)})"
    flowables.append(Paragraph(words_text, WORDS_STYLE))
    flowables.append(Spacer(1, 24))
    flowables.append(_signature_block(col_widths))
    return flowables


def build_employee_pdf(company: dict, fy_months_results: list, output_path):
    """fy_months_results: list of (month_name, year, PayslipResult) for one employee."""
    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                             leftMargin=40, rightMargin=40, topMargin=32, bottomMargin=32)
    content_width = A4[0] - 80
    col_widths = [content_width * r / 88 for r in (26, 16, 30, 16)]

    flowables = []
    for i, (month_name, year, result) in enumerate(fy_months_results):
        if i > 0:
            flowables.append(PageBreak())
        flowables.extend(_payslip_flowables(company, month_name, year, result, col_widths))
    doc.build(flowables)


REGISTER_STYLE = ParagraphStyle("register_cell", fontName="DejaVuSans", fontSize=6.5, leading=8)
REGISTER_HEADER_STYLE = ParagraphStyle("register_header", fontName="DejaVuSans-Bold", fontSize=6.5,
                                        alignment=1, leading=8)
REGISTER_TITLE_STYLE = ParagraphStyle("register_title", fontName="DejaVuSans-Bold", fontSize=13, alignment=1)


def _register_table(month_name, year, results):
    headers = [
        "Employee\nName", "Designation", "Employee\nID", "Employee\nType", "Date of\nJoining",
        "Pay\nDays", "Std\nDays", "UAN Number",
        "Basic", "Sp\nAllowance", "Gross",
        "PF\nEmployee", "PF\nEmployer", "ESIC\nEmployee", "ESIC\nEmployer", "P.Tax",
        "Net", "CTC",
    ]
    currency_fields = {"basic", "sp", "gross", "pfe", "pfr", "ese", "esr", "ptax", "net", "ctc"}
    data = [[Paragraph(h, REGISTER_HEADER_STYLE) for h in headers]]
    totals = {key: 0.0 for key in currency_fields}
    for result in results:
        emp = result.employee
        values = [
            emp.name, emp.designation, emp.employee_id, emp.employee_type, emp.date_of_joining,
            f"{emp.pay_days:g}", str(result.standard_days), emp.uan,
        ]
        money_values = [
            ("basic", result.basic_earned), ("sp", result.sp_allowance_earned), ("gross", result.gross),
            ("pfe", result.pf_employee), ("pfr", result.pf_employer),
            ("ese", result.esic_employee), ("esr", result.esic_employer),
            ("ptax", emp.ptax), ("net", result.net), ("ctc", result.ctc),
        ]
        row = [Paragraph(str(v), REGISTER_STYLE) for v in values]
        for key, amount in money_values:
            totals[key] += amount
            row.append(Paragraph(indian_currency(amount), REGISTER_STYLE))
        data.append(row)

    totals_row = [Paragraph("TOTAL", REGISTER_HEADER_STYLE)] + [""] * 7
    for key in ("basic", "sp", "gross", "pfe", "pfr", "ese", "esr", "ptax", "net", "ctc"):
        totals_row.append(Paragraph(indian_currency(totals[key]), REGISTER_HEADER_STYLE))
    data.append(totals_row)

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
        ("GRID", (0, 0), (-1, -1), GRID_WIDTH, GRID_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("LINEABOVE", (0, -1), (-1, -1), GRID_WIDTH * 1.5, GRID_COLOR),
    ]))
    return table


def build_register_pdf(fy_months_results: list, output_path):
    """fy_months_results: list of (month_name, year, list[PayslipResult]) for all employees."""
    page_size = landscape(A4)
    doc = SimpleDocTemplate(str(output_path), pagesize=page_size,
                             leftMargin=18, rightMargin=18, topMargin=20, bottomMargin=20)
    flowables = []
    for i, (month_name, year, results) in enumerate(fy_months_results):
        if i > 0:
            flowables.append(PageBreak())
        flowables.append(Paragraph(f"Salary Register - {month_name} {year}", REGISTER_TITLE_STYLE))
        flowables.append(Spacer(1, 8))
        flowables.append(_register_table(month_name, year, results))
    doc.build(flowables)

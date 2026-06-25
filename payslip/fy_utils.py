import datetime

MONTH_NAMES = [
    "April", "May", "June", "July", "August", "September",
    "October", "November", "December", "January", "February", "March",
]


def fy_label(fy_start_year: int) -> str:
    return f"FY{fy_start_year}-{fy_start_year + 1}"


def fy_start_year_for_month(month_name: str, year: int) -> int:
    """The financial year a given (month_name, calendar year) falls in.
    January-March belong to the FY that started the previous calendar year."""
    index = MONTH_NAMES.index(month_name)
    return year if index < 9 else year - 1


def normalize_month_name(value: str) -> str:
    """Match a month name/abbreviation case-insensitively to its canonical form."""
    value = value.strip().lower()
    for month in MONTH_NAMES:
        if value == month.lower() or value == month[:3].lower():
            return month
    raise ValueError(f"'{value}' is not a valid month name. Expected one of: {', '.join(MONTH_NAMES)}")


def current_month_year(today: datetime.date = None):
    today = today or datetime.date.today()
    return MONTH_NAMES[(today.month - 4) % 12], today.year

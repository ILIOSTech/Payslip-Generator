_ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
]
_TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def _two_digits_to_words(n: int) -> str:
    if n < 20:
        return _ONES[n]
    tens, ones = divmod(n, 10)
    return _TENS[tens] + (f" {_ONES[ones]}" if ones else "")


def _three_digits_to_words(n: int) -> str:
    hundreds, rest = divmod(n, 100)
    parts = []
    if hundreds:
        parts.append(f"{_ONES[hundreds]} Hundred")
    if rest:
        parts.append(_two_digits_to_words(rest))
    return " ".join(parts)


def number_to_words_indian(n: int) -> str:
    """Convert a non-negative integer to words using the Indian numbering
    system (crore / lakh / thousand)."""
    if n == 0:
        return "Zero"
    crore, n = divmod(n, 10_000_000)
    lakh, n = divmod(n, 100_000)
    thousand, n = divmod(n, 1000)
    remainder = n
    parts = []
    if crore:
        parts.append(f"{_three_digits_to_words(crore)} Crore")
    if lakh:
        parts.append(f"{_three_digits_to_words(lakh)} Lakh")
    if thousand:
        parts.append(f"{_three_digits_to_words(thousand)} Thousand")
    if remainder:
        if parts:
            parts.append("and")
        parts.append(_three_digits_to_words(remainder))
    return " ".join(parts)


def amount_in_words(amount: float) -> str:
    return f"{number_to_words_indian(round(amount))} Only"


def indian_currency(amount: float) -> str:
    """Format a number with Indian digit grouping (lakh/crore), e.g. 1234567.5 -> '₹12,34,567.50'."""
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    rupees, paise = divmod(round(amount * 100), 100)
    rupees_str = str(rupees)
    last_three = rupees_str[-3:]
    rest = rupees_str[:-3]
    groups = []
    while len(rest) > 2:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.insert(0, rest)
    grouped = ",".join(groups + [last_three]) if groups else last_three
    return f"{sign}₹{grouped}.{paise:02d}"


INDIAN_CURRENCY_FORMAT = '"₹"#,##,##0.00'

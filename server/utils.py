import re

EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def normalize_kenyan_phone(raw):
    """Return 2547XXXXXXXX / 2541XXXXXXXX, or None if it isn't a valid Kenyan number."""
    if not isinstance(raw, str):
        return None
    digits = re.sub(r"[\s\-()]", "", raw)
    if digits.startswith("+"):
        digits = digits[1:]
    if digits.startswith("0"):
        digits = "254" + digits[1:]
    elif len(digits) == 9 and digits[0] in "17":
        digits = "254" + digits
    return digits if re.fullmatch(r"254[17]\d{8}", digits) else None
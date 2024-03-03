import re


def check_password(password: str) -> bool:
    length = len(password)
    lowercase = re.search(r"[a-z]", password)
    uppercase = re.search(r"[A-Z]", password)
    number = re.search(r"\d+", password)

    if length >= 8 and lowercase and uppercase and number:
        return True
    return False

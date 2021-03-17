from decimal import Decimal


def filter_bold(obj):
    if (
        obj["object_type"] == "char"
        and obj["fontname"] == "YUQOTN+OpenSans-Semibold"
    ):
        return True
    elif obj["object_type"] == "char" and obj["fontname"] == "UZGVXX+OpenSans":
        return True
    return False


def header_text(obj):
    if obj["object_type"] == "char" and obj["size"] == 14:
        return True


def bold_lines(obj):
    if obj["object_type"] == "line" and obj["linewidth"] == Decimal("2"):
        return True


def regular_text(obj):
    if obj["object_type"] == "char" and obj["size"] == 14:
        return False
    return True


def add_lines(obj):
    if (
        obj["object_type"] == "char"
        and int(obj["size"]) == 14
        and obj["text"] == "."
    ):
        return True
    if (
        obj["object_type"] == "char"
        and int(obj["size"]) == 14
        and obj["text"] == "x"
    ):
        return True
    return False

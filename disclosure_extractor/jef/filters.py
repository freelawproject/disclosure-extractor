from decimal import Decimal


def title_text(obj):
    """
    Filter for bold text in Times-Bold font
    """
    if (
        obj.get("object_type", None) == "char"
        and obj.get("size", None) in [10, 12]
        and obj.get("fontname", None) == "Times-Bold"
    ):
        return True
    return False


def title_text_reverse(obj):
    """
    Filter for bold text in Times-Bold font
    """
    if (
        obj.get("object_type", None) == "char"
        and obj.get("size", None) == 12
        and obj.get("fontname", None) == "Times-Bold"
    ):
        return False
    return True


def filter_bold_times(obj):
    """
    Filter for bold text in Times-Bold font
    """
    if obj.get("fontname", None) == "Times-Bold" or obj.get("size", 0) < 8:
        return False
    return True


def title_text_V(obj):
    """
    Filter for bold text in Times-Bold font
    """
    if (
        obj.get("object_type", None) == "char"
        and obj.get("size", None) == 12
        and obj.get("fontname", None) == "Times-Bold"
        and obj.get("text", None) == "V"
    ):
        return True
    return False


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

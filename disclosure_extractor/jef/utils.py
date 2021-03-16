from decimal import Decimal
from typing import Dict, List

import pdfplumber

from disclosure_extractor.jef.filters import add_lines


def get_lines(page):
    filtered_page = page.filter(add_lines).extract_words()
    lines = page.lines
    keys = []
    for f in filtered_page:
        f["object_type"] = "line"
        f["stroking_color"] = (1, 2, 3)
        f["non_stroking_color"] = None
        f["x1"] = page.width
        f["x0"] = 0
        f["linewidth"] = Decimal("2")
        f["width"] = 600
        f["doctop"] = f["top"] + 700
        f["top"] = f["top"] + 20
        keys.append(f["top"])
        lines.append(f)
    return lines, keys


def set_section(t):
    dc = {
        "I. Positions": [
            "#",
            "ORGANIZATION NAME",
            "NOTE",
            "ORGANIZATION TYPE",
            "POSITION HELD",
        ],
        "II. Agreements": ["#", "EMPLOYER OR PARTY", "NOTE", "TERMS", "DATE"],
        "III A. Filer's Non-Investment Income": [
            "#",
            "SOURCE",
            "NOTE",
            "INCOME TYPE",
            "INCOME AMOUNT",
        ],
        "III B. Spouse's Non-Investment Income": [
            "#",
            "SOURCE",
            "NOTE",
            "DESCRIPTION",
        ],
        "IV. Reimbursements": [
            "#",
            "SOURCE",
            "NOTE",
            "DATES",
            "LOCATION",
            "PURPOSE",
            "ITEMS PAID OR PROVIDED",
        ],
        "V. Gifts": ["#", "SOURCE", "NOTE", "DESCRIPTION", "VALUE"],
        "VI. Liabilities": ["#", "CREDITOR", "NOTE", "TYPE", "VALUE"],
        "VII. Investments and Trusts": [
            "DESCRIPTION",
            "NOTE",
            "INCOME AMOUNT",
            "INCOME TYPE",
            "GROSS VALUE AS OF 12/31",
            "VALUE METHOD",
            "TRANS. TYPE",
            "TRANS. DATE",
            "TRANS. VALUE",
        ],
        "Additional Information or Explanation": ["PART", "#", "NOTE"],
    }
    section_titles = {
        "III A. Filer's Non-Investment Income": "Non-Investment Income",
        "III B. Spouse's Non-Investment Income": "Non Investment Income Spouse",
        "Additional Information or Explanation": ["PART", "#", "NOTE"],
    }
    if "III" in t:
        title = section_titles[t]
    elif "Additional" in t:
        title = "Additional Information or Explanations"
    else:
        title = t.split(". ")[1]

    return dc[t], title


def crop_and_extract(
    page: pdfplumber.pdf.Page,
    line: Dict,
    adjust=False,
    left_shift: int = 0,
    up_shift: int = 12,
    keys: List = [],
) -> str:
    """Extract text content for pdf line if any

    Given a line of a pdf - extracted the text around it.  If adjust
    is True, reduce the cropped area to within the first line (usually above)
    :param page: Page to crop
    :param line: Line to crop around
    :param adjust: Whether to check if another line is inside our crop
    :param left_shift: Leftward crop adjustment
    :param up_shift: Upward crop adjustment
    :return: Content of the section
    """
    bbox = (
        int(line["x0"]) - left_shift,
        max(int(line["top"]) - up_shift, 0),
        int(line["x1"]),
        int(line["top"]),
    )
    crop = page.crop(bbox)
    if adjust:
        tops = [row["top"] for row in crop.lines if row["top"] != line["top"]]
        if len(tops) > 0:
            nbb = (*bbox[:1], tops[-1], *bbox[2:])
            for i in keys:
                if nbb[1] < i < nbb[3]:
                    bbox = (*bbox[:1], int(i), *bbox[2:])

                    # return nbb
            # crop = page.filter(regular_text).crop(bbox=nbb)

            bbox = (*bbox[:1], int(tops[-1]), *bbox[2:])

    return bbox

import os
import re
from typing import Tuple

import pdfplumber

from disclosure_extractor.image_processing import load_template
from disclosure_extractor.jef.utils import (crop_and_extract, get_lines,
                                            set_section)

VALUATION_METHODS = (
    ("Q", "Appraisal"),
    ("R", "Cost (Real Estate Only)"),
    ("S", "Assessment"),
    ("T", "Cash Market"),
    ("U", "Book Value"),
    ("V", "Other"),
)

# INCOME GAIN CODES
INCOME_GAIN = (
    ("A", "1 - 1,000"),
    ("B", "1,001 - 2,500"),
    ("C", "2,501 - 5,000"),
    ("D", "5,001 - 15,000"),
    ("E", "15,001 - 50,000"),
    ("F", "50,001 - 100,000"),
    ("G", "100,001 - 1,000,000"),
    ("H1", "1,000,001 - 5,000,000"),
    ("H2", "5,000,001 +"),
)

GROSS_VALUE = (
    ("J", "1 - 15,000"),
    ("K", "15,001 - 50,000"),
    ("L", "50,001 - 100,000"),
    ("M", "100,001 - 250,000"),
    ("N", "250,001 - 500,000"),
    ("O", "500,001 - 1,000,000"),
    ("P1", "1,000,001 - 5,000,000"),
    ("P2", "5,000,001 - 25,000,000"),
    ("P3", "25,000,001 - 50,000,000"),
    ("P4", "50,000,001 - "),
)


def get_comment(content) -> str:
    """Check if comments are found on the first page, and return them

    :param page:
    :return:
    """
    if "COMMENT" in content:
        comment = content.split("COMMENT")[1]
        return comment.replace("\n", " ").strip()
    return ""


def get_metadata(cd, content) -> Tuple:
    """Check if comments are found on the first page, and return them

    :param page:
    :return:
    """

    cd["report_type"] = content.split(" ")[0]
    cd["year"] = re.findall(r"\d{4}", content)[0]
    cd["judge"] = re.findall(r"\/s\/(.*)\[", content)[0].strip()
    cd["annual"] = True if "Annual" in cd["report_type"] else False
    cd["date_of_report"] = re.findall(r"signed on(.*)by", content)[0].strip()
    return cd


def convert_gross_value(datum):
    if datum and datum != "None":
        if "less" in datum:
            return "J"
        min_val = datum.split(" ")[0]
        h = re.sub("[^\d,]", "", min_val)
        for k, v in GROSS_VALUE:
            if v.split(" ")[0] == h:
                return k
    return datum


def convert_valuation_method(datum):
    if datum and datum != "None":
        if "less" in datum:
            return "J"
        min_val = datum.split(" ")[0]
        h = re.sub("[^\d,]", "", min_val)
        for k, v in VALUATION_METHODS:
            if v.split(" ")[0] == h:
                return k
    return datum


def convert_income_gain(datum):
    if datum and datum != "None":
        if datum == "$1,000 or less":
            return "A"
        min_val = datum.split(" ")[0]
        h = re.sub("[^\d,]", "", min_val)
        for k, v in INCOME_GAIN:
            if v.split(" ")[0] == h:
                return k
    return datum


def add_data(cd, title, data, pg_number):
    if not cd["sections"][title]["rows"]:
        cd["sections"][title]["rows"] = []

    if title == "Positions":
        r = {
            "Name of Organization": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": f'{data["ORGANIZATION NAME"]} - {data["ORGANIZATION TYPE"]}',
            },
            "Position": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": data["POSITION HELD"],
            },
        }
    elif title == "Agreements":
        r = {
            "Date": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": f'{data["DATE"]}',
            },
            "Parties and Terms": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": f'{data["EMPLOYER OR PARTY"]} - {data["TERMS"]}',
            },
        }
    elif title == "Non-Investment Income":
        r = {
            "Date": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": "",
            },
            "Source and Type": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": f'{data["SOURCE"]} - {data["INCOME TYPE"]}',
            },
            "Income": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": f'{data["INCOME AMOUNT"]}',
            },
        }
    elif title == "Non Investment Income Spouse":
        r = {
            "Date": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": "",
            },
            "Source and Type": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": f'{data["SOURCE"]} - {data["DESCRIPTION"]}',
            },
        }
    elif title == "Reimbursements":
        r = {
            "Source": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": f'{data["SOURCE"]}',
            },
            "Dates": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": f'{data["DATES"]}',
            },
            "Locations": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": f'{data["LOCATION"]}',
            },
            "Purpose": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": f'{data["PURPOSE"]}',
            },
            "Items Paid or Provided": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": f'{data["ITEMS PAID OR PROVIDED"]}',
            },
        }
    elif title == "Gifts":
        r = {
            "Soruce": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": data["SOURCE"],
            },
            "Description": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": data["DESCRIPTION"],
            },
            "Value": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": data["VALUE"],
            },
        }
    elif title == "Liabilities":
        r = {
            "Creditor": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": data["CREDITOR"],
            },
            "Description": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": data["TYPE"],
            },
            "Value Code": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": data["VALUE"],
            },
        }
    elif title == "Investments and Trusts":
        r = {
            "A": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": data["DESCRIPTION"],
            },
            "B1": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": convert_income_gain(data["INCOME AMOUNT"]),
            },
            "B2": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": data["INCOME TYPE"],
            },
            "C1": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": convert_gross_value(data["GROSS VALUE AS OF 12/31"]),
            },
            "C2": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": convert_valuation_method(data["VALUE METHOD"]),
            },
            "D1": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": data["TRANS. TYPE"],
            },
            "D2": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": data["TRANS. DATE"],
            },
            "D3": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": convert_gross_value(data["TRANS. VALUE"]),
            },
            "D4": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": "",
            },
            "D5": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": "",
            },
        }
    else:
        return cd

    cd["sections"][title]["rows"].append(r)
    return cd


# files = glob.glob("assets/*.pdf")
# for file in files:


def extract_content(filepath):
    with pdfplumber.open(filepath) as pdf:
        print(filepath)
        page_one = pdf.pages[0].extract_text()
        cd = load_template()

        cd = get_metadata(cd, page_one)

        yet = False
        cd["general_comment"] = get_comment(page_one)
        cd["pdf_size"] = os.path.getsize(filepath)

        for page in pdf.pages:
            lines, keys = get_lines(page)
            row = []
            redacted = False

            for line in sorted(lines, key=lambda x: x["top"]):
                if line["width"] == 600:
                    # SET SECTION TITLE HERE
                    bbox = crop_and_extract(
                        page, line, up_shift=25, adjust=False, keys=keys
                    )
                    output = page.crop(bbox=bbox).extract_text()
                    options, title = set_section(output)

                    row = []
                else:
                    bbox = crop_and_extract(
                        page, line, up_shift=150, adjust=True, keys=keys
                    )
                    for key in keys:
                        if int(bbox[1]) < int(key) < int(bbox[3]):
                            bbox = (*bbox[:1], int(key), *bbox[2:])
                    output = page.crop(bbox=bbox).extract_text()
                    if not redacted:
                        redacted = (
                            True if page.crop(bbox=bbox).curves else False
                        )
                    if output:
                        output = output.replace("\n", " ").strip()
                    if not yet and output == "#":
                        yet = True
                    if not yet:
                        continue
                    row.append(output)
                    if row == ["None"]:
                        cd["sections"][title]["empty"] = True
                    elif len(row) == len(options):
                        if "#" in row or "DESCRIPTION" in row:
                            row = []
                            continue

                        data = dict(zip(options, row))
                        data["is_redacted"] = redacted
                        if title == "Additional Information or Explanations":
                            cd[
                                "general_comment"
                            ] = f'{cd["general_comment"]} PART {data["PART"]} #{data["#"]} {data["NOTE"]}'
                            continue
                        cd["sections"][title]["empty"] = False
                        cd = add_data(cd, title, data, page.page_number)
                        row = []
                        redacted = False
        cd["Additional Information or Explanations"] = cd["general_comment"]
        return cd

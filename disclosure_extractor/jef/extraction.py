import os
import re
from typing import Dict, Tuple

import pdfplumber

from disclosure_extractor.image_processing import load_template
from disclosure_extractor.jef.filters import (
    filter_bold_times,
    title_text,
    title_text_V,
    title_text_reverse,
)
from disclosure_extractor.jef.utils import (
    crop_and_extract,
    get_lines,
    set_section,
)

VALUATION_METHODS = (
    ("Q", "Appraisal"),
    ("R", "Cost (Real Estate Only)"),
    ("S", "Assessment"),
    ("T", "Cash Market"),
    ("U", "Book Value"),
    ("V", "Other"),
    ("W", "Estimated"),
)

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
    """Check if comments are found on the first page - this is a new comment

    This new general comment is appended to the additional comments section.

    :param content:
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
    """Convert gross values to code for gross values

    :param datum:
    :return:
    """
    if datum == None or datum == "None":
        return ""

    if datum:
        if "less" in datum:
            return "J"
        min_val = datum.split(" ")[0]
        h = re.sub(r"[^\d,]", "", min_val)
        for k, v in GROSS_VALUE:
            if v.split(" ")[0] == h:
                return k
    return datum


def convert_valuation_method(datum):
    """Convert values to code for Valuation method

    :param datum:
    :return:
    """
    if datum == None or datum == "None":
        return ""

    if datum:
        for k, v in VALUATION_METHODS:
            if v == datum:
                return k
    return datum


def convert_income_gain(datum):
    """Convert values to code for income gains

    :param datum:
    :return:
    """
    if datum == None or datum == "None":
        return ""

    if datum:
        if datum == "$1,000 or less":
            return "A"
        min_val = datum.split(" ")[0]
        h = re.sub(r"[^\d,]", "", min_val)
        for k, v in INCOME_GAIN:
            if v.split(" ")[0] == h:
                return k
    return datum


def add_data(results: Dict, title: str, data: Dict, pg_number: int) -> Dict:
    """Normalize and combine data into results

    :param results: All extracted content
    :param title: Section title
    :param data: Row data to append to results
    :param pg_number: page number
    :return: Results with appended data row
    """
    for k, v in data.items():
        if v == "None" or v == None:
            data[k] = ""

    if not results["sections"][title]["rows"]:
        results["sections"][title]["rows"] = []

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
            "Source": {
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
                "text": convert_gross_value(data["VALUE"]),
            },
        }
    elif title == "Investments and Trusts":
        r = {
            "A": {
                "is_redacted": data["is_redacted"],
                "page_number": pg_number,
                "text": data["DESCRIPTION"],
                "inferred_value": False,
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
        return results

    results["sections"][title]["rows"].append(r)
    return results


def extract_content(filepath: str) -> Dict:
    """Extract content from JEF financial disclosures.

    This functions works on a new type of document from the AO

    :param filepath: Path to the PDF
    :return: Extracted content
    :type: dict
    """
    with pdfplumber.open(filepath) as pdf:
        print(filepath)
        page_one = pdf.pages[0].extract_text()
        cd = load_template()

        cd = get_metadata(cd, page_one)

        yet = False
        addendum_redacted = False
        cd["general_comment"] = get_comment(page_one)
        cd["pdf_size"] = os.path.getsize(filepath)
        cd["page_count"] = len(pdf.pages)

        for page in pdf.pages:
            lines, keys = get_lines(page)
            row = []
            redacted = False

            for line in sorted(lines, key=lambda x: x["top"]):
                if line["width"] == 600:
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
                    if output == None:
                        output = ""
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
                            if not redacted and data["is_redacted"]:
                                addendum_redacted = True
                            continue
                        cd["sections"][title]["empty"] = False
                        cd = add_data(cd, title, data, page.page_number)
                        row = []
                        redacted = False
        cd["Additional Information or Explanations"] = {
            "text": cd["general_comment"],
            "is_redacted": addendum_redacted,
        }
        return cd


def get_text(page, cell, field):
    """"""
    redacted = False
    if not cell:
        return
    crop = page.crop(cell).filter(filter_bold_times)
    if not crop:
        return
    text = crop.extract_text()
    # Check if yellow - and so not content
    if any([x["fill"] for x in crop.rects]):
        return
    if not text:
        text = ""

    if field == "":
        return text
    if crop.curves and crop.curves[0]["fill"]:
        redacted = True

    cleaned_text = re.sub(r"\s+", " ", text).strip("")

    if field in ["A", "Source", "Creditor", "Date", "Position"]:
        cleaned_text = re.sub(r"^\d{1,4}\.", "", cleaned_text).strip()

    if field == "A":
        cleaned_text = re.sub(r"^[-]{1,4}", "", cleaned_text).strip()

    return {
        "text": cleaned_text,
        "page_number": page.page_number,
        "is_redacted": redacted,
    }


def extract_normal_pdf(filepath: str) -> Dict:
    """"""

    titles = [
        "Positions",
        "Agreements",
        "Non-Investment Income",
        "Non Investment Income Spouse",
        "Reimbursements",
        "Gifts",
        "Liabilities",
        "Investments and Trusts",
    ]
    empty_template = load_template()

    with pdfplumber.open(filepath) as pdf:
        pages = pdf.pages
        for page in pages:
            if not page.extract_text() or len(page.extract_text()) < 100:
                return {
                    "success": False,
                    "msg": f"OCR required on page #{page.page_number}",
                }

        for page in pages:
            for table in page.debug_tablefinder().tables:
                c = get_text(page, table.cells[0], "")
                if c.startswith("1."):
                    title = titles.pop(0)
                    empty_template["sections"][title]["rows"] = []
                if not re.match(r"\d+\.", c):
                    continue
                content = empty_template["sections"][title]["rows"]
                for row in table.rows:
                    cd = {}
                    fields = empty_template["sections"][title]["fields"]
                    if len(row.cells) > len(fields):
                        cells = row.cells[1:]
                    else:
                        cells = row.cells
                    for cell, field in zip(cells, fields):
                        cd[field] = get_text(page, cell, field)

                    if any([v["text"] for k, v in cd.items()]):
                        content.append(cd)
                empty_template["sections"][title]["rows"] = content
        if len(titles) > 0:
            # Unable to find all tables for this modified
            empty_template["success"] = False
            return empty_template

        addendum, redacted_addendum = "", False
        for page in pages:
            text = page.filter(title_text).extract_text()
            if not text:
                continue
            if "VIII. ADDITIONAL INFORMATION OR EXPLANATIONS." in text:
                top = page.filter(title_text_V).extract_words()[0]["bottom"]
                bbox = (0, top, page.width, page.height)
                crop = page.crop(bbox=bbox)

                if not redacted_addendum:
                    if crop.curves and crop.curves[0]["fill"]:
                        redacted_addendum = True

                text = crop.filter(title_text_reverse).extract_text()
                addendum = addendum + "\n " + text if text else ""

        empty_template["Additional Information or Explanations"][
            "text"
        ] = addendum
        empty_template["Additional Information or Explanations"][
            "is_redacted"
        ] = redacted_addendum

        empty_template["page_count"] = len(pdf.pages)
        empty_template["wealth"] = None
        empty_template["msg"] = ""
        empty_template["success"] = True

    count = 0
    investments = empty_template["sections"][title]["rows"]
    for investment_row in investments:
        investment_row["A"]["inferred_value"] = False
        if not count:
            count += 1
            continue
        investement_name = investment_row["A"]["text"]
        if (
            not investement_name
            and investments[count]["D1"]["text"]
            and investment_row["D1"]["text"]
        ):
            empty_template["sections"][title]["rows"][count]["A"][
                "inferred_value"
            ] = True
            empty_template["sections"][title]["rows"][count]["A"][
                "text"
            ] = investments[count - 1]["A"]["text"]
        count += 1

    return empty_template

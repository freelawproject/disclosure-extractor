import collections
import logging
import re
from itertools import groupby

import pytesseract

from disclosure_extractor.image_processing import find_redactions

investment_components = {
    1: {
        "roman_numeral": "I",
        "name": "Positions",
        "fields": ["Position", "Name of Organization/Entity"],
    },
    2: {
        "roman_numeral": "II",
        "name": "Agreements",
        "fields": ["Date", "Parties and Terms"],
    },
    3: {
        "roman_numeral": "IIIA",
        "name": "Non-Investment Income",
        "fields": ["Date", "Source and Type", "Income"],
    },
    4: {
        "roman_numeral": "IIIB",
        "name": "Spouse's Non-Investment Income",
        "fields": ["Date", "Source and Type"],
    },
    5: {
        "roman_numeral": "IV",
        "name": "Reimbursements",
        "fields": [
            "Sources",
            "Dates",
            "Location",
            "Purpose",
            "Items Paid or Provided",
        ],
    },
    6: {
        "roman_numeral": "V",
        "name": "Gifts",
        "fields": ["Source", "Description", "Value"],
    },
    7: {
        "roman_numeral": "VI",
        "name": "Liabilities",
        "fields": ["Creditor", "Description", "Value Code"],
    },
    8: {
        "roman_numeral": "VII",
        "name": "Investments and Trusts",
        "fields": [
            "A Description of Asset",
            "B Amount Code",
            "B Type",
            "C Value Code",
            "C Value Method",
            "C Type",
            "D Date",
            "D Value Code",
            "D Gain Code",
            "D Identity of Buyer/Seller",
        ],
    },
}
import json
from collections import OrderedDict
import os

scriptdir = os.path.basename(os.path.dirname(os.path.realpath(__file__)))

with open(os.path.join(scriptdir, "template.json")) as f:
    section_template = json.load(f, object_pairs_hook=OrderedDict)


def ocr_page(image):
    text = pytesseract.image_to_string(
        image, config="-c preserve_interword_spaces=1x1 --psm %s --oem 3" % 6
    )
    text = text.replace("\n", " ").strip().replace("|", "")
    return re.sub(" +", " ", text)


def ocr_date(image):
    """OCR date string from image slice

    """
    text = pytesseract.image_to_string(
        image,
        config="-c tessedit_char_whitelist=01234567890./: preserve_interword_spaces=1x1 --psm %s --oem 3"
        % 11,
    )
    text = text.replace("\n", " ").strip().replace("|", "")
    text = re.sub(" +", " ", text)
    return text


def ocr_variables(slice, column):
    """
    Values range from A to H

    :param file_path:
    :return:
    """
    if column == 2 or column == 9:
        possibilities = ["A", "B", "C", "D", "E", "F", "G", "H"]
    elif column == 5:
        possibilities = ["Q", "R", "S", "T", "U", "V", "W"]
    else:
        possibilities = [
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P1",
            "P2",
            "P3",
            "P4",
        ]

    for v in [6, 7, 10]:
        width, height = slice.size
        # Crop inside the cell for better results on the single code values
        crop = slice.crop((width * 0.3, 0, width * 0.7, height * 0.65))
        text = pytesseract.image_to_string(crop, config="--psm %s --oem 3" % v)
        clean_text = text.replace("\n", "").strip().upper().strip(".")
        if clean_text == "PL" or clean_text == "PI" or clean_text == "P|":
            return "P1"
        if len(clean_text) > 0:
            if clean_text in possibilities:
                if len(clean_text) > 0:
                    return clean_text
        # Do some hacking around what weve seen in results
        if column == 4 or column == 8:
            if clean_text == "I":
                return "J"
        if clean_text == "WW" and "W" in possibilities:
            return "W"
        if clean_text == "CC" and "C" in possibilities:
            return "C"
    # If we can't identify a known possibility return {} to indicate that
    # we think a value exists but we did not scrape it successfully.
    return "{}"


def ocr_slice(rx, count):
    """

    """

    rx.convert("RGBA")
    w, h = rx.size
    crop = rx.crop((w * 0.1, h * 0.1, w * 0.8, h * 0.8))
    data = crop.getdata()
    counts = collections.Counter(data)
    if (
        len(counts)
        < 50  # this number needs to fluctuate - or i need to find a way to create this in code,
        #     Current ideas is to grab a predictable slice of page that is white and sample it and use that number as a threshold
    ):  # this may need to fluctuate to be accurate at dropping empty sections to remove gibberish
        return ""
    if count == 1 or count == 6 or count == 10 or count == 3:
        text = ocr_page(rx)
    elif count == 7:
        text = ocr_date(rx)
    elif count == 4 or count == 8 or count == 2 or count == 9 or count == 5:
        text = ocr_variables(rx, count)
    return text


def generate_row_data(slice, row, column_index, row_index):
    """

    """
    cd = {}
    section_names = list(section_template["sections"].keys())
    section = section_names[row["section"] - 1]
    cd["section"] = section
    cd["field"] = section_template["sections"][section]["columns"][
        column_index
    ]
    cd["redactions"] = find_redactions(slice)
    cd["column_index"] = column_index
    cd["row_index"] = row_index
    return cd


def process_document(document_structure, pages):
    results = {}
    document_sections = section_template["sections"]
    section_names = list(document_sections.keys())

    checkboxes = [
        {x[5]: x[6]["is_section_empty"]}
        for x in document_structure["checkboxes"]
    ]
    category_list = list(document_sections.keys())
    for v in checkboxes:
        for i in v.keys():
            category = category_list[i - 1]
            document_sections[category]["empty"] = v[i]

    parts = ["all_other_sections", "investments_and_trusts"]
    for part in parts:
        if part == "all_other_sections":
            logging.info("Processing §§ I. to VI.")
        else:
            logging.info("Processing §VII.")
        groups = groupby(
            document_structure[part], lambda content: content["group"],
        )
        adjustment = 0 if part == "investments_and_trusts" else 60
        row_index = 0
        for grouping in groups:
            column_index = 0
            for row in sorted(grouping[1], key=lambda x: x["x"]):
                ocr_key = (
                    1 if part == "all_other_sections" else column_index + 1
                )
                slice = pages[row["page"]].crop(
                    (
                        row["x"],
                        row["y"] - adjustment,
                        (row["x"] + row["w"]),
                        (row["y"] + row["h"]),
                    )
                )
                section = investment_components[row["section"]]["name"]
                cd = generate_row_data(slice, row, column_index, row_index)
                cd["text"] = ocr_slice(slice, ocr_key)
                content = results[section]["content"]
                content.append(cd)
                results[section]["content"] = content
                column_index += 1
            row_index += 1

    width, height = pages[-2].size
    slice = pages[-2].crop((0, height * 0.15, width, height * 0.95,))
    results["Additional Information"] = {
        "section": "Additional Information",
        "title": "VIII",
        "redactions": find_redactions(slice),
        "text": ocr_slice(slice, 1),
    }

    i = 0
    four = ["reporting_period", "date_of_report", "court", "judge"]
    for one in document_structure["first_four"]:
        if i > 0:
            slice = pages[0].crop(
                (
                    one[0],
                    one[1] * 1.2,
                    one[0] + one[2],
                    one[1] * 1.2 + one[3] * 0.7,
                )
            )
        else:
            slice = pages[0].crop(
                (one[0], one[1], one[0] + one[2], one[1] + one[3])
            )
        results[four[i]] = ocr_slice(slice, 1).replace("\n", " ").strip()
        i += 1
    return results

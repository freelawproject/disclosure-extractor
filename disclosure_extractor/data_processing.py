# -*- coding: utf-8 -*-

import collections
import logging
import re

import pytesseract

from disclosure_extractor.image_processing import find_redactions


def ocr_page(image):
    text = pytesseract.image_to_string(
        image, config="-c preserve_interword_spaces=1x1 --psm %s --oem 3" % 6
    )
    text = text.replace("\n", " ").strip().replace("|", "")
    return re.sub(" +", " ", text)


def ocr_date(image):
    """OCR date string from image slice"""
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
        if column == 4 and width > 200:
            # This filters out liabilities cropping
            crop = slice
        else:
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
    """"""

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


def add_first_four(results, page):
    i = 0
    four = ["reporting_period", "date_of_report", "court", "judge"]
    for one in results["first_four"]:
        if i > 0:
            slice = page.crop(
                (
                    one[0],
                    one[1] * 1.2,
                    one[0] + one[2],
                    one[1] * 1.2 + one[3] * 0.7,
                )
            )
        else:
            slice = page.crop(
                (one[0], one[1], one[0] + one[2], one[1] + one[3])
            )
        results[four[i]] = ocr_slice(slice, 1).replace("\n", " ").strip()
        i += 1
    return results


def clean_stock_names(s):
    try:
        s = s.strip().replace("(J)", "").split(" ", 1)[1]
        for i, c in enumerate(s):
            if c.isalnum():
                return s[i:]
    except:
        return s


def process_document(results, pages, show_logs):
    count = 0
    for k, v in results["sections"].items():

        for _, row in v["rows"].items():
            for _, column in row.items():
                if column["section"] == "Investments and Trusts":
                    # if column["section"] == 8:
                    count += 1
    total = float(count)
    count = 0
    for k, v in results["sections"].items():
        logging.info("Processing § %s", k)
        if k == "Investments and Trusts":
            if show_logs:
                print("-" * 90, "//////////| <--- Finish-line")
        if results["sections"][k]["empty"] == True:
            logging.info("§ %s is empty", k)
            results["sections"][k]["rows"] = {}
            continue

        for x, row in v["rows"].items():
            ocr_key = 1
            for y, column in row.items():
                old_page = pages[column["page"]]
                page = old_page.resize((1653, 2180))

                crop = page.crop(column["coords"])
                if column["section"] == "Liabilities":
                    ocr_key += 1
                    if ocr_key == 4:
                        text = ocr_slice(crop, ocr_key).strip()
                    else:
                        text = ocr_slice(crop, 1).strip()
                elif column["section"] == "Investments and Trusts":
                    text = ocr_slice(crop, ocr_key).strip()
                    count += 1
                    if count > total / 100:
                        count = 0
                        if show_logs:
                            print("-", end="", flush=True)
                    ocr_key += 1
                else:
                    text = ocr_slice(crop, ocr_key).strip()
                results["sections"][k]["rows"][x][y] = {}
                if column["section"] == "Investments and Trusts":
                    results["sections"][k]["rows"][x][y][
                        "text"
                    ] = clean_stock_names(text)
                else:
                    results["sections"][k]["rows"][x][y]["text"] = text
                results["sections"][k]["rows"][x][y][
                    "is_redacted"
                ] = find_redactions(crop)

    # Process additional information
    old_page_minus_2 = pages[-2]
    page_minus_2 = old_page_minus_2.resize((1653, 2180))
    width, height = page_minus_2.size
    slice = pages[-2].crop(
        (
            0,
            height * 0.15,
            width,
            height * 0.95,
        )
    )
    results["Additional Information or Explanations"] = {
        "is_redacted": find_redactions(slice),
        "text": ocr_slice(slice, 1),
    }
    # Process page one information
    results = add_first_four(results, pages[0])

    del results["first_four"]
    return results

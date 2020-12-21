# -*- coding: utf-8 -*-

import collections
import re
import threading
from typing import Dict, List, Union

import pytesseract
from PIL import Image, ImageEnhance

from disclosure_extractor.image_processing import clean_image
from disclosure_extractor.image_processing import find_redactions

sema = threading.Semaphore(value=20)


def ocr_page(image: Image) -> str:
    """Ocr the image

    :param image: Image to process
    :return: Cleaned OCR'd text
    """
    text = pytesseract.image_to_string(
        image, config="-c preserve_interword_spaces=1x1 --psm %s --oem 3" % 6
    )
    text = text.replace("\n", " ").strip().replace("|", "")
    return re.sub(" +", " ", text)


def ocr_date(image: Image) -> str:
    """Special OCR processing date strings

    :param image: Image to OCR
    :return: date string if any
    """
    text = pytesseract.image_to_string(
        image,
        config="-c tessedit_char_whitelist=01234567890./: preserve_interword_spaces=1x1 --psm %s --oem 3"
        % 11,
    )
    text = text.replace("\n", " ").strip().replace("|", "")
    text = re.sub(" +", " ", text)
    return text


def ocr_variables(slice: Image, column: int) -> str:
    """OCR investment table sections Values range from A to H

    :param slice: Cropped table cell
    :param column: Column to OCR
    :return: return cell OCR value
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
        text = pytesseract.image_to_string(
            slice, config="--psm %s --oem 3" % v
        )
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
        if clean_text.upper() == "CC" and "C" in possibilities:
            return "C"
    # If we can't identify a known possibility return • to indicate that
    # we think a value exists but we did not scrape it successfully.
    # print("Failed", clean_text)

    enhancer = ImageEnhance.Sharpness(slice)
    enhanced_im = enhancer.enhance(2)
    emhanced_attempt = pytesseract.image_to_string(
        enhanced_im, config="--psm 6 --oem 3"
    )
    clean_text = emhanced_attempt.replace("\n", "").strip().upper().strip(".")
    if clean_text in possibilities:
        return clean_text
    return "•"


def check_if_blank(cell_image: Image) -> bool:
    """Check if image is blank

    Sample the color of the black and white content - if it is white enough
    assume no text and skip.  Function takes a small more centered section to
    OCR to avoid edge lines.
    :param cell_image: Image to OCR
    :return: True or None
    """
    w, h = cell_image.size
    crop = cell_image.crop((w * 0.1, h * 0.1, w * 0.8, h * 0.8))
    data = crop.getdata()
    counts = collections.Counter(data)
    if (
        len(counts)
        < 50  # this number needs to fluctuate - or i need to find a way to create this in code,
        #     Current ideas is to grab a predictable slice of page that is white and sample it and use that number as a threshold
    ):  # this may need to fluctuate to be accurate at dropping empty sections to remove gibberish
        return True
    return False


def ocr_slice(
    image_crop: Image, column_index: int, field=None, section=None
) -> str:
    """OCR cell based on column index

    Determine which function to use to OCR paticular column sections of
    the financial disclosure.

    :param image_crop: Image to OCR
    :param column_index: Column we are processing
    :return: text of cell.
    """
    if field == "Addendum":
        return pytesseract.image_to_string(
            image_crop,
            config="--psm 6 --oem 3 preserve_interword_spaces=1",
        )

    cleaned_image = clean_image(image_crop)
    if cleaned_image.size == 0:
        return ""

    cleaned_image_for_ocr = Image.fromarray(cleaned_image)
    if check_if_blank(cleaned_image_for_ocr):
        return ""
    if (
        column_index == 1
        or column_index == 6
        or column_index == 10
        or column_index == 3
    ):
        cell_text = ocr_page(cleaned_image_for_ocr)
    elif column_index == 7:
        cell_text = ocr_date(cleaned_image_for_ocr)
    else:
        cell_text = ocr_variables(cleaned_image_for_ocr, column_index)

    if field == "Date" or field == "D2":
        enhancer = ImageEnhance.Sharpness(image_crop)
        cleaned_sharpened = enhancer.enhance(2)
        cell_text = pytesseract.image_to_string(
            cleaned_sharpened,
            config="--psm 6 --oem 3 preserve_interword_spaces=1 -c "
            "tessedit_char_whitelist=01234567890./: ",
        ).strip()
        if "." in cell_text:
            cell_text = cell_text.split(".")[-1]
    return cell_text


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
        results[four[i]] = ocr_slice(slice, 1, None).replace("\n", " ").strip()
        i += 1
    return results


def clean_stock_names(s):
    try:
        s = s.strip().replace("(J)", "").split(" ", 1)[1]
        for i, c in enumerate(s):
            if c.isalnum():
                return s[i:].strip()
    except:
        return s.strip()


def process_addendum_normal(images, results):
    # Process additional information
    old_page_minus_2 = images[-2]
    # old_page_minus_2 = pages[-2]
    # page_minus_2 = old_page_minus_2.resize((1653, 2180))
    # else:
    page_minus_2 = old_page_minus_2
    width, height = page_minus_2.size
    slice = images[-2].crop(
        (
            0,
            height * 0.15,
            width,
            height * 0.95,
        )
    )
    results["Additional Information or Explanations"] = {
        "is_redacted": find_redactions(slice),
        "text": ocr_slice(slice, 1, "Addendum"),
    }
    return results


def process_row(row, page, results, k, row_count):
    """Process indivdual row data

    :param row:
    :param page:
    :param results:
    :param k:
    :param row_count:
    :return:
    """
    sema.acquire()
    ocr_key = 1
    pg_num = None
    for field, column in row.items():
        if not pg_num:
            page_number = int(column["page"]) + 1

        crop = page.crop(column["coords"])
        if column["section"] == "Liabilities":
            ocr_key += 1
            if ocr_key == 4:
                text = ocr_slice(
                    crop, ocr_key, field, column["section"]
                ).strip()
            else:
                text = ocr_slice(crop, 1, field, column["section"]).strip()
        elif column["section"] == "Investments and Trusts":
            text = ocr_slice(crop, ocr_key, field, column["section"]).strip()
            ocr_key += 1
        else:
            text = ocr_slice(crop, ocr_key, field, column["section"]).strip()

        data = {}
        if column["section"] == "Investments and Trusts":
            data["text"] = clean_stock_names(text)
        else:
            data["text"] = text

        data["is_redacted"] = find_redactions(crop)
        data["page_number"] = page_number

        results["sections"][k]["rows"][row_count][field] = data

    sema.release()
    return results


def process_document(
    results: Dict[str, Union[str, int, float, List, Dict]],
    pages: List,
    threaded: bool,
) -> Dict[str, Union[str, int, float, List, Dict]]:
    """Iterate over parsed document location data

    :param results: Collected data
    :param pages: page images
    :param resize: Whether to resize teh image
    :return: OCR'd data
    """
    for k, v in results["sections"].items():
        threads = []
        for row_count, row in v["rows"].items():

            try:
                page = pages[row[v["fields"][0]].get("page")]
                if threaded:
                    thread = threading.Thread(
                        target=process_row,
                        args=(row, page, results, k, row_count),
                    )
                    threads.append(thread)
                    thread.setDaemon(True)
                    thread.start()
                else:
                    results = process_row(row, page, results, k, row_count)
            except Exception as e:
                # Field doesnt exist for row
                pass

        for thread in threads:

            thread.join()

    # Process addendum
    results = process_addendum_normal(pages, results)

    # Process page one information
    try:
        results = add_first_four(results, Image.open(pages[0]))
        del results["first_four"]
    except:
        pass

    return results

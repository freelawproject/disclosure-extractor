import collections
import re

import pytesseract


def ocr_page(image):
    text = pytesseract.image_to_string(
        image, config="-c preserve_interword_spaces=1x1 --psm %s --oem 3" % 6
    )
    text = text.replace("\n", " ").strip().replace("|", "")
    return re.sub(" +", " ", text)


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
        if len(clean_text) == 2:
            return clean_text[0]
    return text.replace("\n", " ").strip()


def ocr_slice(rx, count):

    rx.convert("RGBA")
    data = rx.getdata()
    counts = collections.Counter(data)
    if (
        len(counts) < 100
    ):  # this may need to fluctuate to be accurate at dropping empty sections to remove gibberish
        return ""
    if count == 1 or count == 6 or count == 10 or count == 3:
        text = ocr_page(rx)
    elif count == 7:
        text = pytesseract.image_to_string(
            rx,
            config="-c tessedit_char_whitelist=01234567890./: preserve_interword_spaces=1x1 --psm %s --oem 3"
            % 11,
        )
        text = text.replace("\n", " ").strip().replace("|", "")
        text = re.sub(" +", " ", text)
    elif count == 4 or count == 8 or count == 2 or count == 9 or count == 5:
        text = ocr_variables(rx, count)
    return text


def process_document(document_structure, pages):
    results = {}
    g = None

    checkboxes = [
        {x[5]: x[6]["is_section_empty"]}
        for x in document_structure["checkboxes"]
    ]
    print(checkboxes)
    cd = {}
    for v in checkboxes:
        for i in v.keys():
            cd[i] = v[i]
    for row in sorted(
        document_structure["all_other_sections"],
        key=lambda x: (x["group"], x["x"]),
    ):
        if cd[row["section"]]:
            print("SKIPPING section", row["section"])
            continue

        if row["group"] != g:
            print(" ")
            g = row["group"]
        slice = pages[row["page"]].crop(
            (
                row["x"],
                row["y"] - 60,
                (row["x"] + row["w"]),
                (row["y"] + row["h"]),
            )
        )  # 60 is a fluctuating number i think
        text = ocr_slice(slice, 1)
        print(text, end="  |  ")
    column = 1

    for row in sorted(
        document_structure["investments_and_trusts"],
        key=lambda x: (x["group"], x["x"]),
    ):
        if row["group"] != g:
            print(" ")
            g = row["group"]
        slice = pages[row["page"]].crop(
            (row["x"], row["y"], (row["x"] + row["w"]), (row["y"] + row["h"]))
        )
        text = ocr_slice(slice, column)
        print(text, end="  |  ")

        column += 1
        if column == 11:
            column = 1

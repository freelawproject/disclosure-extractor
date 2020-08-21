import collections
import itertools
import logging
import re
from itertools import groupby
from operator import itemgetter
from statistics import mode

import cv2
import numpy as np
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes


def clahe(img, clip_limit=1.0, grid_size=(8, 8)):
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
    return clahe.apply(img)


def ocr_page(image):
    text = pytesseract.image_to_string(
        image, config="-c preserve_interword_spaces=1x1 --psm %s --oem 3" % 6
    )
    text = text.replace("\n", " ").strip().replace("|", "")
    return re.sub(" +", " ", text)


def ocr_column_two(img):
    """
    Values range from A to H

    :param file_path:
    :return:
    """
    words = []
    for v in [6, 7, 10]:
        text = pytesseract.image_to_string(img, config="--psm %s --oem 3" % v)
        clean_text = text.replace("\n", "").strip().upper()
        if len(clean_text) > 0:
            if clean_text in ["A", "B", "C", "D", "E", "F", "G", "H"]:
                return text.replace("\n", "").strip()
        words.append(text.replace("\n", "").strip())
    return text.replace("\n", "").strip()


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
            "PL",
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
        if clean_text == "PL":
            return "P1"
        if len(clean_text) > 0:
            if len(clean_text) == 2:
                clean_text = clean_text[0]
            if clean_text in possibilities:
                if len(clean_text) > 0:
                    return clean_text
    return text.replace("\n", "").strip()


def erode_table(crop_pil):
    open_cv_image = np.array(crop_pil)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    kernel = np.ones((5, 5), np.uint8)
    img = cv2.erode(open_cv_image, kernel, iterations=1)
    # cv2.imwrite("tmp/cropped_table_eroded.png", img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    im_pil = Image.fromarray(img)
    return im_pil

    # cv2.imwrite("tmp/cropped_table_eroded.png", img)


def crop_table(pdf_page_pil):

    open_cv_image = np.array(pdf_page_pil)
    open_cv_image = open_cv_image[:, :, ::-1].copy()

    hsv = cv2.cvtColor(open_cv_image.copy(), cv2.COLOR_BGR2HSV)
    lower_blue = np.array([0, 0, 0])
    upper_blue = np.array([255, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    result = cv2.bitwise_and(open_cv_image, open_cv_image, mask=mask)
    b, g, r = cv2.split(result)
    g = clahe(g, 5, (3, 3))

    # Adaptive Thresholding to isolate the bed
    img_blur = cv2.blur(g, (9, 9))
    img_th = cv2.adaptiveThreshold(
        img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 51, 2
    )

    contours, hierarchy = cv2.findContours(
        img_th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    rect = cv2.boundingRect(
        sorted(contours, key=cv2.contourArea, reverse=True)[1]
    )
    x, y, w, h = rect
    x = x - 10
    y = y - 10
    w = w + 20
    h = h + 20
    # pdf_page_pil.crop((x, y, (x + w), (y + h))).save("tmp/cropped_table.png")
    return pdf_page_pil.crop((x, y, (x + w), (y + h)))


def extract_cell_rects(pdf, page):
    pdf_page_pil = convert_from_bytes(pdf, dpi=300)[page]
    open_cv_image = np.array(pdf_page_pil)
    open_cv_image = open_cv_image[:, :, ::-1].copy()

    hsv = cv2.cvtColor(open_cv_image.copy(), cv2.COLOR_BGR2HSV)
    lower_blue = np.array([0, 0, 0])
    upper_blue = np.array([255, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    result = cv2.bitwise_and(open_cv_image, open_cv_image, mask=mask)
    b, g, r = cv2.split(result)
    g = clahe(g, 5, (3, 3))

    # Adaptive Thresholding to isolate the bed
    img_blur = cv2.blur(g, (9, 9))
    img_th = cv2.adaptiveThreshold(
        img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 51, 2
    )

    contours, hierarchy = cv2.findContours(
        img_th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    rect = cv2.boundingRect(
        sorted(contours, key=cv2.contourArea, reverse=True)[1]
    )
    x, y, w, h = rect
    x = x - 10
    y = y - 10
    w = w + 20
    h = h + 20
    pdf_pil_crop = pdf_page_pil
    # pdf_pil_crop = pdf_page_pil.crop((x, y, (x + w), (y + h)))
    open_cv_image = np.array(pdf_pil_crop)
    src = open_cv_image[:, :, ::-1].copy()

    # HSV thresholding to get rid of as much background as possible
    hsv = cv2.cvtColor(src.copy(), cv2.COLOR_BGR2HSV)
    lower_blue = np.array([0, 0, 0])
    upper_blue = np.array([255, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    result = cv2.bitwise_and(src, src, mask=mask)
    b, g, r = cv2.split(result)
    g = clahe(g, 1, (3, 3))

    # Adaptive Thresholding to isolate the bed
    img_blur = cv2.blur(g, (1, 1))
    img_th = cv2.adaptiveThreshold(
        img_blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        101,
        2,
    )

    contours, hierarchy = cv2.findContours(
        img_th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    locations = []
    for c in sorted(contours, key=cv2.contourArea, reverse=True):
        rect = cv2.boundingRect(c)
        x, y, w, h = rect
        if h < 50:
            continue
        if w < 50:
            continue
        locations.append(rect)

    m = mode([x[3] for x in locations])
    locations = [x for x in locations if m - 10 <= x[3] <= m + 10]
    return locations


def extract_cell_rects_from_cropped_table(pdf, page):
    pdf_page_pil = convert_from_bytes(pdf, dpi=300)[page]
    open_cv_image = np.array(pdf_page_pil)
    open_cv_image = open_cv_image[:, :, ::-1].copy()

    hsv = cv2.cvtColor(open_cv_image.copy(), cv2.COLOR_BGR2HSV)
    lower_blue = np.array([0, 0, 0])
    upper_blue = np.array([255, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    result = cv2.bitwise_and(open_cv_image, open_cv_image, mask=mask)
    b, g, r = cv2.split(result)
    g = clahe(g, 5, (3, 3))

    # Adaptive Thresholding to isolate the bed
    img_blur = cv2.blur(g, (9, 9))
    img_th = cv2.adaptiveThreshold(
        img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 51, 2
    )

    contours, hierarchy = cv2.findContours(
        img_th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    rect = cv2.boundingRect(
        sorted(contours, key=cv2.contourArea, reverse=True)[1]
    )
    x, y, w, h = rect
    x = x - 10
    y = y - 10
    w = w + 20
    h = h + 20
    # pdf_pil_crop = pdf_page_pil
    pdf_pil_crop = pdf_page_pil.crop((x, y, (x + w), (y + h)))
    open_cv_image = np.array(pdf_pil_crop)
    src = open_cv_image[:, :, ::-1].copy()

    # HSV thresholding to get rid of as much background as possible
    hsv = cv2.cvtColor(src.copy(), cv2.COLOR_BGR2HSV)
    lower_blue = np.array([0, 0, 0])
    upper_blue = np.array([255, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    result = cv2.bitwise_and(src, src, mask=mask)
    b, g, r = cv2.split(result)
    g = clahe(g, 1, (3, 3))

    # Adaptive Thresholding to isolate the bed
    img_blur = cv2.blur(g, (1, 1))
    img_th = cv2.adaptiveThreshold(
        img_blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        101,
        2,
    )

    contours, hierarchy = cv2.findContours(
        img_th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    locations = []
    for c in sorted(contours, key=cv2.contourArea, reverse=True):
        rect = cv2.boundingRect(c)
        x, y, w, h = rect
        if h < 50:
            continue
        if w < 50:
            continue
        locations.append(rect)

    m = mode([x[3] for x in locations])
    locations = [x for x in locations if m - 10 <= x[3] <= m + 10]
    return locations


def rectContains(rect, pt):
    return (
        rect[0] < pt[0] < rect[0] + rect[2]
        and rect[1] < pt[1] < rect[1] + rect[3]
    )


def extract_checkboxes(pdf_page_pil, page_count):

    open_cv_image = np.array(pdf_page_pil)
    open_cv_image = open_cv_image[:, :, ::-1].copy()

    hsv = cv2.cvtColor(open_cv_image.copy(), cv2.COLOR_BGR2HSV)
    lower_blue = np.array([0, 0, 0])
    upper_blue = np.array([255, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    result = cv2.bitwise_and(open_cv_image, open_cv_image, mask=mask)
    b, g, r = cv2.split(result)
    g = clahe(g, 5, (3, 3))

    # Adaptive Thresholding to isolate the bed
    img_blur = cv2.blur(g, (9, 9))
    img_th = cv2.adaptiveThreshold(
        img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 51, 2
    )

    contours, hierarchy = cv2.findContours(
        img_th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    rect = cv2.boundingRect(
        sorted(contours, key=cv2.contourArea, reverse=True)[1]
    )
    x, y, w, h = rect
    x = x - 10
    y = y - 10
    w = w + 20
    h = h + 20
    pdf_pil_crop = pdf_page_pil
    # pdf_pil_crop = pdf_page_pil.crop((x, y, (x + w), (y + h)))
    open_cv_image = np.array(pdf_pil_crop)
    src = open_cv_image[:, :, ::-1].copy()

    # HSV thresholding to get rid of as much background as possible
    hsv = cv2.cvtColor(src.copy(), cv2.COLOR_BGR2HSV)
    lower_blue = np.array([0, 0, 0])
    upper_blue = np.array([255, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    result = cv2.bitwise_and(src, src, mask=mask)
    b, g, r = cv2.split(result)
    g = clahe(g, 1, (3, 3))

    # Adaptive Thresholding to isolate the bed
    img_blur = cv2.blur(g, (1, 1))
    img_th = cv2.adaptiveThreshold(
        img_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 71, 2
    )

    contours, hierarchy = cv2.findContours(
        img_th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    locations = []
    for c in sorted(contours, key=cv2.contourArea, reverse=True):
        rect = cv2.boundingRect(c)
        x, y, w, h = rect
        if h < 40:
            continue
        if w < 40:
            continue
        if abs(w - h) > 10:
            continue
        if x > 100:
            continue
        x, y, w, h = rect
        locations.append((x, y, w, h, page_count))

    locations = sorted(locations, key=lambda x: (x[1]))
    i = 0
    while i < len(locations):
        x = locations[i]
        for item in locations:
            if rectContains(item, x):
                locations.pop(i)
        i += 1
    return locations


def ocr_slice(rx, count):

    rx.convert("RGBA")
    data = rx.getdata()
    counts = collections.Counter(data)
    if len(counts) < 50:
        if count == 6 or count == 7 or count == 3:
            answer = "|{:<15}".format("")
        elif (
            count == 4 or count == 8 or count == 2 or count == 9 or count == 5
        ):
            answer = "|{:<6}".format("")
        elif count == 1:
            answer = "|{:<60}".format("")
        elif count == 10:
            answer = "|{:<15}".format("")
        return answer
    if count == 1:
        text = ocr_page(rx)
        text = "|{:<60}".format(text)
    elif count == 6 or count == 10 or count == 7 or count == 3:
        text = ocr_page(rx)
        text = "|{:<15}".format(text)
    elif count == 4 or count == 8 or count == 2 or count == 9 or count == 5:
        text = ocr_variables(rx, count)
        text = "|{:<6}".format(text)
    return text


def get_column_ranges(img):
    img = img.convert("RGBA")
    width, height = img.size
    i = 0
    columns = []

    while i < height:
        left, right = 0, width
        top, bottom = height - (1 + i), height - i
        i += 1
        cropped_example = img.crop((left, top, right, bottom))
        data = cropped_example.getdata()
        counts = collections.Counter(data)
        if sum(counts.most_common(1)[0][0]) / 4 < 100:
            columns.append(bottom)

    ranges = []
    for k, g in groupby(enumerate(sorted(columns)), lambda x: x[0] - x[1]):
        group = list(map(itemgetter(1), g))
        ranges.append((group[0], group[-1]))
    return ranges


def get_row_ranges(img):
    img = img.convert("RGBA")
    rows = []
    i = 0
    width, height = img.size

    while i < width:
        left, right = 0 + i, 1 + i
        top, bottom = 0, height
        i += 1
        cropped_example = img.crop((left, top, right, bottom))
        cropped_example.convert("RGBA")
        data = cropped_example.getdata()
        counts = collections.Counter(data)
        if sum(counts.most_common(1)[0][0]) / 4 < 140:
            rows.append(left)

    ranges = []
    for k, g in groupby(enumerate(sorted(rows)), lambda x: x[0] - x[1]):
        group = list(map(itemgetter(1), g))
        ranges.append((group[0], group[-1]))
    return ranges


def erode(image):
    kernel = np.ones((5, 5), np.uint8)
    return cv2.erode(image, kernel, iterations=1)


def find_cells_manually(img):
    logging.info("Looking")

    columns = get_column_ranges(img)
    rows = get_row_ranges(img)

    if len(rows) != 11:
        logging.info("Failed to parse table, %s columns" % len(rows))
        return None

    r = []
    while len(rows) > 1:
        r.append((rows[0][1], rows[1][0]))
        rows.pop(0)

    c = []
    while len(columns) > 1:
        c.append((columns[0][1], columns[1][0]))
        columns.pop(0)

    rects = []
    for column in c:
        for row in r:
            x, y, w, h = (
                row[0],
                column[0],
                row[1] - row[0],
                column[1] - column[0],
            )
            rects.append((x, y, w, h))
    return rects


def extract_positions(pages):
    """
    positions are on Page #1 - of the PDFs along with agreements.  I have yet to see any that dont have it
    :return:
    """

    page_count = 0
    section_starts = []
    for page in pages:
        cd = extract_checkboxes(page, page_count)
        if cd:
            section_starts.append(cd)
        page_count += 1
    checkbox_locations = list(itertools.chain.from_iterable(section_starts))
    investment_pages = [x[-1] for x in checkbox_locations[7:]]
    return checkbox_locations[:7], investment_pages


def extract_from_page(pages, pg_num, section_info):
    cd = {}
    boundaries = []
    results = []

    open_cv_image = np.array(pages[pg_num])
    image = open_cv_image[:, :, ::-1].copy()

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edged = cv2.Canny(gray, 30, 200)
    contours, hierarchy = cv2.findContours(
        edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
    )

    while contours:
        c = contours.pop()
        rect = cv2.boundingRect(c)
        if rect[2] / rect[3] > 7:
            x, y, w, h = rect
            if w > 2000:
                continue
            if h > 5:
                continue
            if w < 200:
                continue
            boundaries.append((x, y, w, h, pg_num))

    for b in sorted(boundaries, key=lambda x: (x[1])):
        skip = False
        j = set(cd.keys())
        k = set(range(b[1] - 5, b[1] + 5))
        if j & k:
            x = cd[list(j.intersection(k))[0]]
            # before we append make sure its not a dupelicate
            for item in x:
                if item[0] - 5 <= b[0] <= item[0] + 5:
                    skip = True
                    continue
            if not skip:
                x.append(b)
                cd[list(j.intersection(k))[0]] = x
            continue
        cd[b[1]] = [b]

    row_order = 0
    for height, rows in cd.items():

        rows = sorted(rows, key=lambda x: (x[0]))
        i = 1
        while i < len(rows):
            if rows[i - 1][0] == rows[i][0]:
                rows.pop(i)
            i += 1

        for row in rows:
            row_index = rows.index(row)
            if len(rows) < 2:
                continue
            if rows[0][0] > 200:
                continue

            for section in section_info:
                if pg_num == section[4]:
                    if row[1] >= section[1]:
                        q = ["I", "II", "IIIA", "IIIB", "IV", "V", "VI"][
                            section_info.index(section)
                        ]
                if pg_num > section[4]:
                    q = ["I", "II", "IIIA", "IIIB", "IV", "V", "VI"][
                        section_info.index(section)
                    ]

            x, y, w, h, z = row
            results.append((x, y, w, h, z, q, row_index, row_order))
        row_order += 1
    return results


def organize_sections(results):
    cd = {}
    position_data = [x for x in results if x["section"] == "I"]
    positions = []
    agreement_data = [x for x in results if x["section"] == "II"]
    agreements = []
    income_data = [x for x in results if x["section"] == "IIIA"]
    incomes = []
    spouse_income_data = [x for x in results if x["section"] == "IIIB"]
    spouse_income = []
    reimbursement_data = [x for x in results if x["section"] == "IV"]
    reimbursements = []
    gift_data = [x for x in results if x["section"] == "V"]
    gifts = []
    liabilities_data = [x for x in results if x["section"] == "VI"]
    liabilities = []

    for item in zip(
        *[
            iter(
                sorted(
                    position_data,
                    key=lambda x: (x["page_num"], x["y"], x["row_index"]),
                )
            )
        ]
        * 2
    ):
        # print([x['text'] for x in item])
        a = ["position", "name_of_organization"]
        b = [x["text"] for x in item]
        row = dict(zip(a, b))
        positions.append(row)
        print(row)

    for item in zip(
        *[
            iter(
                sorted(
                    agreement_data,
                    key=lambda x: (x["page_num"], x["y"], x["row_index"]),
                )
            )
        ]
        * 2
    ):
        # print([x['text'] for x in item])
        a = ["date", "parties_and_terms"]
        b = [x["text"] for x in item]
        row = dict(zip(a, b))
        agreements.append(row)
        print(row)

    for item in zip(
        *[
            iter(
                sorted(
                    income_data,
                    key=lambda x: (x["page_num"], x["y"], x["row_index"]),
                )
            )
        ]
        * 3
    ):
        a = ["date", "source_type", "income"]
        b = [x["text"] for x in item]
        row = dict(zip(a, b))
        incomes.append(row)
        print(row)

    for item in zip(
        *[
            iter(
                sorted(
                    spouse_income_data,
                    key=lambda x: (x["page_num"], x["y"], x["row_index"]),
                )
            )
        ]
        * 2
    ):
        # print([x['text'] for x in item])
        a = ["date", "source_type"]
        b = [x["text"] for x in item]
        row = dict(zip(a, b))
        spouse_income.append(row)
        print(row)

    for item in zip(
        *[
            iter(
                sorted(
                    reimbursement_data,
                    key=lambda x: (x["page_num"], x["y"], x["row_index"]),
                )
            )
        ]
        * 5
    ):
        # print([x['text'] for x in item])
        a = ["source", "dates", "location", "purpose", "item_paid_or_provided"]
        b = [x["text"] for x in item]
        row = dict(zip(a, b))
        reimbursements.append(row)
        print(row)

    for item in zip(
        *[
            iter(
                sorted(
                    gift_data,
                    key=lambda x: (x["page_num"], x["y"], x["row_index"]),
                )
            )
        ]
        * 3
    ):
        # print([x['text'] for x in item])
        a = ["source", "description", "value"]
        b = [x["text"] for x in item]
        row = dict(zip(a, b))
        gifts.append(row)
        print(row)

    for item in zip(
        *[
            iter(
                sorted(
                    liabilities_data,
                    key=lambda x: (x["page_num"], x["y"], x["row_index"]),
                )
            )
        ]
        * 3
    ):
        # print([x['text'] for x in item])
        a = ["creditor", "description", "value_code"]
        b = [x["text"] for x in item]
        row = dict(zip(a, b))
        liabilities.append(row)
        print(row)

    cd["positions"] = positions
    cd["agreements"] = agreements
    cd["judge_income"] = incomes
    cd["spouse_income"] = spouse_income
    cd["reimbursements"] = reimbursements
    cd["gifts"] = gifts
    cd["liabilities"] = liabilities

    return cd

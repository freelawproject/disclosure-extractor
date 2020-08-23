import json

import cv2
import numpy as np
import pandas as pd


def clahe(img, clip_limit=1.0, grid_size=(8, 8)):
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
    return clahe.apply(img)


def determine_section_of_contour(checkboxes, rect):
    """ This does work with my hacky solution.
        this needs work - but afterwards we should be in good shape to finish this project
        wanna be bigger than checkbox so sort by y - normally- and as soon as we are larger than
    """
    search = [x for x in checkboxes if x[4] == rect[4]]
    for y in sorted(search, key=lambda x: (x[1]))[::-1]:
        if rect[1] > y[1]:
            if y[5] == 1:
                return 2
            if y[5] == 2:
                return 1
            if y[5] == 3:
                return 5
            if y[5] == 5:
                return 3
            if y[5] == 6:
                return 7
            if y[5] == 7:
                return 6
            return y[5]
    return max([x[5] for x in checkboxes])


def extract_contours_from_page(pages):
    """Process PDF

    Return the document structure as JSON data to easily and accurately
    extract out the information.
    """
    pg_num = 0
    checkboxes = []
    s1 = []
    s7 = []

    for page_image in pages:
        cv_image = np.array(page_image)
        src = cv_image[:, :, ::-1].copy()

        # HSV thresholding to get rid of as much background as possible
        hsv = cv2.cvtColor(src.copy(), cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(
            src=hsv,
            lowerb=np.array([0, 0, 0]),
            upperb=np.array([255, 255, 255]),
        )
        result = cv2.bitwise_and(src, src, mask=mask)
        _, g, _ = cv2.split(result)
        g = clahe(g, 1, (3, 3))

        # Adaptive Thresholding to isolate the bed
        image = cv2.adaptiveThreshold(
            src=cv2.blur(g, (1, 1)),
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY,
            blockSize=41,  # maybe variable...
            C=2,
        )
        mode = cv2.RETR_CCOMP
        method = cv2.CHAIN_APPROX_SIMPLE

        height, width = image.shape
        contours, hierarchy = cv2.findContours(image, mode, method)

        # Obtain the checkboxes on the page- to determine what section we are processing
        # do this first so we can remove any noise we might bump into on the top of the page

        i = 0
        checkboxes_on_page = []
        while i < len(contours):
            cntr = contours[i]
            area = cv2.contourArea(cntr)
            x, y, w, h = cv2.boundingRect(cntr)
            rect_area = w * h
            extent = float(area) / rect_area
            aspect_ratio = float(w) / h
            if 0.9 <= aspect_ratio <= 1.1 and extent > 0.8 and x < width * 0.2:
                if hierarchy[0, i, 3] == -1:
                    checkboxes_on_page.append((x, y, w, h, pg_num))
                    section = (
                        len(checkboxes) + 1 if len(checkboxes) + 1 < 9 else 8
                    )
                    checkboxes.append((x, y, w, h, pg_num, section))
                    # print(x,y, pg_num, "\t§", section)
            i += 1

        i = 0

        min_y = 0
        if checkboxes_on_page:
            min_y = min([x[1] for x in checkboxes_on_page])

        while i < len(contours):
            cntr = contours[i]
            area = cv2.contourArea(cntr)
            x, y, w, h = cv2.boundingRect(cntr)
            rect_area = w * h
            extent = float(area) / rect_area
            aspect_ratio = float(w) / h

            # Cells for Investments and Trusts  √√√√√
            upper = 180 if height > 3000 else 80
            if 10 > w / h > 0.9 and upper > h > 40 and len(checkboxes) > 7:
                # This lets me remove overlapping boxes,
                # and take the inner, cleaner version
                if hierarchy[0, i, 3] == -1:
                    cv2.drawContours(cv_image, contours, i, (70, 70, 255))
                    s7.append((x, y, w, h, pg_num, range(y, y + h), 8))

            # Highlight text input lines  √√√√√√
            if w / h > 7 and w > 150 and y > min_y:
                # if hierarchy[0, i, 3] == -1:
                rect = (x, y, w, h, pg_num, range(y, y + h))
                section = determine_section_of_contour(checkboxes, rect)
                rect = (x, y, w, h, pg_num, range(y, y + h), section)
                s1.append(rect)

            # Find small checkboxes on first page  ** this need to be completed
            if (
                0.9 <= aspect_ratio <= 1.1
                and extent > 0.8
                and x > width * 0.2
                and 50 > h > 30
            ):
                cv2.drawContours(cv_image, contours, i, (0, 0, 255))

            # Checkboxes  -- this needs to be completed
            if 0.9 <= aspect_ratio <= 1.1 and extent > 0.8 and x < width * 0.2:
                if hierarchy[0, i, 3] == -1:
                    cv2.drawContours(cv_image, contours, i, (0, 255, 0))
                    mean = np.array(
                        cv2.mean(cv_image[y : y + h, x : x + w])
                    ).astype(np.uint8)
                    # print(mean, (x, y), sum(mean) / 3)
                    checked = ""
                    if sum(mean) / 3 < 220:
                        checked = "X"  # X means the NONE selection was checked and that the section has no content
            i += 1

        pg_num += 1

    # Here is where we do some data processing and group rows together
    # sometimes things need to be massaged a bit.
    df = pd.DataFrame(
        {
            "x": [x[0] for x in s7],
            "y": [x[1] for x in s7],
            "w": [x[2] for x in s7],
            "h": [x[3] for x in s7],
            "top": [x[1] + 10 for x in s7],
            "page": [x[4] for x in s7],
            "section": [x[6] for x in s7],
        }
    )
    df2 = pd.DataFrame(
        {
            "x": [x[0] for x in s1],
            "y": [x[1] for x in s1],
            "w": [x[2] for x in s1],
            "h": [x[3] for x in s1],
            "top": [x[1] + 10 for x in s1],
            "page": [x[4] for x in s1],
            "section": [x[6] for x in s1],
        }
    )

    df = df.sort_values(["page", "y", "top"])
    df["group"] = (
        (
            df.top.rolling(window=2, min_periods=1).min()
            - df.y.rolling(window=2, min_periods=1).max()
        )
        < 0
    ).cumsum()
    ndf = df.groupby("group").filter(lambda x: len(x) == 10)

    df2 = df2.sort_values(["page", "y", "top"])
    df2["group"] = (
        (
            df2.top.rolling(window=2, min_periods=1).min()
            - df2.y.rolling(window=2, min_periods=1).max()
        )
        < 0
    ).cumsum()

    df2 = df2[df2.section != 8]
    ndf2 = df2.groupby("group").filter(lambda x: len(x) > 1)

    investments_and_trusts = json.loads(ndf.to_json(orient="table"))
    all_other_sections = json.loads(ndf2.to_json(orient="table"))

    # print (investments_and_trusts.keys())
    return {
        "investments_and_trusts": investments_and_trusts["data"],
        "all_other_sections": all_other_sections["data"],
    }

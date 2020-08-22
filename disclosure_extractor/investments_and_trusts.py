import logging

from pdf2image import convert_from_bytes

from disclosure_extractor.utils import (
    ocr_slice,
    crop_table,
    find_cells_manually,
    erode_table,
    extract_cell_rects,
)

table_columns = {
    "1": "description_of_asset",
    "2": "amount_code",
    "3": "income_type",
    "4": "gross_value",
    "5": "gross_value_code",
    "6": "transactions_type",
    "7": "transaction_date",
    "8": "transaction_value_code",
    "9": "transaction_gain_value_code",
    "10": "id_buyer_or_seller",
}


def extract_investments_from_page(pdf_bytes, page, jw):
    """

    :param pdf_bytes:
    :param page:
    :return:
    """
    logging.info("Processing § VII, page %s" % page)

    if jw:
        pdf_page_pil = convert_from_bytes(pdf_bytes, dpi=300)[page]
        pdf_pil_crop = crop_table(pdf_page_pil=pdf_page_pil)
        crop_cv = erode_table(pdf_pil_crop)
        locations = find_cells_manually(crop_cv)
    else:
        locations = extract_cell_rects(pdf_bytes, page)
        pdf_pil_crop = convert_from_bytes(pdf_bytes, dpi=300)[page]

    total = []
    for ten in zip(*[iter(sorted(locations, key=lambda x: (x[1])))] * 10):
        row = {}
        count = 0
        for rect in sorted(ten, key=lambda x: (x[0])):
            count += 1
            x, y, w, h = rect
            x = x + 5
            y = y
            w = w - 20
            h = h - 20
            slice = pdf_pil_crop.crop((x, y, (x + w), (y + h)))
            text = ocr_slice(slice, count)
            row[table_columns[str(count)]] = text.strip()[1:]
        total.append(row)
    return total

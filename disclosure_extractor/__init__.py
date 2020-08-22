from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import logging

import requests
from pdf2image import convert_from_bytes

from disclosure_extractor.analyze import estimate_net_worth
from disclosure_extractor.investments_and_trusts import (
    extract_investments_from_page,
)
from disclosure_extractor.utils import (
    extract_positions,
    ocr_slice,
    extract_from_page,
    organize_sections,
    _extract_section_data,
)


def process_financial_document(file=None, url=None, pdf_bytes=None, jw=False):
    """
    These two functions extract out all the information we need from these PDFs
    Pass in a url or filepath and convert the pdf to bytes - and then start processing it

    :return:
    """
    logging.info("Beginning Extraction of Financial Document")

    if not file and not url and not pdf_bytes:
        logging.warning(
            "\n\n--> No file, url or pdf_bytes submitted<--\n--> Exiting early\n"
        )
        return

    if file:
        logging.info("Opening PDF document from path")
        pdf_bytes = open(file, "rb").read()
    if url:
        logging.info("Downloading PDF from URL")
        pdf_bytes = requests.get(url, stream=True).content

    # Turn the PDF into an array of images
    images = convert_from_bytes(pdf_bytes)
    logging.info("Determining document structure")
    section_info, invst_pages = extract_positions(images)

    """Process Sections I-VI"""
    results = _extract_section_data(invst_pages[0], section_info, images)
    extracted_data = organize_sections(results)

    """ Process: VII. Investments and Trusts"""

    res = []
    for pg_num in invst_pages:
        value = extract_investments_from_page(pdf_bytes, pg_num, jw)
        res = res + value
    extracted_data["investments_and_trusts"] = res

    """ Process: VIII. Additional notes pages"""
    # Process: Additional notes pages

    net_worth_estimate = estimate_net_worth(extracted_data)
    logging.info("We estimate a net worth of %s to %s" % net_worth_estimate)
    # return JSON to CL
    return extracted_data

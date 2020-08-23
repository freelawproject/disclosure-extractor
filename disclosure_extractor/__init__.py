from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import logging

import requests
from pdf2image import convert_from_bytes

from disclosure_extractor.data_processing import process_document
from disclosure_extractor.image_processing import extract_contours_from_page


def process_financial_document(file=None, url=None, pdf_bytes=None):
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
    pages = convert_from_bytes(pdf_bytes)
    page_total = len(pages)
    logging.info("Determining document structure")
    logging.info("Document is %s pages long" % page_total)
    document_structure = extract_contours_from_page(pages)

    # this is unfinished - and currently doesnt return the text of the
    # content just prints it off semi-nicely.  Need to generate it into
    # a cl model structure and tweak the OCRing methods.  Need to perhaps sample a whitespace too.
    process_document(document_structure, pages)

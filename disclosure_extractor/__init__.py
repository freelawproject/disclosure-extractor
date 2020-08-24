from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import logging
from itertools import groupby

import requests
from pdf2image import convert_from_bytes

from disclosure_extractor.calculate import (
    estimate_investment_net_worth,
    income_gains,
)
from disclosure_extractor.data_processing import process_document
from disclosure_extractor.image_processing import extract_contours_from_page


def print_results(results):
    """Sometimes its nice to just print out the results

    """
    for k, v in results.items():
        if type(v) != dict:
            continue
        if "content" not in v.keys():
            continue
        groups = groupby(v["content"], lambda content: content["row_index"])
        print("\n", k, "\n====================")
        for g in groups:
            j = [x["text"] for x in list(g[1])]
            k = j.copy()
            k.pop(0)
            if k != "Investments and Trusts":
                if "".join(k).strip() != "":
                    print("  |  ".join(j))
            else:
                print("  |  ".join(j))


def process_financial_document(
    file_path=None, url=None, pdf_bytes=None, log_level=None
):
    """

    """
    if log_level:
        logging.getLogger().setLevel(logging.INFO)

    logging.info("Beginning Extraction of Financial Document")

    if not file_path and not url and not pdf_bytes:
        logging.warning(
            "\n\n--> No file, url or pdf_bytes submitted<--\n--> Exiting early\n"
        )
        return

    if file_path:
        logging.info("Opening PDF document from path")
        pdf_bytes = open(file_path, "rb").read()
    if url:
        logging.info("Downloading PDF from URL")
        pdf_bytes = requests.get(url, stream=True).content

    # Turn the PDF into an array of images
    pages = convert_from_bytes(pdf_bytes)
    page_total = len(pages)
    logging.info("Document is %s pages long" % page_total)

    logging.info("Determining document structure")
    document_structure = extract_contours_from_page(pages)

    logging.info("Extracting content from financial disclosure")
    results = process_document(document_structure, pages)
    results["page_count"] = page_total
    logging.info("Estimating net worth...")

    results["investment_range"] = estimate_investment_net_worth(results)
    results["income_gains"] = income_gains(results)
    logging.info(
        "Judicial investments appear to be roughly %s to %s with a gain between %s and %s or about %s percent.",
        results["investment_range"][0],
        results["investment_range"][1],
        results["income_gains"][0],
        results["income_gains"][1],
        "{:.2f}".format(
            100
            * (
                float(results["income_gains"][1])
                / results["investment_range"][1]
            )
        ),
    )
    return results

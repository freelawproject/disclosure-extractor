# -*- coding: utf-8 -*-

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import logging
from glob import glob
from tempfile import TemporaryDirectory
from typing import Dict

import requests
from pdf2image import convert_from_bytes, convert_from_path

from disclosure_extractor.calculate import estimate_investment_net_worth, color
from disclosure_extractor.data_processing import process_document
from disclosure_extractor.image_processing import (
    extract_contours_from_page,
    CheckboxesNotFound,
)
from disclosure_extractor.judicial_watch_utils import (
    get_investment_pages,
    extract_section_VII,
    extract_section_I_to_VI,
    identify_sections,
    get_text_fields,
    process_addendum,
)
from disclosure_extractor.post_processing import _fine_tune_results


def print_results(results):
    """Display the extraction in a nice table printout."""
    cd = {}
    for k, v in results["sections"].items():
        columns = results["sections"][k]["fields"]
        cd[k] = []
        max_lengths = [len(x) for x in columns]
        if v["rows"] != {}:
            x = cd[k]
            for row in v["rows"]:
                if len(row.items()) != len(columns):
                    continue
                r = []
                lengths = []
                if max_lengths == None:
                    max_lengths = [0] * len(row.items())
                for a, cell in row.items():
                    if cell["text"] is None:
                        r.append("")
                        lengths.append(0)
                        continue
                    if cell["is_redacted"] == True:
                        r.append(cell["text"] + " ⬛⬛⬛ ")
                        lengths.append(len(cell["text"] + " ⬛⬛⬛ ") + 1)
                    else:
                        r.append(cell["text"])
                        lengths.append(len(cell["text"]) + 1)
                max_lengths = [
                    x if x > y else y for x, y in zip(lengths, max_lengths)
                ]
                if len("".join(r).strip()) == 0:
                    continue
                x.append(r)

            headers = [x.ljust(y) for x, y in zip(columns, max_lengths)]
            print("\n")
            print(
                "|",
                "-" * len(" | ".join(headers)),
                "|",
            )
            print("\033[1m", end="")
            print("|", k.ljust(len(" | ".join(headers)) - 1), "\033[0m", "|")
            print(
                "|",
                "-" * len(" | ".join(headers)),
                "|",
            )
            print("\033[1m", end="")
            print("|", " | ".join(headers), "|", "\033[0m")
            print("|", "-" * len(" | ".join(headers)), "|")
            for item in cd[k]:
                clean_row = [x.ljust(y) for x, y in zip(item, max_lengths)]
                print("|", " | ".join(clean_row), "|")
            cd[k] = x
            print("|", "_" * len(" | ".join(headers)), "|")

    if "wealth" not in results.keys():
        return
    print("\n", "Wealth", "\n===============================")
    net_worth = results["wealth"]["investment_net_worth"]
    gains = results["wealth"]["income_gains"]
    debts = results["wealth"]["liabilities"]
    salaries = results["wealth"]["salary_income"]

    gross_low, gross_high = [
        color.RED + color.BOLD + str("${:,}".format(x)) + color.END
        if x > 1000000
        else str("${:,}".format(x))
        for x in net_worth
    ]
    gains_low, gains_high = [
        color.RED + color.BOLD + str("${:,}".format(x)) + color.END
        if x > 50000
        else str("${:,}".format(x))
        for x in gains
    ]
    if (net_worth[0] - gains[0]) > 0:
        percent = 100 * gains[0] / (net_worth[0] - gains[0])
        yoy_percent = (
            color.RED
            + color.BOLD
            + str("{:,.2f}%".format(percent))
            + color.END
            if percent > 5
            else str("{:,.2f}%".format(percent))
        )
    else:
        yoy_percent = 0
    debts_low, debts_high = [
        color.RED + color.BOLD + str("${:,}".format(x)) + color.END
        if x > 50000
        else str("${:,}".format(x))
        for x in debts
    ]

    print("Investments Total:".ljust(25), "%s to %s" % (gross_low, gross_high))
    print(
        "Investments gains YOY:".ljust(25),
        "%s to %s" % (gains_low, gains_high),
    )
    print("Percent gains YOY:".ljust(25), "%s" % (yoy_percent))
    print("Debts:".ljust(25), "%s to %s" % (debts_low, debts_high))
    print(
        "Other incomes totaling:".ljust(25),
        "%s" % ("${:,.2f}".format(salaries)),
    )
    print("\n")


def process_financial_document(
    file_path=None, url=None, pdf_bytes=None, show_logs=None, resize_pdf=True
):
    """Process Financial Documents

    :param file_path:
    :param url:
    :param pdf_bytes:
    :param show_logs:
    :param resize_pdf:
    :return:
    """
    if show_logs:
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

    try:
        document_structure, check_count = extract_contours_from_page(
            pages, resize=resize_pdf
        )
    except:
        return {"success": False, "msg": CheckboxesNotFound}

    if check_count < 8:
        logging.warning("Failed to extract document structure")
        return {
            "success": False,
            "msg": "Failed to process document properly",
            "checkbox_count_found": check_count,
        }

    logging.info("Extracting content from financial disclosure")
    results = process_document(
        document_structure, pages, show_logs, resize=resize_pdf
    )
    results["page_count"] = page_total
    results["pdf_size"] = len(pdf_bytes)
    results["wealth"] = estimate_investment_net_worth(results)
    results["success"] = True

    # Cleanup raw data & update document structure
    cleaned_data = _fine_tune_results(results)
    return cleaned_data


def process_judicial_watch(
    file_path=None, url=None, pdf_bytes=None, show_logs=None
):
    """This is the second and more brute force method for ugly PDFs.

    This method relies upon our own slicing and dicing of the image.
    """
    if show_logs:
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
    (
        non_investment_pages,
        investment_pages,
        addendum_page,
    ) = get_investment_pages(pdf_bytes)

    s1 = get_text_fields(non_investment_pages)
    document_data = identify_sections(s1)
    results = extract_section_I_to_VI(document_data, non_investment_pages)

    # Process Section VII
    results = extract_section_VII(results, investment_pages)

    # Process Section VIII - Addendum
    addendum_data = process_addendum(addendum_page)
    results["Additional Information or Explanations"] = addendum_data

    # Calculate net worth and mark processing as a success
    results["wealth"] = estimate_investment_net_worth(results)

    # Add final data
    results["page_count"] = page_total
    results["pdf_size"] = len(pdf_bytes)
    results["success"] = True

    # Cleanup raw data & update document structure
    cleaned_data = _fine_tune_results(results)

    return cleaned_data


def extract_financial_document(
    file_path: str = None,
    pdf_bytes: bytes = None,
    show_logs: bool = False,
    resize: bool = False,
) -> Dict:
    """Extract documents with lowered memory footprint


    :param file_path: Location of the PDF to extract
    :param show_logs: Should we show our logs
    :return: Our results of the extracted content
    """

    if show_logs:
        logging.getLogger().setLevel(logging.INFO)
    with TemporaryDirectory() as dir:
        if pdf_bytes:
            convert_from_bytes(
                pdf_bytes, thread_count=4, output_folder=dir, fmt="tiff"
            )
        else:
            convert_from_path(
                file_path, thread_count=4, output_folder=dir, fmt="tiff"
            )
        page_paths = sorted(glob(f"{dir}/*.tif"))
        logging.info("Document is %s pages long" % len(page_paths))
        logging.info("Determining document structure.")

        try:
            document_structure, check_count = extract_contours_from_page(
                page_paths, resize=resize
            )
        except:
            try:
                logging.info("Switch resizing again")
                resize = False if resize else True
                (
                    document_structure,
                    check_count,
                ) = extract_contours_from_page(page_paths, resize=resize)
            except:
                return {"success": False, "msg": CheckboxesNotFound}

        if check_count < 8:
            logging.warning("Failed to extract document structure")
            return {
                "success": False,
                "msg": "Failed to process document properly",
                "checkbox_count_found": check_count,
            }

        logging.info("Extracting content from financial disclosure")
        results = process_document(
            document_structure, page_paths, show_logs, resize=resize
        )
        results["page_count"] = len(page_paths)
    results["pdf_size"] = ""
    results["wealth"] = estimate_investment_net_worth(results)
    results["success"] = True
    results["msg"] = ""

    # Cleanup raw data & update document structure
    cleaned_data = _fine_tune_results(results)

    if show_logs:
        print_results(cleaned_data)

    return cleaned_data

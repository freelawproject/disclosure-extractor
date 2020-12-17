import re
from typing import Dict


def _fine_tune_results(results: dict) -> Dict:
    """Clean results by restructuring document

    :param results: Raw data extracted by OCR
    :return: Refined data
    """
    for k, v in results["sections"].items():
        del v["empty"]
        del v["order"]
        rows = []

        for k1, v1 in v["rows"].items():
            single_row = []
            for k2, v2 in v1.items():
                if v2["text"] is None:
                    v2["text"] = ""
                clean_text = re.sub(
                    r"^(\. )|^([\d]{1,3}(\.|,)? ?)", "", v2["text"]
                )
                single_row.append(clean_text)
            if len("".join(single_row)) > 3:
                rows.append(v1)
        v["rows"] = rows

    # Remove junk from - Unused numbers from the first item in a row
    # Excluding Investments and Trusts Section
    for k, sect in results["sections"].items():
        if k == "Investments and Trusts":
            continue
        for row in sect["rows"]:
            for _, field in row.items():
                field["text"] = re.sub(
                    r"^([0-9]{1,2}\.|,) |^(\. )", "", field["text"]
                )
                # Clean up (lL. Board Member -> Board Member)
                field["text"] = re.sub(
                    r"(^\S(?<!U)(\w)?\.? )",
                    "",
                    field["text"],
                    flags=re.IGNORECASE,
                )

                # Capitalize first words in sentences
                if len(field["text"]) > 1:
                    field["text"] = (
                        field["text"][0].upper() + field["text"][1:]
                    )

                # Dates - sometimes get addneded a numerical count  (12011 -> 2011; 2.2011 -> 2011)
                year_cleanup_regex = r"^(1(?P<year1>(20)(0|1)[0-9]))|([1-5]\.(?P<year2>(20)(0|1)[0-9]))"
                m = re.match(year_cleanup_regex, field["text"])
                if m:
                    if m.group("year1"):
                        field["text"] = m.group("year1")
                    elif m.group("year2"):
                        field["text"] = m.group("year2")
                break

    # Cleanup Investments and Trusts B2 field- appears to be dropdown with
    # free text options
    for row in results["sections"]["Investments and Trusts"]["rows"]:
        if "rest" in row["B2"]["text"]:
            row["B2"]["text"] = "Interest"
        if "Dist" in row["B2"]["text"]:
            row["B2"]["text"] = "Distribution"
        if "idend" in row["B2"]["text"]:
            row["B2"]["text"] = "Dividend"

    # Infer values for empty description fields in Investments and Trusts
    # Mark field as inferred value or not
    count = 0
    inv = results["sections"]["Investments and Trusts"]["rows"]
    for i in inv:
        inv[count]["A"]["inferred_value"] = False
        name = i["A"]["text"]
        if len(name) < 4:
            name = ""
        else:
            name = re.sub(r"^(\d|\W)(\S){1,3}\.? ?$", "", name)
        if name == "":
            if i["D1"]["text"] != "":
                inv[count]["A"]["text"] = inv[count - 1]["A"]["text"]
                inv[count]["A"]["inferred_value"] = True

        # Clean up D1 Field/Transaction Type
        # to select Buy Additional or Sold Part
        d1 = inv[count]["D1"]
        if "part)" == d1["text"] or "purt" in d1["text"]:
            d1["text"] = "Sold (part)"
        if "add'l)" == d1["text"] or "d'l)" in d1["text"]:
            d1["text"] = "Buy (add'l)"
        count += 1
    return results

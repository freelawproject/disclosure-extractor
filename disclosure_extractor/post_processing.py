import json
import re
from typing import Dict, Union, List
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from numpy import median


def _fine_tune_results(
    results: dict,
) -> Dict[str, Union[str, int, float, List, Dict]]:
    """Clean results by restructuring document

    :param results: Raw data extracted by OCR
    :return: Refined data
    """

    # Remove incomplete rows - and assume artifacts
    # Find rows outside of investments that have missing data and
    # remove them from the results
    remove_tuples = []
    for k, v in results["sections"].items():
        if k == "Investments and Trusts":
            for k1, v1 in v["rows"].items():
                if len(v["fields"]) != len(v1.keys()):
                    remove_tuples.append((k, k1))

    for r in remove_tuples:
        results["sections"][r[0]]["rows"].pop(r[1], None)

    # Reorganize results here
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
            # v1["row_count"] = int(k1) + 1
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

                # Dates - sometimes get addendum a numerical count
                # (12011 -> 2011; 2.2011 -> 2011)
                year_cleanup_regex = (
                    r"^(1(?P<year1>(20)(0|1)[0-9]))"
                    r"|([1-5]\.(?P<year2>(20)(0|1)[0-9]))"
                )
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
        if "ad" in d1["text"]:
            d1["text"] = "Buy (add'l)"

        d2 = inv[count]["D2"]["text"]
        if d2:
            if re.match(r"\d{4}\/(\d{2}|\d{4})", d2):
                d2 = f"{d2[:2]}/{d2[2:]}"
            elif re.match(r"(\d{2})\/\d{4}", d2):
                d2 = f"{d2[:5]}/{d2[5:]}"
            inv[count]["D2"]["text"] = d2

        b2 = inv[count]["B2"]["text"]
        if b2:
            if "lnt/" in b2:
                inv[count]["B2"]["text"] = "Int/Div"
            if (
                "D" == b2
                or "y" == b2
                or "v" == b2
                or "Int/" in b2
                or "Dy" in b2
                or "iv" in b2
                or "iy" in b2
                or "Dv" in b2
                or "vy" == b2
            ):
                inv[count]["B2"]["text"] = "Int/Div"

        count += 1

    # Clean up any incomplete rows or rows containing no english

    for title, sect in results["sections"].items():
        to_remove = set()
        fields = sect["fields"]
        if title != "Investments and Trusts":
            count = 0
            for row in sect["rows"]:
                languages = []

                if len(fields) == len(row.keys()):

                    row_text = [row[field]["text"] for field in fields]
                    lengths = [len(r) for r in row_text]
                    if 0 in lengths:
                        for x in row_text:
                            if x != "":
                                m = median([len(l) for l in x.split(" ")])
                                if m < 2:
                                    to_remove.add(count)

                    for field in fields:
                        if row[field]["is_redacted"]:
                            languages.append("en")
                            continue
                        try:
                            languages.append(detect(row[field]["text"]))
                        except LangDetectException:
                            languages.append("")

                    if "en" not in languages:
                        to_remove.add(count)
                else:
                    to_remove.add(count)
                count += 1
        for i in sorted(list(to_remove))[::-1]:
            results["sections"][title]["rows"].pop(i)

    return json.loads(json.dumps(results).replace("\\u2022", "-1"))

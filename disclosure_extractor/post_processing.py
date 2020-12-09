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
                single_row.append(v2["text"])
            if len("".join(single_row)) > 3:
                rows.append(v1)
        v["rows"] = rows

    # Cleanup Investments and Trusts
    for row in results["sections"]["Investments and Trusts"]["rows"]:
        if "rest" in row["B2"]["text"]:
            row["B2"]["text"] = "Interest"
        if "Dist" in row["B2"]["text"]:
            row["B2"]["text"] = "Distribution"
        if "idend" in row["B2"]["text"]:
            row["B2"]["text"] = "Dividend"

    count = 0
    inv = results["sections"]["Investments and Trusts"]["rows"]
    for i in inv:
        name = i["A"]["text"]
        name = re.sub(r"^[\S]{1,3}.?$", "", name)
        if name == "":
            if (
                i["B1"]["text"] == ""
                and i["B2"]["text"] == ""
                and i["D1"]["text"] != ""
            ):
                if ">" not in inv[count - 1]["A"]["text"]:
                    inv[count]["A"]["text"] = (
                        "> " + inv[count - 1]["A"]["text"]
                    )
                else:
                    inv[count]["A"]["text"] = inv[count - 1]["A"]["text"]
        count += 1

    return results

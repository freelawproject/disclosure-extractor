# -*- coding: utf-8 -*-
import re


class color:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def estimate_investment_net_worth(results):
    """Currently only using investment table to calculate net worth"""
    key_codes = {
        "A": [1, 1000],
        "B": [1001, 2500],
        "C": [2501, 5000],
        "D": [5001, 15000],
        "E": [15001, 50000],
        "F": [50001, 100000],
        "G": [100001, 1000000],
        "H1": [1000001, 5000000],
        "H2": [  # This is inaccurate as their is no upper bound
            5000001,
            1000000000,
        ],
        "J": [1, 15000],
        "K": [15001, 50000],
        "L": [50001, 100000],
        "M": [100001, 250000],
        "N": [250001, 500000],
        "O": [500001, 1000000],
        "P1": [1000001, 5000000],
        "P2": [5000001, 25000000],
        "P3": [25000001, 50000000],
        "P4": [  # This is inaccurate as their is no upper bound
            50000001,
            1000000000,
        ],
    }
    gross_values = []
    for k, v in results["sections"]["Investments and Trusts"]["rows"].items():
        if "C1" in v.keys():
            if v["C1"]["text"] != "" and v["C1"]["text"] != "•":
                gross_values.append(key_codes[v["C1"]["text"]])
            if v["D3"]["text"] != "" and v["D3"]["text"] != "•":
                gross_values.append(key_codes[v["D3"]["text"]])

    low = sum(x[0] for x in gross_values)
    high = sum(x[1] for x in gross_values)
    cd = {}
    cd["investment_net_worth"] = (low, high)

    net_change = []
    for k, v in results["sections"]["Investments and Trusts"]["rows"].items():
        if "C1" in v.keys():
            B1, D4 = v["B1"]["text"], v["D4"]["text"]
            for code in [B1, D4]:
                if code != "" and code != "•":
                    net_change.append(key_codes[code])

    low = sum(x[0] for x in net_change)
    high = sum(x[1] for x in net_change)
    cd["income_gains"] = (low, high)

    liabilities_total = []
    try:
        for k, v in results["sections"]["Liabilities"]["rows"].items():
            if (
                v["Value Code"]["text"] != ""
                and v["Value Code"]["text"] != "-1"
            ):
                liabilities_total.append(key_codes[v["Value Code"]["text"]])

        low = sum(x[0] for x in liabilities_total)
        high = sum(x[1] for x in liabilities_total)
        cd["liabilities"] = (low, high)
    except:
        cd["liabilities"] = (0, 0)
    try:
        salaries = []
        for k, v in results["sections"]["Non-Investment Income"][
            "rows"
        ].items():
            if v["Income"]["text"] != "" and v["Income"]["text"] != "-1":
                salary = v["Income"]["text"].replace(",", "").strip("$")
                if not re.match(r"^-?\d+(?:\.\d+)?$", salary) is None:
                    salaries.append(float(salary))

        cd["salary_income"] = sum(salaries)
    except:
        cd["salary_income"] = 0
    return cd

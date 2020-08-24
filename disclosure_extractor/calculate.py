# -*- coding: utf-8 -*-


def estimate_investment_net_worth(extracted_data):
    """Currenlty only using investment table to calculate net worth

    """
    money = {
        "J": [1, 15000],
        "K": [15001, 50000],
        "L": [50001, 100000],
        "M": [100001, 250000],
        "N": [250001, 500000],
        "O": [500001, 1000000],
        "P1": [1000001, 5000000],
        "P2": [5000001, 25000000],
        "P3": [25000001, 50000000],
        "P4": [
            50000001,
            1000000000,
        ],  # This is inaccurate as their is no upper bound
    }
    investments = extracted_data["Investments and Trusts"]["content"]
    gross_values = [
        money[x["text"]]
        for x in investments
        if "Value Code" in x["field"] and x["text"] in money.keys()
    ]
    low = sum(x[0] for x in gross_values)
    high = sum(x[1] for x in gross_values)
    return (low, high)


def income_gains(extracted_data):
    """Currenlty only using investment table to calculate net worth

    """
    money = {
        "A": [1, 1000],
        "B": [1001, 2500],
        "C": [2501, 5000],
        "D": [5001, 15000],
        "E": [15001, 50000],
        "F": [50001, 100000],
        "G": [100001, 1000000],
        "H1": [1000001, 5000000],
        "H2": [
            5000000,
            1000000000,
        ],  # This is inaccurate as their is no upper bound
    }
    investments = extracted_data["Investments and Trusts"]["content"]
    gain_1 = [
        money[x["text"]]
        for x in investments
        if "D Gain Code" == x["field"] and x["text"] in money.keys()
    ]
    gain_2 = [
        money[x["text"]]
        for x in investments
        if "B Amount Code" == x["field"] and x["text"] in money.keys()
    ]
    low = sum(x[0] for x in gain_1 + gain_2)
    high = sum(x[1] for x in gain_1 + gain_2)

    return (low, high)

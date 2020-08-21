

def estimate_net_worth(extracted_data):
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
    low = []
    high = []
    for investments in extracted_data["investments_and_trusts"]:
        if investments["gross_value"]:
            low.append(money[investments["gross_value"]][0])
            high.append(money[investments["gross_value"]][1])
        if investments["transaction_value_code"]:
            low.append(money[investments["transaction_value_code"]][0])
            high.append(money[investments["transaction_value_code"]][1])
    return (sum(low), "to", sum(high))

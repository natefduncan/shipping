from shipping.common import Rate
import datetime as dt


def get_valid_rates(rates: list[Rate], arrive_by: dt.date) -> list[Rate]:
    valid_rates = []
    for rate in rates:
        if not rate.arrival:
            continue
        elif rate.arrival.date() <= arrive_by:
            valid_rates.append(rate)
    return valid_rates


def get_best_rate(rates: list[Rate], arrive_by: dt.date) -> Rate:
    valid_rates = get_valid_rates(rates, arrive_by)
    if not valid_rates:
        raise ValueError("No valid rates for that configuration")
    else:
        return sorted(valid_rates, key=lambda x: x.price)[0]

import datetime as dt
import os
import pandas as pd
import requests as r

from shipping.common import Rate, RateRequest
from shipping.ups_ground import ups_ground_days


def get_token(client_id, client_secret):
    url = "https://wwwcie.ups.com/security/v1/oauth/token"
    payload = {"grant_type": "client_credentials"}
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = r.post(
        url, data=payload, headers=headers, auth=(client_id, client_secret)
    )
    data = response.json()
    return data


def get_rate(token: str, rate_request: RateRequest, map_dir: str, ignore_ground: bool) -> list[Rate]:
    version = "v2205"
    requestoption = "shoptimeintransit"
    url = f"https://wwwcie.ups.com/api/rating/{version}/{requestoption}"
    payload = {
        "RateRequest": {
            "Request": {"TransactionReference": {"CustomerContext": "CustomerContext"}},
            "Shipment": {
                "Shipper": {
                    "Address": {
                        "AddressLine": [rate_request.origination.street],
                        "City": rate_request.origination.city,
                        "StateProvinceCode": rate_request.origination.state,
                        "PostalCode": rate_request.origination.zip_code,
                        "CountryCode": rate_request.origination.country,
                    }
                },
                "ShipTo": {
                    "Name": "ShipToName",
                    "Address": {
                        "AddressLine": [rate_request.destination.street],
                        "City": rate_request.destination.city,
                        "StateProvinceCode": rate_request.destination.state,
                        "PostalCode": rate_request.destination.zip_code,
                        "CountryCode": rate_request.destination.country,
                    },
                },
                "NumOfPieces": "1",
                "DeliveryTimeInformation": {
                    "PackageBillType": "03",
                    "Pickup": {"Date": dt.datetime.today().strftime("%Y%M%d")},
                },
                "Package": {
                    # "SimpleRate": {
                    # "Description": "SimpleRateDescription",
                    # "Code": "XS"
                    # },
                    "PackagingType": {"Code": "00", "Description": "Packaging"},
                    "Dimensions": {
                        "UnitOfMeasurement": {"Code": "IN", "Description": "Inches"},
                        "Length": str(rate_request.dimensions.length),
                        "Width": str(rate_request.dimensions.width),
                        "Height": str(rate_request.dimensions.height),
                    },
                    "PackageWeight": {
                        "UnitOfMeasurement": {"Code": "LBS", "Description": "Pounds"},
                        "Weight": str(
                            round(
                                float(rate_request.weight.pounds)
                                + (rate_request.weight.ounces / 16),
                                2,
                            )
                        ),
                    },
                    "ShipmentTotalWeight": {
                        "UnitOfMeasurement": {
                            "Code": "LBS",
                            "Description": "Pounds",
                        },
                        "Weight": str(
                            round(
                                float(rate_request.weight.pounds)
                                + (rate_request.weight.ounces / 16),
                                2,
                            )
                        ),
                    },
                },
            },
        }
    }

    headers = {
        "Content-Type": "application/json",
        "transId": "string",
        "Authorization": f"Bearer {token}",
    }
    response = r.post(url, json=payload, headers=headers)
    return parse_rate_response(response, rate_request, map_dir, ignore_ground)


def parse_rate_response(
    response: r.Response, rate_request: RateRequest, map_dir, ignore_ground
) -> list[Rate]:
    if response.status_code == 200:
        output = []
        data = response.json()
        for rate in data["RateResponse"]["RatedShipment"]:
            service = rate["Service"]["Code"]
            price = rate["TotalCharges"]["MonetaryValue"]
            if "GuaranteedDelivery" in rate:
                transit_days = rate["GuaranteedDelivery"]["BusinessDaysInTransit"]
                arrival = dt.datetime.today() + dt.timedelta(days=int(transit_days))
            else:
                arrival = None
            if not ignore_ground:
                if int(service) == 3:  # UPS Ground
                    days = ups_ground_days(
                        rate_request.origination.zip_code, rate_request.destination.state, map_dir
                    )
                    arrival = dt.datetime.today() + dt.timedelta(days=int(days))
            output.append(Rate(price, service, arrival))
        return output
    else:
        raise ValueError(response.content)


def get_ups_zone_df(origin: str, user_agent: str):
    short_origin = origin[:3]
    headers = {
        "User-Agent": user_agent,
    }
    url = f"https://www.ups.com/media/us/currentrates/zone-csv/{short_origin}.xls"
    response = r.get(url, headers=headers)
    if response.status_code == 200:
        with open("temp.xls", "wb") as f:
            f.write(response.content)

    df = pd.read_excel(
        "temp.xls",
        sheet_name=str(short_origin),
        header=8,
    )
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df = df.loc[df["Dest. ZIP"].str.len() <= 3]
    os.remove("temp.xls")
    return df


def get_ups_zones(origin: str, destinations: list[str], user_agent):
    zone_df = get_ups_zone_df(origin, user_agent)
    output = []
    for zip_code in destinations:
        short_code = zip_code[:3]
        zone = zone_df.loc[zone_df["Dest. ZIP"] == short_code, "Ground"].iat[0]
        output.append(int(zone))
    return output

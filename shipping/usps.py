import datetime as dt
import requests as r
import xmltodict

from shipping.common import Rate, RateRequest

BASE_URL = "https://secure.shippingapis.com/ShippingAPI.dll?API=RateV4&XML="


def rate_request_to_xml(user_id: str, password: str, rate_request: RateRequest) -> str:
    formatted_date = rate_request.ship_date.strftime("%Y-%m-%d")
    return f"""
<RateV4Request USERID="{user_id}" PASSWORD="{password}">
    <Revision>2</Revision>
    <Package ID="1ST">
        <Service>ALL</Service>
        <ZipOrigination>{rate_request.origination.zip_code}</ZipOrigination>
        <ZipDestination>{rate_request.destination.zip_code}</ZipDestination>
        <Pounds>{rate_request.weight.pounds}</Pounds>
        <Ounces>{rate_request.weight.ounces}</Ounces>
        <Container>VARIABLE</Container>
        <Width>{rate_request.dimensions.width}</Width>
        <Length>{rate_request.dimensions.length}</Length>
        <Height>{rate_request.dimensions.height}</Height>
        <Machinable>False</Machinable>
        <DropOffTime></DropOffTime>
        <ShipDate>{formatted_date}</ShipDate>
        <SortationLevel></SortationLevel>
        <DestinationEntryFacilityType></DestinationEntryFacilityType>
        <ReturnFees>true</ReturnFees>
    </Package>
</RateV4Request>"""


def parse_rate_response(response: r.Response) -> list[Rate]:
    if response.status_code == 200:
        output = []
        data = xmltodict.parse(response.content)
        for temp_rate in data["RateV4Response"]["Package"]["Postage"]:
            if ";" in temp_rate["MailService"]:
                service = temp_rate["MailService"].split("&")[0]
                service_modifier = temp_rate["MailService"].split(";")[-1]
                service += service_modifier
            else:
                service = temp_rate["MailService"]
            rate = Rate(price=temp_rate["Rate"], service=service)
            if "CommitmentDate" in temp_rate:
                if temp_rate["CommitmentDate"]:
                    rate.arrival = dt.datetime.strptime(
                        temp_rate["CommitmentDate"], "%Y-%m-%d"
                    )
            output.append(rate)
        return output
    else:
        raise ValueError(response.content)


def get_rate(user_id: str, password: str, rate_request: RateRequest) -> list[Rate]:
    headers = {"Content-Type": "application/xml"}
    xml = rate_request_to_xml(user_id, password, rate_request)
    url = BASE_URL + xml
    response = r.get(url, headers=headers)
    return parse_rate_response(response)


def parse_usps_zone(response):
    if response.status_code == 200:
        data = response.json()
        numbers = [i for i in data["ZoneInformation"] if i.isdigit()]
        if not numbers:
            raise ValueError("Could not find zip code")
        return int(numbers[0])
    else:
        raise ValueError(f"Status code {response.status_code}")


def get_usps_zone(origination: str, destination: str, user_agent: str):
    today = dt.datetime.now().date()
    today_formatted = today.strftime("%m/%d/%Y")
    headers = {
        "User-Agent": user_agent,
        "X-Requested-With": "XMLHttpRequest",
    }
    url = f"https://postcalc.usps.com/DomesticZoneChart/GetZone?origin={origination}&destination={destination}&shippingDate={today_formatted}"
    response = r.get(url, headers=headers)
    return parse_usps_zone(response)


def get_usps_zones(origin: str, destinations: list[str], user_agent):
    output = []
    for zip_code in destinations:
        zone = get_usps_zone(origin, zip_code, user_agent)
        output.append(zone)
    return output

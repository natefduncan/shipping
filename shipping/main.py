import datetime as dt
import json
import os
import click
import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

from shipping.common import Dimensions, Location, Rate, RateRequest, Weight
from shipping.ups import (
    get_rate as get_ups_rates,
    create_ups_token,
    get_ups_token,
    get_ups_zones,
)
from shipping.usps import get_rate as get_usps_rates, get_usps_zones
from shipping.ups_ground import download_map

load_dotenv()

USPS_USER_ID = os.getenv("USPS_USER_ID")
USPS_PASSWORD = os.getenv("USPS_PASSWORD")
UPS_CLIENT_ID = os.getenv("UPS_CLIENT_ID")
UPS_CLIENT_SECRET = os.getenv("UPS_CLIENT_SECRET")
USER_AGENT = os.getenv("USER_AGENT")


def get_rate_request(
    from_zip, from_state, to_zip, to_state, ounces, size, date, country="US"
):
    return RateRequest(
        origination=Location(zip_code=from_zip, state=from_state, country=country),
        destination=Location(zip_code=to_zip, state=to_state, country=country),
        weight=Weight(0, ounces),
        dimensions=Dimensions.from_str(size),
        ship_date=date,
    )


def get_ups(
    from_zip,
    from_state,
    to_zip,
    to_state,
    ounces,
    size,
    date,
    new_token,
    map_dir,
    ignore_ground,
):
    rate_request = get_rate_request(
        from_zip, from_state, to_zip, to_state, ounces, size, date
    )
    if new_token:
        create_ups_token(UPS_CLIENT_ID, UPS_CLIENT_SECRET)
    token = get_ups_token()
    access_token = token["access_token"]
    return [
        i.to_dict()
        for i in get_ups_rates(access_token, rate_request, map_dir, ignore_ground)
    ]


def get_usps(from_zip, from_state, to_zip, to_state, ounces, size, date):
    rate_request = get_rate_request(
        from_zip, from_state, to_zip, to_state, ounces, size, date
    )
    return [
        i.to_dict() for i in get_usps_rates(USPS_USER_ID, USPS_PASSWORD, rate_request)
    ]


@click.group()
def cli():
    pass


@cli.command()
@click.option("-f", "--from-zip", type=str)
@click.option("-t", "--to-loc", type=str, help="state,zip_code")
@click.option("-z", "--ounces", type=int)
@click.option("-s", "--size", type=str)
@click.option(
    "-d", "--date", type=str, default=dt.datetime.today().strftime("%Y-%m-%d")
)
@click.option("--new-token", is_flag=True)
@click.option("--download-maps", is_flag=True)
@click.option("--map-dir", type=str, default=".")
@click.option("--ignore-ground", is_flag=True)
def ups(
    from_zip,
    to_loc,
    ounces,
    size,
    date,
    new_token,
    download_maps,
    map_dir,
    ignore_ground,
):
    to_state, to_zip = to_loc.split(",")
    date = dt.datetime.strptime(date, "%Y-%m-%d")
    if download_maps:
        download_ups_maps(from_zip, map_dir)
    rates = get_ups(
        from_zip,
        "",
        to_zip,
        to_state,
        ounces,
        size,
        date,
        new_token,
        map_dir,
        ignore_ground,
    )
    click.echo(json.dumps(rates))


@cli.command()
def ups_token():
    create_ups_token(UPS_CLIENT_ID, UPS_CLIENT_SECRET)
    click.echo(json.dumps(get_ups_token()))


@cli.command()
@click.option("-f", "--from-zip", type=str, default=None)
@click.option("-t", "--to-zip", type=str, default=None)
@click.option("-z", "--ounces", type=int)
@click.option("-s", "--size", type=str)
@click.option(
    "-d", "--date", type=str, default=dt.datetime.today().strftime("%Y-%m-%d")
)
def usps(from_zip, to_zip, ounces, size, date):
    date = dt.datetime.strptime(date, "%Y-%m-%d")
    rates = get_usps(from_zip, "", to_zip, "", ounces, size, date)
    click.echo(json.dumps(rates))


def download_ups_maps(zip_codes: list[str], map_dir: str):
    os.chdir(map_dir)
    maps = {"file_name": [], "zip_code": []}
    for zip_code in tqdm(zip_codes):
        file_name = download_map(zip_code, USER_AGENT)
        maps["file_name"].append(file_name)
        maps["zip_code"].append(str(zip_code))
    pd.DataFrame(maps).to_csv(f"maps.csv", index=False)


@cli.command()
@click.argument("from-zips", type=str)
@click.option("-d", "--map-dir", type=str, default=".")
def ups_maps(from_zips, map_dir):
    from_zips = from_zips.split(",")
    download_ups_maps(from_zips, map_dir)


def get_zones(from_zip, to_zips):
    ups_zones = get_ups_zones(from_zip, to_zips, USER_AGENT)
    usps_zones = get_usps_zones(from_zip, to_zips, USER_AGENT)
    return pd.DataFrame(
        {
            "from_zip": [from_zip] * len(to_zips),
            "to_zip": to_zips,
            "ups_zone": ups_zones,
            "usps_zone": usps_zones,
        }
    )


@cli.command()
@click.argument("from-zip", type=str)
@click.argument("to-zips", type=str)
def zones(from_zip, to_zips):
    to_zips = to_zips.split(",")
    zone_df = get_zones(from_zip, to_zips)
    click.echo(zone_df.to_csv(index=False))


if __name__ == "__main__":
    cli()

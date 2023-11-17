# Shipping

Utility CLI that gets shipping prices from UPS and USPS APIs.

## Installation

1. Copy `.env.template` to `.env` and fill in values.
2. `pip3 install .`
3. `shipping --help`

## Usage

```
Usage: shipping [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  ups
  ups-maps
  ups-token
  usps
  zones
```

## Examples

- Get UPS token: `shipping ups-token | jq`
- Get UPS Ground maps: `shipping ups-maps 60602 --map-dir=/tmp/maps`
- Get UPS prices with Ground arrival date: `shipping ups -f 60602 -t CA,90001 -z 60 -s 8x4x4 --map-dir=/tmp/maps | jq`
- Get UPS prices without Ground arrival date: `shipping ups -f 60602 -t CA,90001 -z 60 -s 8x4x4 --ignore-ground | jq`
- Get USPS prices: `shipping usps -f 60602 -t 90001 -z 60 -s 8x4x4 | jq` 
- Get UPS and USPS zones: `shipping zones 60602 90001,10001 > zones.csv`

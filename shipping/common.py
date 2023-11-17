import datetime as dt
from dataclasses import dataclass
from typing import Optional


@dataclass
class Location:
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: str = ""
    country: Optional[str] = None


@dataclass
class Weight:
    pounds: int
    ounces: int

    def __str__(self):
        pounds = round(self.pounds, 2)
        ounces = round(self.ounces, 2)
        return f"{pounds} lb {ounces} oz"

    def __repr__(self):
        return str(self)

    def to_ounces(self):
        return self.pounds * 16 + self.ounces


@dataclass
class Dimensions:
    length: int  # Always the longest
    width: int
    height: int

    def __str__(self):
        return f"{self.length}x{self.width}x{self.height}"

    def __repr__(self):
        return str(self)

    @classmethod
    def from_str(cls, str_dim):
        length, width, height = (int(i) for i in str_dim.split("x"))
        return cls(length, width, height)


@dataclass
class RateRequest:
    origination: Location
    destination: Location
    weight: Weight
    dimensions: Dimensions
    ship_date: dt.date


@dataclass
class Rate:
    price: float
    service: str
    arrival: Optional[dt.date] = None

    def to_dict(self):
        out = self.__dict__
        if out["arrival"]:
            out["arrival"] = out["arrival"].strftime("%Y-%m-%d")
        return out

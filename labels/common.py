from abc import ABC
from dataclasses import dataclass
from typing import List, Optional


STREET_TYPES = {'ln', 'st', 'ave', 'rd', 'avenue', 'dr', }


@dataclass
class Address(ABC):
    addresses: List[str]

    city: str
    zipcode: str

    def __post_init__(self):
        self.addresses = [a.strip() for a in self.addresses]
        self.city = self.city.strip()
        self.zipcode = self.zipcode.strip()

    def __str__(self) -> str:
        ...

    @classmethod
    def from_str(cls, address_str: str) -> 'Address':
        ...


@dataclass
class AddressUS(Address):
    state: str

    def __post_init__(self):
        super().__post_init__()
        self.state = self.state.strip()

    def __str__(self) -> str:
        address_str = '\n'.join(self.addresses)
        address_str += f'\n{self.city}, {self.state} {self.zipcode}'
        return address_str

    @classmethod
    def from_str(cls, address_str: str) -> 'AddressUS':
        address_split = address_str.split(',')

        if len(address_split) < 3:
            quick_str = '\n'.join(address_split)
            raise ValueError(f'Weird address length...\n{quick_str}')

        addresses = address_split[:-2]
        city = address_split[-2]
        locality = address_split[-1]

        locality_split = locality.strip().split(' ')
        state = locality_split[0]
        zipcode = locality_split[-1]

        return AddressUS(
            addresses=addresses,
            city=city.strip(),
            state=state.strip(),
            zipcode=zipcode
        )


@dataclass
class AddressInternational(Address):
    country: str

    def __post_init__(self):
        super().__post_init__()
        self.country = self.country.strip()

    def __str__(self) -> str:
        address_str = '\n'.join(self.addresses)
        address_str += f'\n{self.city}, {self.country} {self.zipcode}'
        return address_str

    @classmethod
    def from_str(cls, address_str: str) -> 'AddressInternational':
        address_split = address_str.split(',')

        if len(address_split) < 4:
            quick_str = '\n'.join(address_split)
            raise ValueError(f'Weird address length...\n{quick_str}')

        addresses = address_split[:-3]
        city = address_split[-3]
        zipcode = address_split[-2]
        country = address_split[-1]

        return AddressInternational(
            addresses=addresses,
            city=city,
            zipcode=zipcode,
            country=country
        )


def address_from_str(address_str: str) -> Address:
    try:
        int(address_str.split(' ')[-1].split('-')[0])
    except ValueError:
        return AddressInternational.from_str(address_str)
    else:
        return AddressUS.from_str(address_str)


@dataclass
class Person:
    name: str
    address: Address

    def __post_init__(self):
        self.name = self.name.strip()

    def __str__(self) -> str:
        return f'{self.name}\n{self.address}'

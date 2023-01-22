from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


STREET_TYPES = {'ln', 'st', 'ave', 'rd', 'avenue', 'dr', }


@dataclass
class Address(ABC):
    address1: str
    address2: Optional[str]

    city: str
    state: str
    zipcode: int

    def __str__(self) -> str:
        address_str = f'{self.address1}\n'
        if self.address2:
            address_str += f'{self.address2}\n'
        address_str += f'{self.city}, {self.state} {self.zipcode}'
        return address_str

    @classmethod
    def from_str(cls, address_str: str) -> 'Address':
        ...


@dataclass
class AddressInternational(Address):
    country: str

    def __str__(self) -> str:
        return super().__str__() + f' {self.country}'

    @classmethod
    def from_str(cls, address_str: str) -> 'AddressInternational':
        address1 = ''
        address2 = None
        city = ''
        state = ''
        zipcode = 0
        country = ''

        return AddressInternational(
            address1=address1,
            address2=None,
            city=city,
            state=state,
            zipcode=zipcode,
            country=country
        )


@dataclass
class AddressUS(Address):
    @classmethod
    def from_str(cls, address_str: str) -> '':
        address_split = address_str.split(',')

        address1 = address_split[0]
        city = address_split[-2]
        locality = address_split[-1]

        address2 = None
        if len(address_split) == 4:
            address2 = address_split[1]
        elif len(address_split) != 3:
            quick_str = '\n'.join(address_split)
            raise ValueError(f'Weird address length...\n{quick_str}')

        locality_split = locality.strip().split(' ')
        state = locality_split[0]
        zipcode = int(locality_split[-1])

        return AddressUS(
            address1=address1.strip(),
            address2=address2.strip() if address2 else None,
            city=city.strip(),
            state=state.strip(),
            zipcode=zipcode
        )


def address_from_str(address_str: str) -> Address:
    try:
        int(address_str.split(' ')[-1])
    except ValueError:
        return AddressInternational.from_str(address_str)
    else:
        return AddressUS.from_str(address_str)


@dataclass
class Person:
    name: str
    address: Address

    def __str__(self) -> str:
        return f'{self.name}\n{self.address}'

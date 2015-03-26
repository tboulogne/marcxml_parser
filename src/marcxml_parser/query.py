#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Interpreter version: python 2.7
#
# Imports =====================================================================
import remove_hairs
from remove_hairs import remove_hairs as remove_hairs_fn
from remove_hairs import remove_hairs_decorator

from . import record

from structures import Person
from structures import Corporation


# Variables ===================================================================
remove_hairs.HAIRS = r" :;<>(){}[]\/"


# Functions & classes =========================================================
def _undefinedPattern(value, fn, undefined):
    """
    If ``fn(value) == True``, return `undefined`, else `value`.
    """
    if fn(value):
        return undefined

    return value


class MARCXMLQuery(record.MARCXMLRecord):
    """
    Highlevel abstractions
    ++++++++++++++++++++++

    Getters:
        - :meth:`get_name`
        - :meth:`get_subname`
        - :meth:`get_price`
        - :meth:`get_part`
        - :meth:`get_part_name`
        - :meth:`get_publisher`
        - :meth:`get_pub_date`
        - :meth:`get_pub_order`
        - :meth:`get_pub_place`
        - :meth:`get_format`
        - :meth:`get_authors`
        - :meth:`get_corporations`
        - :meth:`get_distributors`
        - :meth:`get_ISBNs`
        - :meth:`get_binding`
        - :meth:`get_originals`
    """
    def __init__(self, xml=None, resort=True):
        super(MARCXMLQuery, self).__init__(xml, resort)

    def _parseCorporations(self, datafield, subfield, roles=["any"]):
        """
        Parse informations about corporations from given field identified
        by `datafield` parameter.

        Args:
            datafield (str): MARC field ID ("``110``", "``610``", etc..)
            subfield (str):  MARC subfield ID with name, which is typically
                             stored in "``a``" subfield.
            roles (str): specify which roles you need. Set to ``["any"]`` for
                         any role, ``["dst"]`` for distributors, etc.. For
                         details, see
                         http://www.loc.gov/marc/relators/relaterm.html

        Returns:
            list: :class:`Corporation` objects.
        """
        if len(datafield) != 3:
            raise ValueError(
                "datafield parameter have to be exactly 3 chars long!"
            )
        if len(subfield) != 1:
            raise ValueError(
                "Bad subfield specification - subield have to be 3 chars long!"
            )
        parsed_corporations = []
        for corporation in self.getDataRecords(datafield, subfield, False):
            other_subfields = corporation.getOtherSubfields()

            # check if corporation have at least one of the roles specified in
            # 'roles' parameter of function
            if "4" in other_subfields and roles != ["any"]:
                corp_roles = other_subfields["4"]  # list of role parameters

                relevant = any(map(lambda role: role in roles, corp_roles))

                # skip non-relevant corporations
                if not relevant:
                    continue

            name = ""
            place = ""
            date = ""

            name = corporation

            if "c" in other_subfields:
                place = ",".join(other_subfields["c"])
            if "d" in other_subfields:
                date = ",".join(other_subfields["d"])

            parsed_corporations.append(Corporation(name, place, date))

        return parsed_corporations

    def _parsePersons(self, datafield, subfield, roles=["aut"]):
        """
        Parse persons from given datafield.

        Args:
            datafield (str): code of datafield ("010", "730", etc..)
            subfield (char):  code of subfield ("a", "z", "4", etc..)
            role (list of str): set to ["any"] for any role, ["aut"] for
                 authors, etc.. For details see
                 http://www.loc.gov/marc/relators/relaterm.html

        Main records for persons are: "100", "600" and "700", subrecords "c".

        Returns:
            list: Person objects.
        """
        # parse authors
        parsed_persons = []
        raw_persons = self.getDataRecords(datafield, subfield, False)
        for person in raw_persons:

            # check if person have at least one of the roles specified in
            # 'roles' parameter of function
            other_subfields = person.getOtherSubfields()
            if "4" in other_subfields and roles != ["any"]:
                person_roles = other_subfields["4"]  # list of role parameters

                relevant = any(map(lambda role: role in roles, person_roles))

                # skip non-relevant persons
                if not relevant:
                    continue

            # result of .strip() is string, so ind1/2 in MarcSubrecord are lost
            ind1 = person.getI1()
            ind2 = person.getI2()
            person = person.strip()

            name = ""
            second_name = ""
            surname = ""
            title = ""

            # here it gets nasty - there is lot of options in ind1/ind2
            # parameters
            if ind1 == "1" and ind2 == " ":
                if "," in person:
                    surname, name = person.split(",", 1)
                elif " " in person:
                    surname, name = person.split(" ", 1)
                else:
                    surname = person

                if "c" in other_subfields:
                    title = ",".join(other_subfields["c"])
            elif ind1 == "0" and ind2 == " ":
                name = person.strip()

                if "b" in other_subfields:
                    second_name = ",".join(other_subfields["b"])

                if "c" in other_subfields:
                    surname = ",".join(other_subfields["c"])
            elif ind1 == "1" and ind2 == "0" or ind1 == "0" and ind2 == "0":
                name = person.strip()
                if "c" in other_subfields:
                    title = ",".join(other_subfields["c"])

            parsed_persons.append(
                Person(
                    name.strip(),
                    second_name.strip(),
                    surname.strip(),
                    title.strip()
                )
            )

        return parsed_persons

    @remove_hairs_decorator
    def get_name(self):
        """
        Returns:
            str: Name of the book.

        Raises:
            KeyError: when name is not specified.
        """
        return "".join(self.getDataRecords("245", "a", True))

    @remove_hairs_decorator
    def get_subname(self, undefined=""):
        """
        Args:
            undefined (optional): returned if sub-name record is not found.

        Returns:
            str: Sub-name of the book or `undefined` if name is not defined.
        """
        return _undefinedPattern(
            "".join(self.getDataRecords("245", "b", False)),
            lambda x: x.strip() == "",
            undefined
        )

    @remove_hairs_decorator
    def get_price(self, undefined=""):
        """
        Returns:
            str: Price of the book (with currency).
        """
        return _undefinedPattern(
            "".join(self.getDataRecords("020", "c", False)),
            lambda x: x.strip() == "",
            undefined
        )

    @remove_hairs_decorator
    def get_part(self, undefined=""):
        """
        Returns:
            str: Which part of the book series is this record.
        """
        return _undefinedPattern(
            "".join(self.getDataRecords("245", "p", False)),
            lambda x: x.strip() == "",
            undefined
        )

    @remove_hairs_decorator
    def get_part_name(self, undefined=""):
        """
        Returns:
            str: Name of the part of the series.
        """
        return _undefinedPattern(
            "".join(self.getDataRecords("245", "n", False)),
            lambda x: x.strip() == "",
            undefined
        )

    @remove_hairs_decorator
    def get_publisher(self, undefined=""):
        """
        Returns:
            str: name of the publisher ("``Grada``" for example)
        """
        return _undefinedPattern(
            "".join(self.getDataRecords("260", "b", False)),
            lambda x: x.strip() == "",
            undefined
        )

    @remove_hairs_decorator
    def get_pub_date(self, undefined=""):
        """
        Returns:
            str: date of publication (month and year usually)
        """
        return _undefinedPattern(
            "".join(self.getDataRecords("260", "c", False)),
            lambda x: x.strip() == "",
            undefined
        )

    @remove_hairs_decorator
    def get_pub_order(self, undefined=""):
        """
        Returns:
            str: information about order in which was the book published
        """
        return _undefinedPattern(
            "".join(self.getDataRecords("901", "f", False)),
            lambda x: x.strip() == "",
            undefined
        )

    @remove_hairs_decorator
    def get_pub_place(self, undefined=""):
        """
        Returns:
            str: name of city/country where the book was published
        """
        return _undefinedPattern(
            "".join(self.getDataRecords("260", "a", False)),
            lambda x: x.strip() == "",
            undefined
        )

    @remove_hairs_decorator
    def get_format(self, undefined=""):
        """_p  _p     Returns:
            str: dimensions of the book ('``23 cm``' for example)
        """
        return _undefinedPattern(
            "".join(self.getDataRecords("300", "c", False)),
            lambda x: x.strip() == "",
            undefined
        )

    def get_authors(self):
        """
        Returns:
            list: authors represented as Person objects
        """
        authors = self._parsePersons("100", "a")
        authors += self._parsePersons("600", "a")
        authors += self._parsePersons("700", "a")
        authors += self._parsePersons("800", "a")

        return authors

    def get_corporations(self, roles=["dst"]):
        """
        Args:
            roles (list, optional): specify which types of corporations you
                  need. Set to ``["any"]`` for any role, ``["dst"]`` for
                  distributors, etc..
                  See http://www.loc.gov/marc/relators/relaterm.html for
                  details.

        Returns:
            list: :class:`Corporation` objects specified by roles parameter.
        """
        corporations = self._parseCorporations("110", "a", roles)
        corporations += self._parseCorporations("610", "a", roles)
        corporations += self._parseCorporations("710", "a", roles)
        corporations += self._parseCorporations("810", "a", roles)

        return corporations

    def get_distributors(self):
        """
        Returns:
            list: distributors represented as :class:`Corporation` object
        """
        return self.get_corporations(roles=["dst"])

    def get_ISBNs(self):
        """
        Returns:
            list: array with ISBN strings
        """

        if self.getDataRecords("020", "a", False):
            return map(
                lambda ISBN: ISBN.strip().split(" ", 1)[0],
                self.getDataRecords("020", "a", True)
            )

        if self.getDataRecords("901", "i", False):
            return map(
                lambda ISBN: ISBN.strip().split(" ", 1)[0],
                self.getDataRecords("901", "i", True)
            )

        return []

    def get_binding(self):
        """
        Returns:
            list: array of strings with bindings (``["brož."]``) or blank list
        """
        if self.getDataRecords("020", "a", False):
            return map(
                lambda x: remove_hairs_fn(
                    x.strip().split(" ", 1)[1]
                ),
                filter(
                    lambda x: "-" in x and " " in x,
                    self.getDataRecords("020", "a", True)
                )
            )

        return []

    def get_originals(self):
        """
        Returns:
            list: of original names
        """
        return self.getDataRecords("765", "t", False)

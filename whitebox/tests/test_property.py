import pytest

from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup


def test_property_initialization_and_group_registration():
    group = PropertyGroup("Brown", "brown")
    prop = Property("Mediterranean Avenue", 1, 60, 2, group)

    assert prop.group is group
    assert prop in group.properties
    assert prop.mortgage_value == 30
    assert prop.is_available() is True


def test_get_rent_base_and_mortgaged_branch():
    prop = Property("Test", 1, 100, 12)
    assert prop.get_rent() == 12

    prop.is_mortgaged = True
    assert prop.get_rent() == 0


def test_property_group_all_owned_by_requires_every_property_owned():
    group = PropertyGroup("Brown", "brown")
    owner = Player("Alice")

    p1 = Property("A", 1, 60, 2, group)
    Property("B", 3, 60, 4, group)

    p1.owner = owner
    # second property intentionally unowned

    assert group.all_owned_by(owner) is False


def test_get_rent_full_group_multiplier_when_all_owned():
    group = PropertyGroup("Brown", "brown")
    owner = Player("Alice")

    p1 = Property("A", 1, 60, 2, group)
    p2 = Property("B", 3, 60, 4, group)
    p1.owner = owner
    p2.owner = owner

    assert p1.get_rent() == 4
    assert p2.get_rent() == 8


def test_mortgage_and_unmortgage_state_transitions():
    prop = Property("Test", 1, 101, 10)

    payout = prop.mortgage()
    assert payout == prop.mortgage_value
    assert prop.is_mortgaged is True

    # Already mortgaged
    assert prop.mortgage() == 0

    cost = prop.unmortgage()
    assert cost == int(prop.mortgage_value * 1.1)
    assert prop.is_mortgaged is False

    # Not mortgaged
    assert prop.unmortgage() == 0


def test_is_available_false_for_owned_or_mortgaged():
    prop = Property("Test", 1, 100, 10)
    assert prop.is_available() is True

    prop.owner = Player("Alice")
    assert prop.is_available() is False

    prop.owner = None
    prop.is_mortgaged = True
    assert prop.is_available() is False


def test_property_group_add_property_backlink_and_no_duplicates():
    group = PropertyGroup("Brown", "brown")
    prop = Property("Test", 1, 100, 10)

    group.add_property(prop)
    group.add_property(prop)

    assert prop.group is group
    assert group.properties.count(prop) == 1


def test_property_group_get_owner_counts_and_size():
    group = PropertyGroup("Brown", "brown")
    alice = Player("Alice")
    bob = Player("Bob")

    p1 = Property("A", 1, 100, 10, group)
    p2 = Property("B", 3, 120, 12, group)
    p3 = Property("C", 5, 140, 14, group)

    p1.owner = alice
    p2.owner = alice
    p3.owner = bob

    counts = group.get_owner_counts()
    assert counts[alice] == 2
    assert counts[bob] == 1
    assert group.size() == 3


def test_repr_variants():
    group = PropertyGroup("Brown", "brown")
    prop = Property("A", 1, 100, 10, group)

    assert "unowned" in repr(prop)
    prop.owner = Player("Alice")
    assert "Alice" in repr(prop)
    assert "PropertyGroup" in repr(group)

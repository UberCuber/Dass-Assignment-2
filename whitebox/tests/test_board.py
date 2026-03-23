from moneypoly.board import Board, SPECIAL_TILES
from moneypoly.player import Player


def test_board_initializes_all_groups_and_properties():
    board = Board()
    assert len(board.groups) == 8
    assert len(board.properties) == 22


def test_get_property_at_found_and_missing():
    board = Board()
    found = board.get_property_at(1)
    missing = board.get_property_at(0)

    assert found is not None
    assert found.name == "Mediterranean Avenue"
    assert missing is None


def test_get_tile_type_covers_special_property_and_blank():
    board = Board()
    assert board.get_tile_type(0) == "go"
    assert board.get_tile_type(2) == "community_chest"
    assert board.get_tile_type(7) == "chance"
    assert board.get_tile_type(1) == "property"
    assert board.get_tile_type(12) == "blank"


def test_is_purchasable_for_missing_owned_mortgaged_and_available():
    board = Board()
    player = Player("Alice")
    prop = board.get_property_at(1)

    assert board.is_purchasable(12) is False
    assert board.is_purchasable(1) is True

    prop.owner = player
    assert board.is_purchasable(1) is False

    prop.owner = None
    prop.is_mortgaged = True
    assert board.is_purchasable(1) is False


def test_is_special_tile_branch():
    board = Board()
    special_pos = next(iter(SPECIAL_TILES))
    assert board.is_special_tile(special_pos) is True
    assert board.is_special_tile(1) is False


def test_properties_owned_by_and_unowned_properties_lists():
    board = Board()
    alice = Player("Alice")
    bob = Player("Bob")

    p1 = board.get_property_at(1)
    p3 = board.get_property_at(3)
    p6 = board.get_property_at(6)
    p1.owner = alice
    p3.owner = alice
    p6.owner = bob

    alice_props = board.properties_owned_by(alice)
    bob_props = board.properties_owned_by(bob)
    unowned = board.unowned_properties()

    assert set(alice_props) == {p1, p3}
    assert set(bob_props) == {p6}
    assert p1 not in unowned
    assert p3 not in unowned
    assert p6 not in unowned
    assert len(unowned) == len(board.properties) - 3


def test_board_repr_shows_owned_count():
    board = Board()
    before = repr(board)
    board.get_property_at(1).owner = Player("Alice")
    after = repr(board)

    assert "22 properties" in before
    assert "0 owned" in before
    assert "1 owned" in after

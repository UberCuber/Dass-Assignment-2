import pytest

from moneypoly.cards import CardDeck


def test_draw_and_peek_return_none_for_empty_deck():
    deck = CardDeck([])
    assert deck.peek() is None
    assert deck.draw() is None


def test_draw_cycles_through_cards_in_order():
    cards = [
        {"description": "A", "action": "collect", "value": 10},
        {"description": "B", "action": "pay", "value": 5},
    ]
    deck = CardDeck(cards)

    assert deck.draw()["description"] == "A"
    assert deck.draw()["description"] == "B"
    assert deck.draw()["description"] == "A"


def test_peek_does_not_advance_index():
    cards = [{"description": "Only", "action": "collect", "value": 1}]
    deck = CardDeck(cards)

    first_peek = deck.peek()
    second_peek = deck.peek()
    drawn = deck.draw()

    assert first_peek == second_peek == drawn
    assert deck.index == 1


def test_reshuffle_resets_index_and_uses_random_shuffle(monkeypatch):
    cards = [
        {"description": "A", "action": "collect", "value": 10},
        {"description": "B", "action": "pay", "value": 5},
        {"description": "C", "action": "jail", "value": 0},
    ]
    deck = CardDeck(cards)
    deck.draw()
    deck.draw()
    assert deck.index == 2

    called = {"shuffled": False}

    def fake_shuffle(seq):
        called["shuffled"] = True
        seq.reverse()

    monkeypatch.setattr("moneypoly.cards.random.shuffle", fake_shuffle)
    deck.reshuffle()

    assert called["shuffled"] is True
    assert deck.index == 0
    assert [card["description"] for card in deck.cards] == ["C", "B", "A"]


def test_cards_remaining_when_not_wrapped():
    cards = [
        {"description": "A", "action": "collect", "value": 10},
        {"description": "B", "action": "pay", "value": 5},
        {"description": "C", "action": "jail", "value": 0},
    ]
    deck = CardDeck(cards)
    assert deck.cards_remaining() == 3
    deck.draw()
    assert deck.cards_remaining() == 2


def test_cards_remaining_empty_deck_should_be_zero():
    deck = CardDeck([])
    assert deck.cards_remaining() == 0


def test_repr_empty_deck_should_not_crash():
    deck = CardDeck([])
    text = repr(deck)
    assert "0 cards" in text


def test_len_and_repr_for_non_empty_deck():
    cards = [{"description": "A", "action": "collect", "value": 10}]
    deck = CardDeck(cards)

    assert len(deck) == 1
    assert "CardDeck(1 cards" in repr(deck)

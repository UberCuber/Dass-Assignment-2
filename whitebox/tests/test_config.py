from moneypoly import config


def test_config_expected_values():
    assert config.STARTING_BALANCE == 1500
    assert config.GO_SALARY == 200
    assert config.BOARD_SIZE == 40
    assert config.JAIL_POSITION == 10
    assert config.GO_TO_JAIL_POSITION == 30
    assert config.FREE_PARKING_POSITION == 20
    assert config.INCOME_TAX_POSITION == 4
    assert config.LUXURY_TAX_POSITION == 38
    assert config.INCOME_TAX_AMOUNT == 200
    assert config.LUXURY_TAX_AMOUNT == 75
    assert config.JAIL_FINE == 50
    assert config.MAX_TURNS == 100
    assert config.AUCTION_MIN_INCREMENT == 10
    assert config.BANK_STARTING_FUNDS == 20580


def test_config_basic_invariants():
    assert config.STARTING_BALANCE > 0
    assert config.GO_SALARY >= 0
    assert config.BOARD_SIZE > 0
    assert 0 <= config.JAIL_POSITION < config.BOARD_SIZE
    assert 0 <= config.GO_TO_JAIL_POSITION < config.BOARD_SIZE
    assert 0 <= config.FREE_PARKING_POSITION < config.BOARD_SIZE
    assert 0 <= config.INCOME_TAX_POSITION < config.BOARD_SIZE
    assert 0 <= config.LUXURY_TAX_POSITION < config.BOARD_SIZE
    assert config.MAX_TURNS > 0

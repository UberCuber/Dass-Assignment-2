from pathlib import Path
import sys

import pytest

# Ensure both package modules and top-level main.py are importable in tests.
WHITEBOX_ROOT = Path(__file__).resolve().parents[1]
CODE_ROOT_CANDIDATES = [
    WHITEBOX_ROOT / "code",
    WHITEBOX_ROOT / "moneypoly",
]
CODE_ROOT = next((p for p in CODE_ROOT_CANDIDATES if p.exists()), None)
if CODE_ROOT is None:
    raise RuntimeError(
        "Could not locate code root. Expected one of: "
        + ", ".join(str(p) for p in CODE_ROOT_CANDIDATES)
    )
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from moneypoly.game import Game


@pytest.fixture
def game_two_players():
    return Game(["Alice", "Bob"])

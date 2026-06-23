"""Regression tests for the glitches fixed in the Game Glitch Investigator.

Run from the repo root:

    python -m pytest tests/ -v

Each test below pins down a bug we fixed so it can never silently come back.
The pure-logic bug (G2) is tested by calling the function directly. The
Streamlit-flow bugs (G1, G3, G4) live in app.py and are exercised with
Streamlit's AppTest harness, which runs the whole app headlessly.
"""
import os

from streamlit.testing.v1 import AppTest

from logic_utils import check_guess, get_range_for_difficulty, parse_guess

# conftest.py at the repo root puts the root on sys.path, so the imports above
# resolve regardless of how pytest is launched.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app.py")


# ---------------------------------------------------------------------------
# Baseline behavior (corrected). check_guess returns an (outcome, message)
# tuple, not a bare string. The original starter tests asserted against a
# string and therefore always failed; here we unpack the tuple.
# ---------------------------------------------------------------------------
def test_winning_guess():
    outcome, _message = check_guess(50, 50)
    assert outcome == "Win"


def test_guess_too_high():
    outcome, _message = check_guess(60, 50)
    assert outcome == "Too High"


def test_guess_too_low():
    outcome, _message = check_guess(40, 50)
    assert outcome == "Too Low"


# ---------------------------------------------------------------------------
# G2 - the secret must be compared numerically, never as a string.
# The old code turned the secret into a string every other turn, so check_guess
# fell into a lexicographic comparison where, e.g., "9" > "50" is True and the
# guess 9 was wrongly reported as "Too High". These two cases are the ones that
# differ between numeric and string comparison, so they fail if the glitch
# ever returns.
# ---------------------------------------------------------------------------
def test_g2_single_digit_guess_below_two_digit_secret():
    # 9 < 50 numerically -> Too Low ("9" > "50" as text -> Too High).
    outcome, _ = check_guess(9, 50)
    assert outcome == "Too Low"


def test_g2_three_digit_guess_above_two_digit_secret():
    # 100 > 20 numerically -> Too High ("100" < "20" as text -> Too Low).
    outcome, _ = check_guess(100, 20)
    assert outcome == "Too High"


# ---------------------------------------------------------------------------
# Streamlit-flow tests (G1, G3, G4) via AppTest.
# ---------------------------------------------------------------------------
def test_g2_even_turn_secret_stays_numeric_end_to_end():
    # G2 (the real reproduction): the glitch only appeared on even-numbered
    # turns, when app.py used to stringify the secret and check_guess then
    # compared lexicographically. We pin the secret, burn one (odd) guess, then
    # on the second (even) guess submit a value that is numerically LOWER but
    # lexically HIGHER than the secret. Old code -> "Go HIGHER" (wrong);
    # fixed code -> "Go LOWER".
    at = AppTest.from_file(APP).run()
    at.session_state["secret"] = 50
    at.run()

    # Guess 1 (attempts -> 1, odd): any wrong guess to advance the turn.
    at.text_input[0].set_value("99")
    next(b for b in at.button if b.label.startswith("Submit")).click().run()

    # Guess 2 (attempts -> 2, even): 9 < 50, but "9" > "50" as text.
    at.text_input[0].set_value("9")
    next(b for b in at.button if b.label.startswith("Submit")).click().run()

    assert "LOWER" in at.warning[0].value
    assert "HIGHER" not in at.warning[0].value


def test_g1_attempts_start_at_zero():
    # G1: attempts must initialize to 0, not 1.
    at = AppTest.from_file(APP).run()
    assert at.session_state["attempts"] == 0
    # Default difficulty is Normal (8 attempts); with attempts=0 the banner
    # should advertise all 8 as remaining.
    assert "Attempts left: 8" in at.info[0].value


def test_g4_info_text_matches_difficulty_range():
    # G4: the info banner must reflect the selected difficulty's range, not a
    # hardcoded "1 and 100".
    at = AppTest.from_file(APP).run()
    at.selectbox[0].set_value("Easy").run()
    assert "between 1 and 20" in at.info[0].value
    assert "between 1 and 100" not in at.info[0].value


def test_g3_new_game_resets_all_state():
    # G3: "New Game" must reset every piece of state, not just attempts/secret.
    at = AppTest.from_file(APP).run()

    # Dirty every field as if a game just finished.
    at.session_state["score"] = 99
    at.session_state["status"] = "won"
    at.session_state["history"] = [11, 22]
    at.session_state["attempts"] = 4
    at.run()

    # Click the New Game button.
    new_game = next(b for b in at.button if b.label.startswith("New Game"))
    new_game.click().run()

    assert at.session_state["attempts"] == 0
    assert at.session_state["score"] == 0
    assert at.session_state["status"] == "playing"
    assert at.session_state["history"] == []
    low, high = get_range_for_difficulty("Normal")
    assert low <= at.session_state["secret"] <= high


# ===========================================================================
# EDGE CASES
# These challenge the code at the margins the original author overlooked.
# ===========================================================================

# ---------------------------------------------------------------------------
# Edge case 1 + 2 (logic): parse_guess must reject out-of-range numbers when a
# range is supplied. The UI advertises a range, so the parser must enforce it.
# ---------------------------------------------------------------------------
def test_ec_parse_guess_rejects_negative():
    ok, value, err = parse_guess("-5", 1, 100)
    assert ok is False
    assert value is None
    assert "between 1 and 100" in err


def test_ec_parse_guess_rejects_zero_below_range():
    ok, _value, _err = parse_guess("0", 1, 20)
    assert ok is False


def test_ec_parse_guess_rejects_above_range():
    ok, _value, _err = parse_guess("150", 1, 100)
    assert ok is False


def test_ec_parse_guess_accepts_range_boundaries():
    # The boundaries themselves are valid (inclusive range).
    assert parse_guess("1", 1, 20)[0] is True
    assert parse_guess("20", 1, 20)[0] is True


def test_ec_parse_guess_backward_compatible_without_range():
    # With no range supplied, behavior is unchanged for existing callers.
    ok, value, _err = parse_guess("9999")
    assert ok is True
    assert value == 9999


# ---------------------------------------------------------------------------
# Edge case 1 (flow): an invalid or out-of-range submission must NOT consume an
# attempt or land in history.
# ---------------------------------------------------------------------------
def test_ec_non_numeric_submission_does_not_consume_attempt():
    at = AppTest.from_file(APP).run()
    assert at.session_state["attempts"] == 0
    at.text_input[0].set_value("abc")
    next(b for b in at.button if b.label.startswith("Submit")).click().run()
    assert at.session_state["attempts"] == 0
    assert at.session_state["history"] == []


def test_ec_out_of_range_submission_does_not_consume_attempt():
    at = AppTest.from_file(APP).run()  # Normal: 1-100
    at.text_input[0].set_value("-5")
    next(b for b in at.button if b.label.startswith("Submit")).click().run()
    assert at.session_state["attempts"] == 0
    assert at.session_state["history"] == []


def test_ec_valid_submission_consumes_exactly_one_attempt():
    at = AppTest.from_file(APP).run()
    at.session_state["secret"] = 50
    at.run()
    at.text_input[0].set_value("40")
    next(b for b in at.button if b.label.startswith("Submit")).click().run()
    assert at.session_state["attempts"] == 1
    assert at.session_state["history"] == [40]


# ---------------------------------------------------------------------------
# Edge case 3 (flow): changing difficulty mid-game must not leave a stale
# secret outside the new range; it starts a fresh game in the new range.
# ---------------------------------------------------------------------------
def test_ec_difficulty_change_regenerates_secret_in_range():
    at = AppTest.from_file(APP).run()        # Normal: 1-100
    at.session_state["secret"] = 99  # legal on Normal, impossible on Easy
    at.session_state["attempts"] = 3
    at.run()

    at.selectbox[0].set_value("Easy").run()  # Easy: 1-20

    low, high = get_range_for_difficulty("Easy")
    assert low <= at.session_state["secret"] <= high
    assert at.session_state["attempts"] == 0
    assert at.session_state["status"] == "playing"

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

from logic_utils import (
    check_guess,
    get_range_for_difficulty,
    narrow_range,
    optimal_guess,
    parse_guess,
    remaining_count,
    update_score,
)

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
# Backwards-hint bug: the hint must point the player the RIGHT way. A guess
# that is too high should say "go lower", and too low should say "go higher".
# The messages used to be inverted.
# ---------------------------------------------------------------------------
def test_hint_too_high_says_go_lower():
    outcome, message = check_guess(80, 30)
    assert outcome == "Too High"
    assert "LOWER" in message.upper()
    assert "HIGHER" not in message.upper()


def test_hint_too_low_says_go_higher():
    outcome, message = check_guess(10, 30)
    assert outcome == "Too Low"
    assert "HIGHER" in message.upper()


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
    # lexically HIGHER than the secret. Correct numeric result -> Too Low ->
    # "Go HIGHER"; the string bug would give Too High -> "Go LOWER", so the
    # hint direction distinguishes the two.
    at = AppTest.from_file(APP).run()
    at.session_state["secret"] = 50
    at.run()

    # Guess 1 (attempts -> 1, odd): any wrong guess to advance the turn.
    at.text_input[0].set_value("99")
    next(b for b in at.button if b.label.startswith("Submit")).click().run()

    # Guess 2 (attempts -> 2, even): 9 < 50, but "9" > "50" as text.
    at.text_input[0].set_value("9")
    next(b for b in at.button if b.label.startswith("Submit")).click().run()

    assert "HIGHER" in at.warning[0].value
    assert "LOWER" not in at.warning[0].value


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


def test_hard_difficulty_has_larger_range_than_normal():
    # Balance regression: Hard used to be 1-50, which made it a smaller search
    # space than Normal's 1-100 range.
    easy_low, easy_high = get_range_for_difficulty("Easy")
    normal_low, normal_high = get_range_for_difficulty("Normal")
    hard_low, hard_high = get_range_for_difficulty("Hard")

    easy_size = easy_high - easy_low + 1
    normal_size = normal_high - normal_low + 1
    hard_size = hard_high - hard_low + 1

    assert easy_size < normal_size < hard_size


def test_hard_difficulty_banner_shows_expanded_range():
    at = AppTest.from_file(APP).run()
    at.selectbox[0].set_value("Hard").run()
    assert "between 1 and 1000" in at.info[0].value


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


# ===========================================================================
# FEATURE: STRATEGY COACH
# narrow_range / remaining_count / optimal_guess are pure, so they get fast
# unit tests; the panel itself gets one end-to-end AppTest.
# ===========================================================================
def test_coach_no_guesses_gives_full_range():
    assert narrow_range([], 50, 1, 100) == (1, 100)


def test_coach_too_high_guess_lowers_upper_bound():
    # 80 > 30 -> upper bound drops to 79.
    assert narrow_range([80], 30, 1, 100) == (1, 79)


def test_coach_too_low_guess_raises_lower_bound():
    # 10 < 30 -> lower bound rises to 11.
    assert narrow_range([10], 30, 1, 100) == (11, 100)


def test_coach_combined_guesses_narrow_both_bounds():
    # 50 too high -> hi=49; 25 too low -> lo=26.
    assert narrow_range([50, 25], 30, 1, 100) == (26, 49)


def test_coach_correct_guess_collapses_range():
    assert narrow_range([42, 50, 42], 42, 1, 100) == (42, 42)


def test_coach_range_always_contains_secret():
    # The core invariant: no sequence of guesses can exclude the secret.
    secret = 37
    lo, hi = narrow_range([50, 20, 40, 30, 35], secret, 1, 100)
    assert lo <= secret <= hi


def test_coach_remaining_count():
    assert remaining_count(26, 49) == 24
    assert remaining_count(42, 42) == 1
    assert remaining_count(50, 49) == 0  # empty range guards to 0


def test_coach_optimal_guess_is_midpoint():
    assert optimal_guess(1, 100) == 50
    assert optimal_guess(26, 49) == 37


def test_coach_panel_shows_narrowed_range_after_guesses():
    at = AppTest.from_file(APP).run()
    at.session_state["secret"] = 30
    at.run()

    # 50 (too high) then 25 (too low) -> feasible range 26-49, 24 numbers left.
    at.text_input[0].set_value("50")
    next(b for b in at.button if b.label.startswith("Submit")).click().run()
    at.text_input[0].set_value("25")
    next(b for b in at.button if b.label.startswith("Submit")).click().run()

    metrics = {m.label: str(m.value) for m in at.metric}
    assert "26" in metrics["Possible range"]
    assert "49" in metrics["Possible range"]
    assert metrics["Numbers left"] == "24"


# ===========================================================================
# B1 — Hard difficulty range and attempt limit
# ===========================================================================
def test_b1_hard_range_is_wider_than_normal():
    low_h, high_h = get_range_for_difficulty("Hard")
    low_n, high_n = get_range_for_difficulty("Normal")
    assert (high_h - low_h) > (high_n - low_n), (
        "Hard must have a wider range than Normal"
    )


def test_b1_hard_range_is_1_to_1000():
    assert get_range_for_difficulty("Hard") == (1, 1000)


# ===========================================================================
# B2 / B3 — update_score: win formula and symmetric wrong-guess penalty
# ===========================================================================
def test_b2_win_attempt_1_scores_100():
    # First-guess win: 100 - 10*(1-1) = 100. Old formula gave 80.
    assert update_score(0, "Win", 1) == 100


def test_b2_win_attempt_2_scores_90():
    assert update_score(0, "Win", 2) == 90


def test_b2_win_attempt_10_scores_10():
    # At the cap boundary: 100 - 10*(10-1) = 10.
    assert update_score(0, "Win", 10) == 10


def test_b2_win_attempt_11_is_capped_at_10():
    # Beyond the cap: 100 - 10*(11-1) = 0, floored to 10.
    assert update_score(0, "Win", 11) == 10


def test_b2_win_adds_to_existing_score():
    assert update_score(50, "Win", 1) == 150


def test_b3_too_high_always_subtracts_5():
    # No parity — both even and odd attempts cost -5.
    assert update_score(100, "Too High", 1) == 95
    assert update_score(100, "Too High", 2) == 95
    assert update_score(100, "Too High", 3) == 95


def test_b3_too_low_always_subtracts_5():
    assert update_score(100, "Too Low", 1) == 95
    assert update_score(100, "Too Low", 2) == 95


def test_b3_wrong_guesses_are_symmetric():
    # "Too High" and "Too Low" must produce identical score changes.
    score_high = update_score(100, "Too High", 1)
    score_low = update_score(100, "Too Low", 1)
    assert score_high == score_low


def test_update_score_unknown_outcome_unchanged():
    assert update_score(42, "Unknown", 1) == 42


# ===========================================================================
# B7 — duplicate guesses must not consume an attempt
# ===========================================================================
def test_b7_duplicate_guess_does_not_consume_attempt():
    at = AppTest.from_file(APP).run()
    at.session_state["secret"] = 50
    at.run()

    # First submission: valid, consumes attempt 1.
    at.text_input[0].set_value("30")
    next(b for b in at.button if b.label.startswith("Submit")).click().run()
    assert at.session_state["attempts"] == 1

    # Second submission of the same number: must NOT consume attempt 2.
    at.text_input[0].set_value("30")
    next(b for b in at.button if b.label.startswith("Submit")).click().run()
    assert at.session_state["attempts"] == 1
    assert at.session_state["history"].count(30) == 1

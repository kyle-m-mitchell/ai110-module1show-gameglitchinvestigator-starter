import random

import streamlit as st

# REFACTOR: WHAT - the four pure-logic functions used to live in this file.
# WHY - mixing logic with UI made the logic impossible to unit-test and made
# this file hard to read. HOW - they were moved to logic_utils.py and are now
# imported (one name per line, per PEP 8).
from logic_utils import (
    check_guess,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)


def reset_game(difficulty, low, high):
    """Reset all per-game session state to a fresh, playable game.

    REFACTOR: WHAT - centralizes the five-field reset that was duplicated
    across first-load init, the New Game button, and the difficulty-change
    handler. WHY - three hand-maintained copies could drift out of sync (the
    original New Game bug, G3, was exactly such a drift). HOW - a single helper
    every reset site calls, so the set of fields can only be defined once.

    Args:
        difficulty: The difficulty the new game is played at; recorded so a
            later difficulty change can be detected.
        low: Inclusive lower bound the secret is drawn from.
        high: Inclusive upper bound the secret is drawn from.
    """
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.game_difficulty = difficulty


st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

# BUG FIX (G1): WHAT - attempts now start at 0 (they used to start at 1).
# WHY - starting at 1 made "Attempts left" off by one, stole a guess via the
# loss check, and skewed the score. HOW - reset_game initializes attempts to 0
# on first load. (The first-load guard keys on "secret" being absent.)
if "secret" not in st.session_state:
    reset_game(difficulty, low, high)

# BUG FIX (edge case 3): WHAT - changing difficulty mid-game now starts a fresh
# game in the new range. WHY - the secret was generated once under the original
# difficulty; switching difficulty left a stale secret that could fall outside
# the new range, making the game unwinnable and "Attempts left" go negative.
# HOW - track the difficulty the current game was created under and, when it no
# longer matches the dropdown, rebuild the game so the invariant "secret is
# always inside the current range" holds.
if difficulty != st.session_state.game_difficulty:
    reset_game(difficulty, low, high)

st.subheader("Make a guess")

# BUG FIX (G4): WHAT - the banner reports the real difficulty range, not a
# hardcoded "1 and 100". WHY - on Easy/Hard the old text lied about the range.
# HOW - interpolate the computed low/high values.
st.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

# REFACTOR: WHAT - wrapped the text input and submit button in an st.form.
# WHY - so pressing Enter in the box submits the same way the button does.
# HOW - st.form batches the widgets and fires once on form submit.
with st.form(key=f"guess_form_{difficulty}"):
    raw_guess = st.text_input(
        "Enter your guess:",
        key=f"guess_input_{difficulty}",
    )
    submit = st.form_submit_button("Submit Guess 🚀")

# REFACTOR: WHAT - dropped the now-unused third column. WHY - the submit button
# moved into the form above, so only New Game and the hint checkbox remain.
col1, col2 = st.columns(2)
with col1:
    new_game = st.button("New Game 🔁")
with col2:
    show_hint = st.checkbox("Show hint", value=True)

# BUG FIX (G3): WHAT - New Game now resets every per-game field, not just
# attempts and secret. WHY - score, status, and history used to persist, so a
# finished game's "won"/"lost" status immediately stopped the new one. HOW -
# delegate to reset_game so all five fields (and the range) are reset together.
if new_game:
    reset_game(difficulty, low, high)
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    # BUG FIX (edge cases 1 & 2): WHAT - validate the input (including range)
    # BEFORE counting the attempt. WHY - the attempt counter used to increment
    # first, so an empty/invalid/out-of-range submission burned a guess and
    # pushed junk into history. HOW - parse first (passing the range); only on
    # a valid guess do we increment attempts and record history.
    ok, guess_int, err = parse_guess(raw_guess, low, high)

    if not ok:
        st.error(err)
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        # BUG FIX (G2): WHAT - pass the real integer secret to check_guess.
        # WHY - the old code turned the secret into a string on every other
        # turn, triggering broken string comparison and wrong hints. HOW - the
        # stringification was removed; the true secret is passed directly.
        outcome, message = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"Out of attempts! "
                    f"The secret was {st.session_state.secret}. "
                    f"Score: {st.session_state.score}"
                )

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")

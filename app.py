import os
import random

import streamlit as st

# REFACTOR: WHAT - the four pure-logic functions used to live in this file.
# WHY - mixing logic with UI made the logic impossible to unit-test and made
# this file hard to read. HOW - they were moved to logic_utils.py and are now
# imported (one name per line, per PEP 8).
from logic_utils import (
    check_guess,
    get_range_for_difficulty,
    narrow_range,
    optimal_guess,
    parse_guess,
    remaining_count,
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

# ENHANCED UI: load the custom palette/CSS layer (kept in a separate file so
# app.py stays PEP 8 clean). Pathed off this file so it resolves no matter the
# working directory.
_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "style.css")) as _css:
    st.markdown(f"<style>{_css.read()}</style>", unsafe_allow_html=True)

# ENHANCED UI: gradient hero header in place of the plain title/caption.
st.markdown(
    """
<div class="hero">
  <h1>🎮 Game Glitch Investigator</h1>
  <p>Crack the secret number. Outsmart the machine.</p>
</div>
""",
    unsafe_allow_html=True,
)

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

# FEATURE (Strategy Coach): toggles for the live strategy readout. The coach is
# on by default; the explicit optimal-guess suggestion is a separate opt-in so
# it doesn't trivialize the game. The second box only appears when the coach is
# on, so there is never a dangling control.
coach_on = st.sidebar.checkbox("🧭 Strategy Coach", value=True)
show_optimal = (
    st.sidebar.checkbox("Show optimal next guess", value=False)
    if coach_on
    else False
)

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

# ENHANCED UI: Wordle-style history chips. Each past guess is shown as a
# colored pill (red = too high, blue = too low, green = the winning guess),
# giving instant visual feedback on the player's trail. Rendered after the
# submit handler so it includes the guess just made.
if st.session_state.history:
    secret = st.session_state.secret
    chips = []
    for past_guess in st.session_state.history:
        if past_guess == secret:
            chip_class = "chip-win"
        elif past_guess > secret:
            chip_class = "chip-high"
        else:
            chip_class = "chip-low"
        chips.append(
            f'<span class="chip {chip_class}">{past_guess}</span>'
        )
    st.markdown("**Your guesses**")
    st.markdown(
        '<div class="chips">' + "".join(chips) + "</div>",
        unsafe_allow_html=True,
    )

# FEATURE (Strategy Coach): a live readout of the still-feasible range, how
# much of the search space is ruled out, and (opt-in) the best next guess.
# Rendered after the submit handler so it reflects the latest guess, and only
# while the game is in progress so it disappears on win/loss. Derived purely
# from existing state (history + secret + range), so it cannot desync.
if coach_on and st.session_state.status == "playing":
    lo, hi = narrow_range(
        st.session_state.history, st.session_state.secret, low, high
    )
    count = remaining_count(lo, hi)
    total = high - low + 1
    ruled_out = round((1 - count / total) * 100)

    st.subheader("🧭 Strategy Coach")
    coach_col1, coach_col2 = st.columns(2)
    coach_col1.metric("Possible range", f"{lo}–{hi}")
    coach_col2.metric("Numbers left", count)
    st.progress(1 - count / total)
    st.caption(f"{ruled_out}% of the range ruled out.")

    if show_optimal:
        st.info(f"Optimal next guess: {optimal_guess(lo, hi)}")

st.divider()
# ENHANCED UI: styled footer.
st.markdown(
    '<div class="app-footer">Built by an AI that claimed this code was '
    "production-ready — debugged, tested, and redesigned by a human.</div>",
    unsafe_allow_html=True,
)

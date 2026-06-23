"""Pure game logic for the Game Glitch Investigator guessing game.

REFACTOR: these four functions were extracted verbatim from app.py so the
game's logic can be unit-tested without launching Streamlit and so app.py is
left with only its UI/flow concerns.
"""


def get_range_for_difficulty(difficulty: str):
    """Return the inclusive guessing range for a difficulty level.

    Args:
        difficulty: One of ``"Easy"``, ``"Normal"``, or ``"Hard"``. Any
            unrecognized value falls back to the Normal range.

    Returns:
        A ``(low, high)`` tuple of ints describing the inclusive range the
        secret number is drawn from.
    """
    # REFACTOR: moved from app.py unchanged. (Note: the Hard range is still a
    # known design quirk, not yet addressed.)
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str, low: int | None = None, high: int | None = None):
    """Parse raw user input into a validated integer guess.

    Numeric text is converted to an int (decimals are truncated, e.g.
    ``"3.9"`` -> ``3``). When both ``low`` and ``high`` are supplied, the
    parsed value must fall within the inclusive range or it is rejected.

    Args:
        raw: The raw text entered by the player. May be ``None`` or empty.
        low: Optional inclusive lower bound for range validation.
        high: Optional inclusive upper bound for range validation.

    Returns:
        A ``(ok, guess, error)`` tuple where:
            * ``ok`` (bool): True if the input is a valid, in-range integer.
            * ``guess`` (int | None): the parsed int when ``ok`` is True,
              otherwise None.
            * ``error`` (str | None): a user-facing message when ``ok`` is
              False, otherwise None.
    """
    # BUG FIX (edge case 2): WHAT - reject numbers outside the active range.
    # WHY - the UI promises "a number between low and high", but the parser
    # previously accepted any integer (e.g. -5, 0, 999), violating that
    # contract and letting players waste turns on impossible guesses.
    # HOW - validate against the optional low/high bounds before returning ok.
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    if low is not None and high is not None and not (low <= value <= high):
        return False, None, f"Guess must be between {low} and {high}."

    return True, value, None


def check_guess(guess, secret):
    """Compare a guess against the secret number.

    Args:
        guess: The player's integer guess.
        secret: The secret integer to compare against.

    Returns:
        An ``(outcome, message)`` tuple. ``outcome`` is one of ``"Win"``,
        ``"Too High"``, or ``"Too Low"``; ``message`` is the matching
        user-facing hint string.
    """
    # BUG FIX (G2): WHAT - removed a try/except TypeError fallback that did
    # lexicographic string comparison (so "9" > "50" wrongly read as "higher").
    # WHY - app.py used to stringify the secret on every other turn, dropping
    # into that branch and producing wrong hints. HOW - that stringification
    # was removed in app.py, so the secret is always an int here; a plain
    # numeric comparison is now correct and the dead branch is gone.
    # BUG FIX (backwards hints): WHAT - swapped the two hint messages. WHY - a
    # guess that is too HIGH must tell the player to go LOWER (and vice versa),
    # but the messages were inverted ("Too High" said "Go HIGHER!"), sending
    # players the wrong way. HOW - pair each outcome with the correct
    # direction word and arrow. (The outcome labels themselves were correct.)
    if guess == secret:
        return "Win", "🎉 Correct!"
    if guess > secret:
        return "Too High", "📉 Go LOWER!"
    return "Too Low", "📈 Go HIGHER!"


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Return the new score after applying the result of one guess.

    Args:
        current_score: The score before this guess.
        outcome: The result from :func:`check_guess` (``"Win"``,
            ``"Too High"``, or ``"Too Low"``).
        attempt_number: The 1-based count of guesses taken so far.

    Returns:
        The updated integer score. An unrecognized ``outcome`` leaves the
        score unchanged.
    """
    # REFACTOR: moved from app.py unchanged. (Note: the win formula and the
    # asymmetric "Too High" scoring remain known design quirks, not yet
    # addressed.)
    if outcome == "Win":
        points = 100 - 10 * (attempt_number + 1)
        if points < 10:
            points = 10
        return current_score + points

    if outcome == "Too High":
        if attempt_number % 2 == 0:
            return current_score + 5
        return current_score - 5

    if outcome == "Too Low":
        return current_score - 5

    return current_score

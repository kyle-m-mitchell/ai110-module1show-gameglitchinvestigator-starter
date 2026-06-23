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
    # BUG FIX (B1): WHAT - Hard now returns (1, 1000) instead of (1, 50).
    # WHY - 1-50 is narrower than Normal's 1-100, making Hard accidentally
    # easier; worse, binary search needs ceil(log2(50))=6 steps but Hard only
    # gave 5 attempts, so optimal play could never win. HOW - widen Hard to
    # 1-1000 (needs ceil(log2(1000))=10 steps) and set its attempt limit to 10
    # in app.py so perfect play can just barely win — a genuinely hard game.
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 1000
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
    # BUG FIX (B2): WHAT - win formula changed from (attempt_number + 1) to
    # (attempt_number - 1). WHY - attempt_number is already 1-based, so + 1
    # added a phantom deduction: guessing correctly on try 1 gave 80 points
    # instead of 100. HOW - subtract one fewer step so attempt 1 scores 100,
    # attempt 2 scores 90, ..., attempt 10+ scores the 10-point floor.
    if outcome == "Win":
        points = 100 - 10 * (attempt_number - 1)
        if points < 10:
            points = 10
        return current_score + points

    # BUG FIX (B3): WHAT - removed the parity branch that awarded +5 on even
    # attempts for "Too High". WHY - the reward was invisible to players
    # (depends on turn parity, not skill) and created an asymmetry where "Too
    # High" was sometimes rewarded while "Too Low" was always penalized. HOW -
    # both wrong-direction outcomes now apply the same -5 penalty, making
    # scoring symmetric and predictable.
    if outcome in ("Too High", "Too Low"):
        return current_score - 5

    return current_score


def narrow_range(guesses, secret, low, high):
    """Return the range of values still consistent with the guesses so far.

    FEATURE (Strategy Coach): given the player's past guesses and the secret,
    this reconstructs the ``(lo, hi)`` window a player following the
    higher/lower hints would have deduced. A guess below the secret raises the
    lower bound; a guess above it lowers the upper bound; the exact guess
    collapses the window to that single value.

    Because the secret always lies inside ``[low, high]`` and each bound only
    moves toward (never past) the secret, the returned range always satisfies
    ``lo <= secret <= hi`` and can never become empty.

    Args:
        guesses: Iterable of integer guesses made this game (e.g. the
            ``history`` list).
        secret: The secret integer being guessed.
        low: Inclusive lower bound of the full difficulty range.
        high: Inclusive upper bound of the full difficulty range.

    Returns:
        A ``(lo, hi)`` tuple of ints describing the still-feasible inclusive
        range.
    """
    lo, hi = low, high
    for guess in guesses:
        if guess == secret:
            return guess, guess
        if guess < secret:
            lo = max(lo, guess + 1)
        else:
            hi = min(hi, guess - 1)
    return lo, hi


def remaining_count(lo, hi):
    """Return how many integers remain in an inclusive ``[lo, hi]`` range.

    FEATURE (Strategy Coach): drives the "numbers left" metric and the
    proportion of the search space ruled out.

    Args:
        lo: Inclusive lower bound.
        hi: Inclusive upper bound.

    Returns:
        The count of integers in ``[lo, hi]``, or 0 if the range is empty.
    """
    return max(0, hi - lo + 1)


def optimal_guess(lo, hi):
    """Return the guess that best halves an inclusive ``[lo, hi]`` range.

    FEATURE (Strategy Coach): the midpoint is the binary-search choice that
    minimizes the worst-case number of possibilities remaining after the
    guess.

    Args:
        lo: Inclusive lower bound of the still-feasible range.
        hi: Inclusive upper bound of the still-feasible range.

    Returns:
        The midpoint integer ``(lo + hi) // 2``.
    """
    return (lo + hi) // 2

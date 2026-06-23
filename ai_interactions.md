# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I asked it to add an impressive, meaningful new feature that dramatically
changes how the game plays — a real tool for the player — without breaking the
existing logic or tests, and with the behavior kept unambiguous. We settled on
a **Strategy Coach**: a live panel that narrows the still-possible range as you
guess, shows how much of the search space you've ruled out, and (opt-in)
suggests the optimal next guess.

**What did the agent do?**

It worked in distinct, multi-step phases:

1. **Planned first (Plan mode).** It proposed the feature, asked me to choose
   between four options, and wrote a written plan I approved before any code
   changed.
2. **Added pure logic** to `logic_utils.py`: `narrow_range`,
   `remaining_count`, and `optimal_guess`, each with a docstring and a
   `FEATURE`-labeled comment.
3. **Wired the UI** in `app.py`: a sidebar "Strategy Coach" toggle (on by
   default) plus a nested opt-in "Show optimal next guess", and a panel using
   `st.metric` / `st.progress` rendered only mid-game.
4. **Wrote tests** in `tests/test_game_logic.py`: 8 unit tests (including an
   invariant test proving the feasible range always contains the secret) and
   1 end-to-end AppTest driving the real app.
5. **Ran the tooling itself**: `python -m pytest` and
   `python -m pycodestyle --max-line-length=79`, and fixed its own line-length
   violation until both were clean (29 tests passing, 0 style violations).

**What did you have to verify or fix manually?**

- I **found a bug the agent missed**: the higher/lower hints were backwards
  ("Too High" told me to go HIGHER). It had carried this over verbatim from the
  original code during an earlier fix. After I reported it, it fixed the
  messages and added regression tests.
- That bug also exposed a **flawed test** it had written earlier: a test
  asserted on the hint's display text, which itself was buggy, so the test had
  been passing for the wrong reason. It corrected the test to check the outcome
  and direction together.
- I **reviewed every diff** as it went and made several of the earlier edits
  myself, with the agent checking my work — so the workflow was collaborative
  review, not blind acceptance.

---

## Test Generation (SF7)

> Document how you used AI to help generate or improve tests.

| Edge Case | Prompt Used | AI-Suggested Test | Did It Pass? | Your Reasoning |

| Edge case 1 — Ordering bug: an invalid submission burns an attempt. | help me identify and fix three edge cases that break my game if not resolved; help me with the thought process behind identifying these edge cases - help me think like an expert; create a suite of pytest cases that challenge the code we've put together, specifically focusing on the edge cases we've identified; explain, teach, and conceptualize the solutions to me so that I understand it from it's core | type "abc", submit an empty box, or press Enter with no input | Yes. | It now only acknowledges valid input as a guess attempt because we set a validation check before the counter is updated. Parse first, count second.|

| Edge case 2 — Input-domain bug: out-of-range numbers are accepted as legit guesses. | help me identify and fix three edge cases that break my game if not resolved; help me with the thought process behind identifying these edge cases - help me think like an expert; create a suite of pytest cases that challenge the code we've put together, specifically focusing on the edge cases we've identified; explain, teach, and conceptualize the solutions to me so that I understand it from it's core | Guessing with -5, 0, and 999999 | Yes | We ask, "what's the strangest thing a user could submit?" From here, we test negatives, 0, and an immense number. It now only accepts valid number guesses as an attempt because validation matches real-world logic, not just data type. |

| Edge case 3 — State-transition bug: changing difficulty mid-game makes it unwinnable. | help me identify and fix three edge cases that break my game if not resolved; help me with the thought process behind identifying these edge cases - help me think like an expert; create a suite of pytest cases that challenge the code we've put together, specifically focusing on the edge cases we've identified; explain, teach, and conceptualize the solutions to me so that I understand it from it's core | Start a new game at Normal Difficulty, then switch to Easy or Hard. The acceptable range changes when the difficulty changes. | Yes | We set the code to auto-reset to a New Game whenever the difficulty is changed because it is a property of the game, not a mid-game option. |


---

## Linting & Style (SF9)

> Document your use of AI for linting or code style improvements.

**Prompt used:**

```
Then review my code for PEP 8 style compliance and apply recommended fixes
to resolve formatting or naming issues.
```

(Tool & command used: `pycodestyle` at the strict 79-character limit —
`python3 -m pycodestyle --max-line-length=79 app.py logic_utils.py tests/test_game_logic.py conftest.py`)

**Linting output before:**

```
app.py:84:80: E501 line too long (80 > 79 characters)
app.py:150:80: E501 line too long (80 > 79 characters)
tests/test_game_logic.py:22:1: E402 module level import not at top of file
tests/test_game_logic.py:56:80: E501 line too long (80 > 79 characters)
tests/test_game_logic.py:62:80: E501 line too long (84 > 79 characters)
tests/test_game_logic.py:70:1: E402 module level import not at top of file
tests/test_game_logic.py:78:80: E501 line too long (80 > 79 characters)
tests/test_game_logic.py:84:80: E501 line too long (80 > 79 characters)
tests/test_game_logic.py:88:80: E501 line too long (80 > 79 characters)
tests/test_game_logic.py:208:80: E501 line too long (80 > 79 characters)
tests/test_game_logic.py:213:80: E501 line too long (82 > 79 characters)
```

11 violations across two rule codes: **E501** (line too long) ×9 and
**E402** (import not at top of file) ×2. After the fixes, the same command
reported `0 violations`.

**Changes applied:**

- **E501 (×9):** every long line was a *comment*, so each was reworded or
  wrapped to fit 79 characters — no logic changed. Examples: shortened the G4
  comment in `app.py:84` ("instead of a" → "not a"), replaced
  "lexicographically" with "lexically" / "as text" in several test comments,
  wrapped the edge-case-3 comment onto two lines, and collapsed an over-wide
  inline-comment alignment gap to two spaces.
- **E402 (×2):** the test file ran `sys.path` manipulation *before* its
  imports, which pushed those imports below executable code. Fixed by moving
  the `sys.path` responsibility into a new root **`conftest.py`** (the
  idiomatic pytest way to make the repo root importable), then hoisting all
  imports to the top of the test file and deleting the now-duplicate
  `AppTest` import lower down.
- **Verification:** all 18 tests still passed after the cleanup, confirming
  the style fixes were behavior-preserving.

---

## Model Comparison (SF11)

> Compare two AI models on the same task.

**Task given to both models:**

<!-- Describe what you asked each model to do -->

| | Model A | Model B |
|-|---------|---------|
| **Model name** | | |
| **Response summary** | | |
| **More Pythonic?** | | |
| **Clearer explanation?** | | |

**Which did you prefer and why?**

<!-- Your conclusion -->

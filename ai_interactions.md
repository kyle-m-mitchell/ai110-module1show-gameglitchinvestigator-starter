# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

<!-- Describe the goal you asked the agent to accomplish -->

**What did the agent do?**

<!-- List the steps the agent took (files edited, commands run, etc.) -->

**What did you have to verify or fix manually?**

<!-- Describe anything the agent got wrong or that required human review -->

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
<!-- Paste the prompt you gave the AI -->
```

**Linting output before:**

```
<!-- Paste relevant linter warnings/errors -->
```

**Changes applied:**

<!-- Describe what you changed based on the AI's suggestions -->

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

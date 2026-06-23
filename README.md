# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the broken app: `python -m streamlit run app.py`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*

You store the variable and keep it from resetting by using session state. Streamlit reruns the script after every interaction. Use st.session_state to store information that must survive reruns.

3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

- [ ] Describe the game's purpose. 
   The purpose of the game is to guess a secret number between a set range of values (determined by the games overall difficulty setting.)
- [ ] Detail which bugs you found.
- [ ] Explain what fixes you applied.

## 📸 Demo Walkthrough

Describe your fixed game in numbered steps so a reader can follow along without watching a video:

1. User enters a guess of 50
2. The game returns a hint that's either "Too Low" or "Too High" depending on the secret
3. User enters a guess of 25; the game returns "Too Low" or "Too High" depending on the secret
4. Score and attempts update after each guess
5. Game ends after the correct guess or when out of attempts

**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🧪 Test Results

```
# ========================== test session starts ===========================
platform darwin -- Python 3.14.5, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/kylemitchell/ai110-module1show-gameglitchinvestigator-starter
plugins: anyio-4.13.0
collected 18 items                                                       

tests/test_game_logic.py ..................                        [100%]

=========================== 18 passed in 2.48s ===========================

## 🚀 Stretch Features

- [ ] [If you choose to complete Challenge 4, describe the Enhanced UI changes here — a screenshot is optional]

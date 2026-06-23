# 💭 Reflection: Game Glitch Investigator

## Completed by Kyle M. Mitchell

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it? 

I could tell that it had several bugs by just running it once. After observing the Developer Debug Info I noticed that the scoring convention looked off and the history was inaccurate. However, it accepted the numbers I guessed and I was able to make it to the end of the game, I just couldn't restart it. 

- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").

  the attempt counter is inaccurate, pressing enter as prompted doesn't work

**Bug Reproduction Log**

Document at least 3 bugs you found. Add rows as needed.

| Input | Expected Behavior | Actual Behavior | Console Output / Error |

| playing a full game and losing at normal difficulty | Hitting the new game button will restart the game and the Developer Debug Info resets | the game never restarts and the game over message is still displayed, the Developer Debug info partially resets and the submission history log doesn't reset inside it | none |

| guess of 100 at normal difficulty | the program tells me the number is too high | the program gives a hint to go higher | none |

| guessing the secret at normal difficulty | I can start a new game and can submit a new guess | the new guess isn't accepted and the game freezes | none |

| guessing 1 at normal difficulty| hint: "Go Higher!", the secret is 51 | hint: "Go Lower!"| none |

| guessing 0 at normal difficulty | a message will appear to the user indicating that the number is invalid, wrong, or not within the parameters of 1-100 | hint: "Go Lower!" | none |

| guessing 71.1 - 71.9 at normal difficulty | it will not accept it because it is not the exact number | the secret was 71 and submitting 71.1 or 71.9 won the game | none |

| starting a new game after playing one at normal difficulty | the score to reset to 0 | the score reset to 10 | none |

| pressing enter on the keyboard to submit a guess at normal difficulty | the guess is submitted | the guess will not submit and the message disappears | none |

| negative numbers at normal difficulty | the guess will not submit and it will let the user know that it doesn't accept negative numbers or the guess is out of bounds | gives a hint to go lower | none |

| starting a new game for the first time at normal difficulty | the attempts counter resets to 0 and Attempts left is set to 8 | the counter starts at 1 | none |

| guesses | the Developer Debug history log prints the number you just submitted | the history prints only up to 5 of the guesses, does strange calculations sometimes, doubles, and out of order | none |

| a guess one value smaller or larger than the answer  | Hint: "Go Lower!" "Go Higher!" | it won't accept a guess one value lower and if it's larger it will say "Go Higher!" | none |

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)? 

Claude Code, Claude

- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result). 

It suggested we reference the documentation for Streamlit to resolve the bug where pressing "Enter" on the keyboard didn't submit the guess. We put the guess box and its submit button inside a st.form container to define the behavior of pressing Enter being the equivalent of clicking submit. I reviewed the documentation it pointed me to and studied the syntax. It suggested a fix for it and I compared it with the documentation before approving it and I also challenged it on whether this was the most effective and efficient fix for this bug. I performed a set of tests to evalutate the fix and found that the fix was complete and I verified it as fixed.

- Give one example of an AI suggestion that was incorrect or misleading (including what the AI suggested and how you verified the result).

It mislead me by making me think we must use a handler to resolve the "Enter" key bug. The documentation for Streamlit has a more efficient way of doing so through its syntax. Just by referring to the documentation, we found a way to resolve this problem with fewer lines of code.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed? 

I instructed Claude to generate pytests for each bug we fixed. I then ran a series of tests and edge cases to confirm and verify the completion of a bug being fixed or not. 

- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.

Claude suggested we use Streamlit's official AppTest harness to run app.py in a headless simulator to inspect session_state and widgets. When running the tests, Claude Code found that the initial test scripts were broken so it fixed them and wrote some additional tests to cover the bugs we've found. It mostly showed me what kind of tests I should be performing to solidify a permanent fix; regression tests. Through them, we performed these tests to confirm that the bug solutions are permanent fixes. 

- Did AI help you design or understand any tests? How?

Yes. Claude Code re-broke the fixes we made to help me visualize and conceptualize the bugs that were initially present in the code. It also helped me become familiar with pytests and how they work. I learned that pytest works by discovery and convention. It finds files named test_*.py, and it looks for functions in the scripts that are named test_* . I also learned that each test function is independent and are run in isolation. Claude explained that the test script didn't live in the same directory path as the scripts we were testing so we manually set the sys.path . It also showed me how to use Streamlit's AppTest simulator to identify and confirm fixes for bugs that appear when the app is ran. 

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

Streamlit is a third-party library that gives you the ability to turn data into web applications. It does so through stateful or statelessness. Everytime a user interacts with a widget, in Streamlit, the script is reran from the top. Stateful variables record and retain informatiion through reruns of the script. Stateless variables reset through script reruns. For Streamlit, plain variables are stateless and are erased/ reset everytime the script reruns. State is kept through st.session_state, a dictionary where you can store manual memory for a state and then there's the automatic memory that's built into the widgets. Widgets remember their own value across reuruns for you in Streamlit.
---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?

  - This could be a testing habit, a prompting strategy, or a way you used Git.

  I definitely will take the debugging and thought process for interacting with AI with me as I work on future labs. I'm still learning how to write clean code and the debugging exercises helped me identify areas in my coding process that need more attention and focus. I'm also growing to communicate in a constructive manner with AI.

- What is one thing you would do differently next time you work with AI on a coding task?

I will ask it to ask me questions to clear ambiguity in the code or logic errors. 

- In one or two sentences, describe how this project changed the way you think about AI generated code.

Though AI generated code seems impressive, it can hold many bugs and needs to be reviewed and evaluated before it is considered correct. It can overcomplicate the logic it generates. Sometimes, it will steer the logic in a direction the engineer was not intending to go.

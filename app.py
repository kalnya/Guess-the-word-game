from flask import Flask, render_template, request, redirect, url_for
from random_word import RandomWords
import random

app = Flask(__name__)

# Initialize RandomWords instance
random_words = RandomWords()

# Difficulty map for word lengths
difficulty_map = {
    "easy": (5, 6),
    "medium": (7, 8),
    "hard": (9, 15)
}

# Initialize game variables
selected_word = ""
hidden_word = []
attempts = 5
used_letters = []
wrong_letters = []

# Function to fetch a random word based on difficulty
def generate_random_word(min_length, max_length):
    retries = 100  # Retry limit
    for _ in range(retries):
        word = random_words.get_random_word()  # Fetch a random word
        if word and word.isalpha() and min_length <= len(word) <= max_length:
            print(f"Generated word: {word}")  # Debugging
            return word.lower()
    # If no valid word is generated, return None
    print("Failed to generate a valid word after retries.")  # Debugging
    return None

# Function to reset the game
def reset_game():
    global selected_word, hidden_word, attempts, used_letters, wrong_letters
    selected_word = ""
    hidden_word = []
    attempts = 5
    used_letters = []
    wrong_letters = []

@app.route("/", methods=["GET", "POST"])
def home():
    global selected_word, hidden_word, attempts, used_letters, wrong_letters, hints_remaining

    message = ""

    if not selected_word:
        if request.method == "POST" and "start" in request.form:
            difficulty = request.form["difficulty"]
            min_length, max_length = difficulty_map[difficulty]

            # Set hints based on difficulty
            if difficulty == "easy":
                hints_remaining = 3
            elif difficulty == "medium":
                hints_remaining = 4
            elif difficulty == "hard":
                hints_remaining = 5

            selected_word = generate_random_word(min_length, max_length)
            if not selected_word:
                message = "Unable to generate a valid word. Please try again."
                return render_template(
                    "index.html", 
                    word=None, 
                    message=message, 
                    attempts=None, 
                    wrong_letters=None, 
                    used_letters=[]
                )

            hidden_word = ["_"] * len(selected_word)
            attempts = 6
            used_letters = []
            wrong_letters = []
            return redirect(url_for("home"))

        return render_template(
            "index.html",
            word=None,
            attempts=None,
            wrong_letters=None,
            message=message,
            used_letters=[]
        )

    if request.method == "POST":
        if "reset" in request.form:  # Reset game
            reset_game()
            return redirect(url_for("home"))

        if "hint" in request.form:
            if hints_remaining > 0 and attempts > 1:
                revealed = False
                for i, char in enumerate(selected_word):
                    if hidden_word[i] == "_":
                        hidden_word[i] = char
                        hints_remaining -= 1
                        attempts -= 1
                        message = f"Hint used! '{char}' revealed. Hints left: {hints_remaining}. Attempts left: {attempts}."
                        revealed = True
                        break
                if not revealed:
                    message = "No more letters to reveal!"
            elif hints_remaining <= 0:
                message = "No hints remaining!"
            elif attempts <= 1:
                message = "Cannot use hints with one attempt left!"

        elif "letter" in request.form:
            letter = request.form["letter"].lower()
            if letter in used_letters:
                message = f"You already guessed '{letter}'. Try a different letter."
            elif letter in selected_word:
                used_letters.append(letter)
                for i, char in enumerate(selected_word):
                    if char == letter:
                        hidden_word[i] = letter
                message = "Correct guess!"
            else:
                attempts -= 1
                wrong_letters.append(letter)
                used_letters.append(letter)
                message = f"'{letter}' is not in the word. Attempts left: {attempts}"

    if "_" not in hidden_word:
        message = f"Congratulations! You guessed the word: '{selected_word}'! Play again?"
    elif attempts <= 0:
        message = f"Game Over! The word was '{selected_word}'. Play again?"

    return render_template(
        "index.html",
        word=" ".join(hidden_word),
        attempts=attempts,
        wrong_letters=", ".join(wrong_letters),
        message=message,
        used_letters=used_letters,
        hints_remaining=hints_remaining
    )

if __name__ == "__main__":
    app.run(debug=True)

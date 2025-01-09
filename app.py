from flask import Flask, render_template, request, redirect, url_for, session
from random_word import RandomWords

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a secure random key

# Initialize RandomWords instance
random_words = RandomWords()

# Difficulty map for word lengths
difficulty_map = {
    "easy": (5, 6),
    "medium": (7, 8),
    "hard": (9, 15)
}

# Function to fetch a random word based on difficulty
def generate_random_word(min_length, max_length):
    retries = 100  # Retry limit
    for _ in range(retries):
        word = random_words.get_random_word()  # Fetch a random word
        if word and word.isalpha() and min_length <= len(word) <= max_length:
            print(f"Generated word: {word}")  # Debugging
            return word.lower()
    print("Failed to generate a valid word after retries.")  # Debugging
    return None

# Function to reset the game
def reset_game():
    session['selected_word'] = ""
    session['hidden_word'] = []
    session['attempts'] = 0
    session['used_letters'] = []
    session['wrong_letters'] = []
    session['hints_remaining'] = 0
    session['message'] = ""  # Clear the message

# Function to update the hidden word with correct guesses
def update_hidden_word():
    """Update hidden_word to show all correctly guessed letters."""
    session['hidden_word'] = [
        char if char in session['used_letters'] else "_"
        for char in session['selected_word']
    ]
@app.route("/", methods=["GET", "POST"])
def home():
    if 'selected_word' not in session or not session['selected_word']:
        reset_game()

    # Handle POST requests (start, reset, hint, letter)
    if request.method == "POST":
        if "start" in request.form:  # Start game with chosen difficulty
            reset_game()
            difficulty = request.form["difficulty"]
            min_length, max_length = difficulty_map[difficulty]

            # Set hints and attempts based on difficulty
            session['hints_remaining'] = {"easy": 3, "medium": 4, "hard": 5}[difficulty]
            session['attempts'] = {"easy": 5, "medium": 6, "hard": 7}[difficulty]

            session['selected_word'] = generate_random_word(min_length, max_length)
            if not session['selected_word']:
                session['message'] = "Unable to generate a valid word. Please try again."
                return render_template(
                    "index.html",
                    word=None,
                    message=session['message'],
                    attempts=None,
                    wrong_letters=None,
                    used_letters=[]
                )

            session['hidden_word'] = ["_"] * len(session['selected_word'])
            session['used_letters'] = []
            session['wrong_letters'] = []
            return redirect(url_for("home"))

        if "reset" in request.form:  # Reset game and redirect to difficulty selection
            reset_game()
            session['message'] = ""  # Clear any leftover message
            return redirect(url_for("home"))

        if "hint" in request.form:
            if session['hints_remaining'] > 0 and session['attempts'] > 1:
                for i, char in enumerate(session['selected_word']):
                    if session['hidden_word'][i] == "_":
                        session['used_letters'].append(char)
                        session['hints_remaining'] -= 1
                        session['attempts'] -= 1
                        update_hidden_word()
                        session['message'] = f"Hint used! '{char}' revealed. Hints left: {session['hints_remaining']}. Attempts left: {session['attempts']}."
                        break
                else:
                    session['message'] = "No more letters to reveal!"
            elif session['hints_remaining'] <= 0:
                session['message'] = "No hints remaining!"
            elif session['attempts'] <= 1:
                session['message'] = "Cannot use hints with one attempt left!"

        if "letter" in request.form:
            letter = request.form["letter"].lower()
            if letter in session['used_letters']:
                session['message'] = f"You already guessed '{letter}'. Try a different letter."
            elif letter in session['selected_word']:
                session['used_letters'].append(letter)
                update_hidden_word()
                session['message'] = "Correct guess!"
            else:
                session['attempts'] -= 1
                session['wrong_letters'].append(letter)
                session['used_letters'].append(letter)
                session['message'] = f"'{letter}' is not in the word. Attempts left: {session['attempts']}."

    # Check for victory or defeat only if the game has started
    if session['selected_word']:
        if "_" not in session['hidden_word']:
            session['message'] = f"Congratulations! You guessed the word: '{session['selected_word']}'! Play again?"
        elif session['attempts'] <= 0:
            session['message'] = f"Game Over! The word was '{session['selected_word']}'. Play again?"

    return render_template(
        "index.html",
        word=" ".join(session['hidden_word']),
        attempts=session['attempts'],
        wrong_letters=", ".join(session['wrong_letters']),
        message=session['message'],
        used_letters=session['used_letters'],
        hints_remaining=session['hints_remaining']
    )
if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, g, jsonify, session
from nltk.chat.util import Chat, reflections
import random
import sqlite3

app = Flask(__name__)
chat = Chat([
    # Define your chat pairs here based on the menu options
    # Each menu option will have its own response patterns
], reflections)

# This dictionary will store the tickets
tickets = {}

# This variable will track the state of the conversation
state = 'ASKING'

MENU_OPTIONS = [
    "My computer/system/laptop is slow or lagging",
    "I can't print or printer not working",
    "I can't connect to the network or no internet",
    "My screen/monitor/display is blank or black",
    "I can't log in or login issue or forgot password",
    "I received an error message",
    "How to install software",
    "Email/Outlook/Mailbox not working",
]


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('tickets.db')
    return db


def get_troubleshooting_suggestions(issue):
    # Sample troubleshooting suggestions
    troubleshooting_dict = {
        "My computer/system/laptop is slow or lagging": [
            "Close unnecessary background applications.",
            "Check for malware or viruses using an antivirus program.",
            "Upgrade your computer's RAM for better performance.",
        ],
        # Add troubleshooting suggestions for other issues
    }
    return "\n".join(troubleshooting_dict.get(issue, ["No suggestions available."]))


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/reset")
def reset():
    session.clear()
    return "Session has been reset"


@app.route("/get")
def get_bot_response():
    global state
    user_text = request.args.get('msg')
    db = get_db()
    cursor = db.cursor()
    response_message = ""

    if state == 'ASKING' or state == 'START':
        state = 'MENU_SELECTED'
        # Present the menu options
        menu_prompt = "Please select your IT issue from the menu:\n" + "\n".join(
            [f"{i + 1}. {option}" for i, option in enumerate(MENU_OPTIONS)])
        response_message = menu_prompt
    elif state == 'MENU_SELECTED':
        try:
            selected_option = int(user_text)
            if 1 <= selected_option <= len(MENU_OPTIONS):
                selected_issue = MENU_OPTIONS[selected_option - 1]

                # Provide troubleshooting suggestions based on the selected issue
                troubleshooting_suggestions = get_troubleshooting_suggestions(selected_issue)
                response_message = f"Thank you for selecting '{selected_issue}'. Here are some troubleshooting suggestions:\n\n{troubleshooting_suggestions}\n\nDid these suggestions help resolve your issue? (yes/no)"
                state = 'FEEDBACK'
            else:
                response_message = "Invalid selection. Please choose a valid option from the menu."
        except ValueError:
            response_message = "Invalid input. Please enter the number corresponding to your selected option."
    elif state == 'FEEDBACK':
        if "yes" in user_text:
            state = 'ASKING'
            response_message = "Great! If you have any other issues, feel free to ask. You can also contact our support team for further assistance. Thank you!"
        elif "no" in user_text:
            state = 'DETAILS'
            response_message = "I'm sorry to hear that. Could you please provide more details about the issue?"
    elif state == 'DETAILS':
        # The user is providing more details about their issue
        # Generate a unique ticket number
        ticket_number = random.randint(1000, 9999)
        # Store the ticket information in the database
        cursor.execute("INSERT INTO tickets VALUES (?, ?)", (ticket_number, user_text))
        db.commit()
        # Reset the state
        state = 'ASKING'
        # Provide the ticket number to the user
        response_message = f"Your support ticket has been raised. Your ticket number is {ticket_number}. One of our support team members will reach out to you soon. Thanks for using our service."


    elif "reset" in user_text.lower():

        state = 'START'  # Reset the state to 'START' here

        response_message = "The chat has been reset. How can I assist you today? Please start a new conversation."

        print(response_message)
        # Add the welcoming message here

        response_message += "\n\nWelcome! I'm your IT Support Bot, ready to assist you. To kick off our chat, simply send a friendly 'Hi'. How can I help you today?"
    else:
        # Provide a default response for unrecognized inputs
        response_message = "I'm here to assist you. If you have a specific IT issue, please choose the appropriate option from the menu or provide more details so I can help you effectively."

    # Display the response on the chat screen
    return jsonify({"response": response_message})


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template
from flask_socketio import SocketIO
import speech_recognition as sr
import pyttsx3
import yfinance as yf
import requests
import mysql.connector
import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.tree import DecisionTreeClassifier

app = Flask(__name__)
socketio = SocketIO(app)

# SQLite Database Connection and other functions...

def connect_db():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='qwerty',
        database='rb1'
    )
    return conn

def create_tables():
    db = connect_db()
    cursor = db.cursor()
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        category VARCHAR(255),
                        amount DECIMAL(10, 2),
                        month VARCHAR(255),
                        date_logged TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                      );""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS budgets (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        category VARCHAR(255),
                        amount DECIMAL(10, 2),
                        month VARCHAR(255)
                      );""")

    db.commit()
    cursor.close()
    db.close()

def log_expense(category, amount, month):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO expenses (category, amount, month) VALUES (%s,%s,%s)",
                   (category, amount, month))
    db.commit()
    cursor.close()
    db.close()

def get_expense_report(month):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE month = %s GROUP BY category", (month,))
    expense_data = cursor.fetchall()
    cursor.close()
    db.close()
    return {category: amount for category, amount in expense_data}

def set_budget(category, amount, month):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT amount FROM budgets WHERE category = %s AND month = %s", (category, month))
    existing_budget = cursor.fetchone()

    if existing_budget:
        new_amount = float(existing_budget[0]) + float(amount)
        cursor.execute("UPDATE budgets SET amount = %s WHERE category = %s AND month = %s", (new_amount, category, month))
    else:
        cursor.execute("INSERT INTO budgets (category, amount, month) VALUES (%s,%s,%s)", (category, amount, month))

    db.commit()
    cursor.close()
    db.close()

def check_budget(month):
    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT category, amount FROM budgets WHERE month = %s", (month,))
    budget_data = cursor.fetchall()
    expenses = get_expense_report(month)
    remaining_budget = {}

    for category, budget in budget_data:
        total_expense = float(expenses.get(category, 0))
        remaining_budget[category] = float(budget) - total_expense

    cursor.close()
    db.close()
    return remaining_budget

# Text-to-Speech Conversion
def speak(text):
    socketio.emit('response', {'message': text})  # Emit the text to the frontend before speaking
    print(text)  # Print the text before speaking
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# Capturing voice input
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        socketio.emit('listening', {'status': 'start'})  # Indicate listening
        audio = r.listen(source)
        socketio.emit('listening', {'status': 'stop'})  # Stop listening

    try:
        command = r.recognize_google(audio)
        print(f"You said: {command}")
        return command
    except sr.UnknownValueError:
        speak("Sorry, I did not understand that.")
        return None
    except sr.RequestError:
        speak("Sorry, my speech service is down.")
        return None

def get_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        price = stock.history(period="1d")['Close'].iloc[-1]
        return price
    except Exception as e:
        print(e)
        return None

def get_exchange_rate(from_currency, to_currency):
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
    try:
        response = requests.get(url)
        data = response.json()
        rates = data.get('rates', {})
        rate = rates.get(to_currency)
        if rate:
            return rate
        else:
            return None  # If rate is not available
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return None

def get_crypto_price(crypto):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies=usd"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get(crypto, {}).get('usd', None)
    except Exception as e:
        print(e)
        return None
    
# Classifier for command recognition
class CommandClassifier:
    def __init__(self):
        self.vectorizer = CountVectorizer()
        self.classifier = DecisionTreeClassifier()
        self.commands = [
            ("log expense", ["log expense", "I want to log an expense", "record expense", "I spend some money", "I spent money"]),
            ("set budget", ["set budget", "I want to set a budget", "budget set"]),
            ("check budget", ["check budget", "how much budget do I have", "what's my budget"]),
            ("check exchange rate", ["check exchange rate", "what's the exchange rate"]),
            ("check stock price", ["get stock price", "check stock price", "stock price"]),
            ("check cryptocurrency price", ["get cryptocurrency price", "check crypto price", "check cryptocurrency price for me"]),
            ("exit", ["exit", "quit", "close", "stop"])
        ]
        self.train_classifier()

    def train_classifier(self):
        phrases = [phrase for _, variations in self.commands for phrase in variations]
        labels = [command for command, variations in self.commands for _ in variations]
        X = self.vectorizer.fit_transform(phrases)
        self.classifier.fit(X, labels)

    def predict(self, command):
        X_test = self.vectorizer.transform([command])
        predicted = self.classifier.predict(X_test)
        return predicted[0]

# Initialize the command classifier
command_classifier = CommandClassifier()
    
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_listening')
def handle_start_listening():
    listen()  # Start listening for commands after the greeting

@socketio.on('voice_command')
def handle_voice_command(command):
    if command is None:
        speak("Sorry, I did not understand that.")
        socketio.emit('user_command', {'command': "Sorry, I did not understand that."})  # Emit the command
        return
    
    command = command.lower()

    # Emit the user's command to the frontend
    classified_command = command_classifier.predict(command)
    socketio.emit('user_command', {'command': command})  # Emit the command

    # Initial Greeting Logic
    if 'start listening' in command:
        speak("Welcome to your personal finance assistant.")
        speak("You can say the following commands:\n"
              "Log Expense\n"
              "Set Budget\n"
              "Check Budget\n"
              "Check Exchange Rate\n"
              "Check Stock Price\n"
              "Check Cryptocurrency Price\n"
              "Exit")
        
        while True:
            command = listen()
            if command is not None:  # Only handle valid commands
                handle_voice_command(command)  # Call the command handler
            else:
                speak("Sorry, I did not understand that. Please say a command again.")
            return


    valid_months = ['january', 'february', 'march', 'april', 'may', 'june', 
                    'july', 'august', 'september', 'october', 'november', 'december']

    # Command handling loop
    while True:
        if command is None:
            speak("Sorry, I did not understand that. Please try again.")
            socketio.emit('user_command', {'command': "Sorry, I did not understand that."})  # Emit the command
            command = listen()  # Prompt for the next command
            continue

        if classified_command == "log expense":
            speak("What category? (groceries, transport, utilities, entertainment)")
            category = listen()
            socketio.emit('user_command', {'command': category})  # Emit category command
            while category is None or category.lower() not in ['groceries', 'transport', 'utilities', 'entertainment']:
                speak("Sorry, I did not understand that. Please say the category again.")
                category = listen()
                socketio.emit('user_command', {'command': category})  # Emit category command

            speak("Enter the amount.")
            amount = listen()
            socketio.emit('user_command', {'command': amount})  # Emit amount command
            while amount is None:
                speak("Sorry, I did not understand that. Please say the amount again.")
                amount = listen()
                socketio.emit('user_command', {'command': amount})  # Emit amount command

            speak("Enter the month.")
            month = listen()
            socketio.emit('user_command', {'command': month})  # Emit month command
            while month is None or month.lower() not in valid_months:
                speak("Invalid month. Please say a valid month.")
                month = listen()
                socketio.emit('user_command', {'command': month})  # Emit month command

            log_expense(category, amount, month)
            speak(f"Expense of {amount} logged in {category} for {month}.")
            break

        elif classified_command == "set budget":
            # Similar loop handling for setting budgets
            speak("What category? (groceries, transport, utilities, entertainment)")
            category = listen()
            socketio.emit('user_command', {'command': category})  # Emit month command
            while category is None or category.lower() not in ['groceries', 'transport', 'utilities', 'entertainment']:
                speak("Sorry, I did not understand that. Please say the category again.")
                category = listen()

            speak("Enter the budget amount.")
            amount = listen()
            socketio.emit('user_command', {'command': amount})  # Emit month command
            while amount is None:
                speak("Sorry, I did not understand that. Please say the amount again.")
                amount = listen()

            try:
                amount = float(amount)
            except ValueError:
                speak("Invalid amount. Please try again.")
                continue  # Restart command handling loop if invalid

            speak("Enter the month.")
            month = listen()
            socketio.emit('user_command', {'command': month})  # Emit month command
            while month is None or month.lower() not in valid_months:
                speak("Invalid month. Please say a valid month.")
                month = listen()

            set_budget(category, amount, month)
            speak(f"Budget of {amount} set for {category} in {month}.")
            break

        elif classified_command == "check budget":
            speak("Enter the month to check.")
            month = listen()
            socketio.emit('user_command', {'command': month})  # Emit month command
            if month is None or month.lower() not in valid_months:
                speak("Invalid month. Please say a valid month.")
                continue  # Re-ask the last command

            remaining_budgets = check_budget(month)
            if remaining_budgets:
                for category, remaining in remaining_budgets.items():
                    speak(f"For {category}, your remaining budget is: {remaining:.2f}.")
                break  # Exit the loop after speaking the budget
            else:
                speak(f"No budget information available for {month}.")
            break  # Exit the loop if no budget is found for the month

        elif classified_command == "check stock price":
            speak("What is the stock symbol? e.g., AAPL, META")
            symbol = listen()
            socketio.emit('user_command', {'command': symbol})  # Emit month command

            if symbol is None:
                speak("Sorry, I did not understand that. Please say the stock symbol again.")
                continue  # Re-ask the last command

            price = get_stock_price(symbol.upper())
            if price:
                speak(f"The current price of {symbol} is {price:.2f} dollars.")
                break  # Exit the loop after processing the command
        
        # Check Exchange Rate Flow
        elif classified_command == "check exchange rate":
            speak("Which currencies would you like to check? For example, say 'USD to INR'.")
            currencies = listen()

            # Check if the user provided input
            if currencies is None:
                speak("I didn't catch that. Please try again.")
                continue  # Re-prompt the user

            # Match the format 'USD to EUR' using regular expression
            match = re.match(r"(\w+)\s+to\s+(\w+)", currencies.lower())
            if match:
                from_currency = match.group(1).upper()
                to_currency = match.group(2).upper()

                # Attempt to get the exchange rate
                rate = get_exchange_rate(from_currency, to_currency)
                if rate:
                    speak(f"The exchange rate from {from_currency} to {to_currency} is {rate:.4f}.")
                    socketio.emit('user_command', {'command': currencies})  # Log user command
                    break  # Exit the loop after processing the exchange rate command
                else:
                    speak("Sorry, I couldn't retrieve the exchange rate at the moment. Please try again later.")
                    break  # Exit the loop after notifying the user
            else:
                speak("That format was incorrect. Please say something like 'USD to EUR'.")
                continue  # Re-prompt the user


        elif classified_command == "check cryptocurrency price":
            speak("What cryptocurrency do you want the price for? (e.g., bitcoin, ethereum)")
            crypto = listen()
            if crypto is None:
                speak("Sorry, I did not understand that. Please say the cryptocurrency name again.")
                continue  # Re-ask the last command

            price = get_crypto_price(crypto.lower())
            if price:
                socketio.emit('user_command', {'command': crypto})  # Emit month command
                speak(f"The current price of {crypto} is {price:.2f} USD.")
                break
            else:
                speak("Could not retrieve the cryptocurrency price.")
                break
        
        elif classified_command == "exit":
            speak("Goodbye!")
            socketio.emit('stop_listening', {'status': 'stop'})  # Emit stop event to frontend
            break

        else:
            speak("I did not understand that command. Please say the commands again.")
            command = listen()  # Prompt for the next command

if __name__ == "__main__":
    create_tables()
    socketio.run(app)

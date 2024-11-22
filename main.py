import speech_recognition as sr
import pyttsx3
import requests
import re
import yfinance as yf
import sqlite3
from budget import set_budget, check_budget
from expenses import log_expense, get_expense_report
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.tree import DecisionTreeClassifier

# Initialize text-to-speech engine
def speak(text):
    engine = pyttsx3.init()
    print(text)  # Display the text as well
    engine.say(text)
    engine.runAndWait()

# Function to capture voice input
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        speak("Listening...")
        audio = r.listen(source)

    try:
        command = r.recognize_google(audio)
        print(f"You said: {command}")  # Show what was said
        return command
    except sr.UnknownValueError:
        speak("Sorry, I did not understand that.")
        return None
    except sr.RequestError:
        speak("Sorry, my speech service is down.")
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
            ("get stock price", ["get stock price", "check stock price", "stock price"]),
            ("get cryptocurrency price", ["get cryptocurrency price", "check crypto price"]),
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

# Function to get exchange rate
def get_exchange_rate(from_currency, to_currency):
    api_key = "6ef3ec1c13a9fb1757a0abfa"
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{from_currency}"
    try:
        response = requests.get(url)
        data = response.json()
        if data and data['result'] == 'success':
            conversion_rates = data['conversion_rates']
            if to_currency in conversion_rates:
                rate = conversion_rates[to_currency]
                return rate
            else:
                print(f"Conversion rate for {to_currency} not found.")
                return None
        else:
            print(f"API request unsuccessful: {data.get('error-type', 'No error message provided')}")
            return None
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return None

# Function to get stock price
def get_stock_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        price = stock.info['currentPrice']
        print(price)
        return price
    except Exception as e:
        print(f"Error fetching stock price: {e}")
        return None

# Function to get cryptocurrency price
def get_crypto_price(crypto_id):
    api_key = 'CG-k7exUfiegEhJR6GkCkpZCTSy'
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd"
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": api_key
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if data and crypto_id in data:
            price = data[crypto_id]['usd']
            return price
        else:
            return None
    except Exception as e:
        print(f"Error fetching cryptocurrency price: {e}")
        return None

# Database connection function
def connect_db():
    conn = sqlite3.connect('finance_assistant.db')
    return conn

# Main assistant interaction
def main():
    classifier = CommandClassifier()
    speak("Welcome to your personal finance assistant.")
    speak("You can say commands like 'Log Expense', 'Set Budget', 'Check Budget', 'Check Exchange Rate', 'Get Stock Price', 'Get Cryptocurrency Price', or 'Exit'.")

    while True:
        command = listen()
        if command is None:
            continue

        command = command.lower()
        predicted_command = classifier.predict(command)

        # Debugging output
        print(f"Predicted command: {predicted_command}")  # Show what command was predicted

        # Processing based on the predicted command
        if predicted_command == "log expense":
            while True:
                speak("What category? (groceries, transport, utilities, entertainment)")
                category = listen()
                if category is None:
                    continue
                category = category.lower()

                if category not in ['groceries', 'transport', 'utilities', 'entertainment']:
                    speak("Invalid category. Please try again.")
                    continue

                while True:
                    speak("Enter the amount.")
                    amount = listen()
                    if amount is None:
                        continue
                    try:
                        amount = float(amount)
                        break
                    except ValueError:
                        speak("Invalid amount. Please try again.")

                speak("Enter the month.")
                month = listen()
                if month is None:
                    continue
                month = month.lower()

                log_expense(category, amount, month)
                speak(f"Expense of {amount} logged in {category} for {month}.")
                break

        elif predicted_command == "set budget":
            while True:
                speak("What category? (groceries, transport, utilities, entertainment)")
                category = listen()
                if category is None:
                    continue
                category = category.lower()

                if category not in ['groceries', 'transport', 'utilities', 'entertainment']:
                    speak("Invalid category. Please try again.")
                    continue

                while True:
                    speak("Enter the budget amount.")
                    amount = listen()
                    if amount is None:
                        continue
                    try:
                        amount = float(amount)
                        break
                    except ValueError:
                        speak("Invalid amount. Please try again.")

                speak("Enter the month.")
                month = listen()
                if month is None:
                    continue
                month = month.lower()

                set_budget(category, amount, month)
                speak(f"Budget of {amount} set for {category} in {month}.")
                break

        elif predicted_command == "check budget":
            while True:
                speak("Which category do you want to check? (groceries, transport, utilities, entertainment)")
                category = listen()
                if category is None:
                    continue
                category = category.lower()

                if category not in ['groceries', 'transport', 'utilities', 'entertainment']:
                    speak("Invalid category. Please try again.")
                    continue

                speak("Enter the month to check.")
                month = listen()
                if month is None:
                    continue
                month = month.lower()

                remaining_budgets = check_budget(month)
                if category in remaining_budgets:
                    remaining = remaining_budgets[category]
                    speak(f"For {category}, your remaining budget is: {remaining:.2f}.")
                else:
                    speak(f"No budget found for the category: {category} in {month}.")
                break

        elif predicted_command == "check exchange rate":
            while True:
                speak("Which currencies would you like to check? For example, say 'USD to EUR'.")
                currencies = listen()
                if currencies is None:
                    continue
                currencies = currencies.upper()
                match = re.match(r"(\w+)\s+TO\s+(\w+)", currencies)
                if match:
                    from_currency = match.group(1)
                    to_currency = match.group(2)
                    rate = get_exchange_rate(from_currency, to_currency)
                    if rate:
                        speak(f"The exchange rate from {from_currency} to {to_currency} is {rate:.4f}.")
                    else:
                        speak("Sorry, I couldn't retrieve the exchange rate.")
                else:
                    speak("Invalid format. Please say currencies in the format 'USD to EUR'.")
                break

        elif predicted_command == "get stock price":
            while True:
                speak("Which stock symbol would you like to check?")
                symbol = listen()
                if symbol is None:
                    continue

                symbol = symbol.upper()
                price = get_stock_price(symbol)

                if price is not None:
                    speak(f"The current price of {symbol} is {price:.2f}.")
                    break
                else:
                    speak(f"Sorry, I couldn't retrieve the price for {symbol}. Please try again.")

        elif predicted_command == "get cryptocurrency price":
            while True:
                speak("Which cryptocurrency would you like to check? For example, say Bitcoin.")
                symbol = listen()
                if symbol is None:
                    continue
                symbol = symbol.lower()
                price = get_crypto_price(symbol)
                if price:
                    speak(f"The current price of {symbol} is ${price:.2f}.")
                    break
                else:
                    speak(f"Sorry, I couldn't retrieve the price for {symbol}. Please try again.")

        elif predicted_command == "exit":
            speak("Thank you for using your personal finance assistant. Goodbye!")
            break
        else:
            speak("Sorry, I didn't understand that command. Can you try again?")

if __name__ == "__main__":
    main()

import speech_recognition as sr
import pyttsx3
import requests
import re
import yfinance as yf
import sqlite3
from budget import set_budget, check_budget
from expenses import log_expense, get_expense_report

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
    speak("Welcome to your personal finance assistant.")
    speak("You can say the following commands:\n"
          " Log Expense\n"
          " Set Budget\n"
          " Check Budget\n"
          " Check Exchange Rate\n"
          " Get Stock Price\n"
          " Get Cryptocurrency Price\n"
          " Exit")

    while True:
        command = listen()
        if command is None:
            continue
        
        command = command.lower()
        
        # Logging Expense
        if "log expense" in command:
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
        
        # Setting Budget
        elif "set budget" in command:
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
        
        # Checking Budget
        elif "check budget" in command:
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
        
        # Checking Exchange Rate
        elif "check exchange rate" in command:
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
        
        # Getting Stock Price
        elif "get stock price" in command:
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
        
        # Getting Cryptocurrency Price
        elif "get cryptocurrency price" in command:
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
        
        # Exit Command
        elif "exit" in command:
            speak("Thank you for using your personal finance assistant. Goodbye!")
            break
        
        # Unrecognized Command
        else:
            speak("Sorry, I didn't understand that command.")


if __name__ == "__main__":
    main()

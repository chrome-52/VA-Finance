import mysql.connector
from database import connect_db
from expenses import get_expense_report

# Function to set or update the budget
def set_budget(category, amount, month):
    db = connect_db()
    cursor = db.cursor()

    # Check if a budget already exists for the given category and month
    cursor.execute("SELECT amount FROM budgets WHERE category = %s AND month = %s", 
                   (category, month))
    existing_budget = cursor.fetchone()

    if existing_budget:
        # Convert the existing budget amount from Decimal to float and add the new amount
        new_amount = float(existing_budget[0]) + float(amount)
        cursor.execute("UPDATE budgets SET amount = %s WHERE category = %s AND month = %s", 
                       (new_amount, category, month))
    else:
        # If no budget exists, insert a new record
        cursor.execute("INSERT INTO budgets (category, amount, month) VALUES (%s, %s, %s)", 
                       (category, amount, month))

    db.commit()
    cursor.close()
    db.close()

# Function to check remaining budget
def check_budget(month):
    db = connect_db()
    cursor = db.cursor()

    # Get all budgets for the specified month
    cursor.execute("SELECT category, amount FROM budgets WHERE month = %s", (month,))
    budget_data = cursor.fetchall()

    # Get logged expenses for the specified month
    expenses = get_expense_report(month)

    # Calculate remaining budget for each category
    remaining_budget = {}
    for category, budget in budget_data:
        total_expense = float(expenses.get(category, 0))  # Convert expense to float
        remaining_budget[category] = float(budget) - total_expense  # Convert budget to float and subtract

    cursor.close()
    db.close()

    return remaining_budget
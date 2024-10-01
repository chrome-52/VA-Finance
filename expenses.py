import mysql.connector
from database import connect_db

def log_expense(category, amount, month):
    db = connect_db()
    cursor = db.cursor()
    
    cursor.execute("INSERT INTO expenses (category, amount, month) VALUES (%s, %s, %s)", 
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

import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="qwerty",
        database="VA"
    )

def create_tables():
    db = connect_db()
    cursor = db.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        category VARCHAR(50),
        amount DECIMAL(10, 2),
        month VARCHAR(20),
        date_logged TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        category VARCHAR(50),
        amount DECIMAL(10, 2),
        month VARCHAR(20)
    );
    """)
    
    db.commit()
    cursor.close()
    db.close()

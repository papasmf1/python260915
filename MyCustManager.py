import sqlite3

class CustomerManager:
    """SQLite3 기반 고객 정보 CRUD 처리 클래스"""

    def __init__(self, db_path="MyCust.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Customers (
                custID INTEGER PRIMARY KEY AUTOINCREMENT,
                custName TEXT NOT NULL,
                custTitle TEXT
            )
        """)
        self.conn.commit()

    def add_customer(self, custName, custTitle):
        self.cursor.execute(
            "INSERT INTO Customers (custName, custTitle) VALUES (?, ?)",
            (custName, custTitle)
        )
        self.conn.commit()

    def update_customer(self, custID, custName, custTitle):
        self.cursor.execute(
            "UPDATE Customers SET custName = ?, custTitle = ? WHERE custID = ?",
            (custName, custTitle, custID)
        )
        self.conn.commit()

    def delete_customer(self, custID):
        self.cursor.execute("DELETE FROM Customers WHERE custID = ?", (custID,))
        self.conn.commit()

    def search_customer(self, keyword):
        self.cursor.execute(
            "SELECT * FROM Customers WHERE custName LIKE ?",
            (f"%{keyword}%",)
        )
        return self.cursor.fetchall()

    def get_all_customers(self):
        self.cursor.execute("SELECT * FROM Customers")
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

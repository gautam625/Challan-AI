import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "cars.db")


def create_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cars (
        car_number TEXT PRIMARY KEY,
        owner_name TEXT,
        age INTEGER,
        location TEXT,
        mobile TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS challans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        car_number TEXT,
        amount INTEGER,
        reason TEXT,
        date TEXT,
        status TEXT
    )''')
    conn.commit()
    conn.close()


def insert_data(car_number, owner_name, age, location, mobile):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO cars VALUES (?, ?, ?, ?, ?)",
              (car_number, owner_name, age, location, mobile))
    conn.commit()
    conn.close()


def get_owner(car_number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM cars WHERE car_number=?", (car_number,))
    data = c.fetchone()
    conn.close()
    return data


def get_all_vehical():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM cars")
    data = c.fetchall()
    conn.close()
    return data


def insert_challan(car_number, amount, reason, date, status="Pending"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO challans (car_number, amount, reason, date, status) VALUES (?, ?, ?, ?, ?)",
              (car_number, amount, reason, date, status))
    conn.commit()
    conn.close()


def get_all_challans():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM challans")
    data = c.fetchall()
    conn.close()
    return data


def get_pending_challans(car_number):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT amount FROM challans WHERE car_number=? AND status='Pending'", (car_number,))
    data = c.fetchall()
    conn.close()
    return data

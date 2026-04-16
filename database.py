import sqlite3
import os
from functools import lru_cache

DB_PATH = os.environ.get("DB_PATH", "cars.db")


def _conn():
    """Return a thread-safe connection with WAL mode for faster writes."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    with _conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS cars (
                car_number TEXT PRIMARY KEY,
                owner_name TEXT NOT NULL,
                age        INTEGER,
                location   TEXT,
                mobile     TEXT
            );
            CREATE TABLE IF NOT EXISTS challans (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                car_number TEXT NOT NULL,
                amount     INTEGER NOT NULL,
                reason     TEXT NOT NULL,
                date       TEXT NOT NULL,
                status     TEXT NOT NULL DEFAULT 'Pending'
            );
            CREATE INDEX IF NOT EXISTS idx_challans_car ON challans(car_number);
            CREATE INDEX IF NOT EXISTS idx_challans_status ON challans(status);
        """)


def upsert_vehicle(car_number, owner_name, age, location, mobile):
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cars VALUES (?,?,?,?,?)",
            (car_number.upper(), owner_name, age, location, mobile)
        )
    get_owner.cache_clear()


@lru_cache(maxsize=256)
def get_owner(car_number: str):
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM cars WHERE car_number=?", (car_number,)
        ).fetchone()
    return tuple(row) if row else None


def get_all_vehicles():
    with _conn() as conn:
        return conn.execute("SELECT * FROM cars ORDER BY car_number").fetchall()


def insert_challan(car_number, amount, reason, date, status="Pending"):
    with _conn() as conn:
        conn.execute(
            "INSERT INTO challans (car_number,amount,reason,date,status) VALUES (?,?,?,?,?)",
            (car_number, amount, reason, date, status)
        )


def get_all_challans():
    with _conn() as conn:
        return conn.execute("SELECT * FROM challans ORDER BY id DESC").fetchall()


def get_pending_amount(car_number: str) -> int:
    with _conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM challans WHERE car_number=? AND status='Pending'",
            (car_number,)
        ).fetchone()
    return row[0] if row else 0


def get_dashboard_stats():
    with _conn() as conn:
        total, total_amt, pending = conn.execute("""
            SELECT COUNT(*),
                   COALESCE(SUM(amount),0),
                   SUM(CASE WHEN status='Pending' THEN 1 ELSE 0 END)
            FROM challans
        """).fetchone()
    return int(total or 0), int(total_amt or 0), int(pending or 0)


def seed_default_data():
    with _conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM cars").fetchone()[0]
        if count == 0:
            default_cars = [
                ("MH12AB3456", "Ravi Kumar", 30, "Hyderabad", "9004420925"),
                ("MH20DV2366", "Anjali Sharma", 28, "Mumbai", "9004420925"),
                ("MH02DH2964", "Rahul Singh", 35, "Ranchi", "9004420925"),
                ("MH13AZ9456", "Priya kumari", 26, "Pune", "9004420925"),
                ("MP09CU0092", "Rohit Singh", 40, "Goa", "9004420925"),
            ]

            conn.executemany("""INSERT INTO cars (car_number, owner_name, age, location, mobile) VALUES (?,?,?,?,?)""", default_cars)

            #
            default_challans = [
                ("TS09AB1234", 500, "Wrong Parking", "2026-04-01", "Pending"),
                ("TS08CD5678", 1000, "Over-speeding", "2026-04-02", "Pending"),
                ("TS07EF9012", 500, "Signal Jumping", "2026-04-03", "Paid"),
                ("TS06GH3456", 1000, "Without License", "2026-04-04", "Pending"),
                ("TS05IJ7890", 2000, "Drunken Driving", "2026-04-05", "Paid"),
            ]

            conn.executemany("""INSERT INTO challans (car_number, amount, reason, date, status) VALUES (?,?,?,?,?)""", default_challans)

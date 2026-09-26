import os
import sqlite3
import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import ai_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")
BUDGET_CATEGORIES = ["Food", "Transport", "Rent", "Utilities", "Entertainment", "Savings"]


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"pbkdf2_sha256$100000${salt}${digest.hex()}"


def verify_password(password: str, stored_password: str) -> bool:
    if not stored_password:
        return False
    if stored_password.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, stored_hash = stored_password.split("$", 3)
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations),
            ).hex()
            return hmac.compare_digest(digest, stored_hash)
        except (ValueError, TypeError):
            return False
    return hmac.compare_digest(stored_password, password)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            age TEXT,
            salary TEXT,
            city TEXT,
            living_type TEXT,
            family_size TEXT,
            transport_mode TEXT,
            additional_info TEXT,
            onboarding_completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS manual_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute("PRAGMA table_info(manual_expenses)")
    manual_expense_cols = {row[1] for row in cursor.fetchall()}
    if "description" not in manual_expense_cols:
        cursor.execute("ALTER TABLE manual_expenses ADD COLUMN description TEXT DEFAULT ''")

    conn.commit()
    conn.close()


init_db()


class Question(BaseModel):
    question: str


class UserSignup(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserProfileUpdate(BaseModel):
    email: str
    name: Optional[str] = None
    age: Optional[str] = None
    salary: Optional[str] = None
    city: Optional[str] = None
    living_type: Optional[str] = None
    family_size: Optional[str] = None
    transport_mode: Optional[str] = None
    additional_info: Optional[str] = None
    onboarding_completed: Optional[bool] = None


class ManualExpense(BaseModel):
    user_email: str
    category: str
    amount: float
    description: Optional[str] = ""


def parse_salary(raw_value) -> int:
    try:
        salary = int(float(raw_value or 0))
        return salary if salary > 0 else 100000
    except (TypeError, ValueError):
        return 100000


def calculate_budget(user_row) -> Dict[str, int]:
    salary = parse_salary(user_row["salary"] if user_row else 0)
    city = (user_row["city"] if user_row else "") or "Other"
    living_type = (user_row["living_type"] if user_row else "") or "Family Home"
    family_size = (user_row["family_size"] if user_row else "") or "Single"
    transport_mode = (user_row["transport_mode"] if user_row else "") or "Public Transport"
    additional_info = (user_row["additional_info"] if user_row else "") or ""

    # Base percentages (Everyone has their own budget basis)
    base_food = 0.20
    base_transport = 0.08
    base_rent = 0.25 if living_type == "Rented House" else (0.12 if living_type == "Hostel" else 0.0)
    base_utilities = 0.10
    base_entertainment = 0.07

    # Dynamic adjustments based on profile/scenarios
    family_factor = {
        "Single": 1.0,
        "Small Family": 1.4,
        "Large Family": 2.0,
    }.get(family_size, 1.0)

    # Scenario Logic: Multi-Asset Parsing (e.g., "3 cars and 1 motorbike")
    import re
    car_count = 0
    bike_count = 0
    
    # 1. Car Detection
    car_match = re.search(r'(\d+|one|two|three|four|five)\s*(?:car|vehicle)', additional_info, re.I)
    if car_match:
        val = car_match.group(1).lower()
        num_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
        car_count = num_map.get(val, int(val) if val.isdigit() else 1)
    elif "car" in additional_info.lower(): car_count = 1

    # 2. Motorbike Detection
    bike_match = re.search(r'(\d+|one|two|three|four|five)\s*(?:bike|motorcycle|motorbike)', additional_info, re.I)
    if bike_match:
        val = bike_match.group(1).lower()
        num_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
        bike_count = num_map.get(val, int(val) if val.isdigit() else 1)
    elif any(x in additional_info.lower() for x in ["bike", "motorcycle", "motorbike"]): bike_count = 1

    # Logic: If assets found, calculate cumulative transport costs
    if car_count > 0 or bike_count > 0:
        base_transport = (car_count * 0.12) + (bike_count * 0.05)
    else:
        # Defaults based on primary mode if no assets specified
        base_transport = {"Car": 0.12, "Bike": 0.07, "Public Transport": 0.05}.get(transport_mode, 0.08)
    
    # Cap transport to 40% of salary to maintain budget balance
    base_transport = min(base_transport, 0.40)
    
    # Ensure category budgets don't exceed 85% before savings
    total_pct = base_food * family_factor + base_transport + base_rent + base_utilities + base_entertainment
    scaling_factor = 0.85 / total_pct if total_pct > 0.85 else 1.0

    budgets = {
        "Food": round(salary * base_food * family_factor * scaling_factor),
        "Transport": round(salary * base_transport * scaling_factor),
        "Rent": round(salary * base_rent * scaling_factor),
        "Utilities": round(salary * base_utilities * scaling_factor),
        "Entertainment": round(salary * base_entertainment * scaling_factor),
    }

    # Zero-based budgeting: Remaining salary goes to Savings
    allocated_sum = sum(budgets.values())
    budgets["Savings"] = max(salary - allocated_sum, 0)

    return budgets


def get_monthly_manual_expenses(email: str) -> Dict[str, int]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT category, COALESCE(SUM(amount), 0) AS total
        FROM manual_expenses
        WHERE lower(user_email) = lower(?)
          AND strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
        GROUP BY category
        """,
        (email,),
    )
    rows = cursor.fetchall()
    conn.close()

    expenses = {category: 0 for category in BUDGET_CATEGORIES}
    for row in rows:
        if row["category"] in expenses:
            expenses[row["category"]] = int(row["total"] or 0)
    return expenses


def get_recent_manual_expenses(email: str, limit: int = 8):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, category, amount, COALESCE(description, '') AS description, timestamp
        FROM manual_expenses
        WHERE lower(user_email) = lower(?)
        ORDER BY datetime(timestamp) DESC, id DESC
        LIMIT ?
        """,
        (email, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def build_dashboard_summary(email: str) -> Dict[str, Dict[str, int]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    budget = calculate_budget(user)
    spent = get_monthly_manual_expenses(email)
    salary = parse_salary(user["salary"] if user else 0)

    # --- UNIQUE AI FEATURE: FINANCIAL ZEN SCORE ---
    total_budget = sum(budget.values()) # Should equal salary
    total_spent = sum(spent.values())
    
    if total_budget > 0:
        score = 100 - (min(total_spent / total_budget, 1.2) * 80) 
        overspent_count = sum(1 for cat in BUDGET_CATEGORIES if spent.get(cat, 0) > budget.get(cat, 0))
        score -= (overspent_count * 5)
        health_score = max(int(score), 0)
    else:
        health_score = 0

    remaining_by_cat = {key: budget[key] - spent.get(key, 0) for key in BUDGET_CATEGORIES}
    percentage = {
        key: round((spent.get(key, 0) / budget[key]) * 100) if budget.get(key, 0) > 0 else 0
        for key in BUDGET_CATEGORIES
    }

    return {
        "user": {
            "name": user["name"],
            "email": user["email"],
            "age": user["age"],
            "salary": salary,
            "city": user["city"] or "",
            "living_type": user["living_type"] or "",
            "family_size": user["family_size"] or "",
            "transport_mode": user["transport_mode"] or "",
            "additional_info": user["additional_info"] or "",
        },
        "budget": budget,
        "spent": spent,
        "remaining": remaining_by_cat,
        "percentage": percentage,
        "health_score": health_score,
        "totals": {
            "budget": salary,
            "spent": total_spent,
            "remaining": salary - total_spent - (total_budget - budget.get("Savings", 0)), # Correct logic: Surplus - Total Spent
        },
    }


@app.get('/')
def index():
    return "Smart AI Expenses Tracker Backend"


@app.post("/signup")
def signup(user: UserSignup):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (user.name, user.email.strip().lower(), hash_password(user.password))
        )
        conn.commit()
        return {"message": "User created successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already exists")
    finally:
        conn.close()


@app.post("/login")
def login(user: UserLogin):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE lower(email) = lower(?)",
        (user.email.strip().lower(),)
    )
    row = cursor.fetchone()

    if row and verify_password(user.password, row["password"]):
        if not str(row["password"]).startswith("pbkdf2_sha256$"):
            cursor.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (hash_password(user.password), row["id"]),
            )
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE id = ?", (row["id"],))
            row = cursor.fetchone()
        user_data = dict(row)
        if "additional_info" not in user_data:
            user_data["additional_info"] = ""
        conn.close()
        return {"message": "Login successful", "user": user_data}

    conn.close()
    raise HTTPException(status_code=401, detail="Invalid email or password")


@app.post("/update-profile")
def update_profile(profile: UserProfileUpdate):
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []
    fields = [
        ("name", profile.name),
        ("age", profile.age),
        ("salary", profile.salary),
        ("city", profile.city),
        ("living_type", profile.living_type),
        ("family_size", profile.family_size),
        ("transport_mode", profile.transport_mode),
        ("additional_info", profile.additional_info),
        ("onboarding_completed", profile.onboarding_completed)
    ]

    for field, value in fields:
        if value is not None:
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        conn.close()
        return {"message": "No fields to update"}

    params.append(profile.email.strip().lower())
    query = f"UPDATE users SET {', '.join(updates)} WHERE lower(email) = lower(?)"
    cursor.execute(query, tuple(params))
    conn.commit()
    conn.close()
    return {"message": "Profile updated successfully"}


@app.post("/add-expense")
def add_expense(expense: ManualExpense):
    email = expense.user_email.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO manual_expenses (user_email, category, amount, description) VALUES (?, ?, ?, ?)",
        (email, expense.category, expense.amount, expense.description or "")
    )
    conn.commit()

    cursor.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    budget_data = calculate_budget(user)
    category_budget = int(budget_data.get(expense.category, 0))

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM manual_expenses
        WHERE lower(user_email) = lower(?)
          AND category = ?
          AND strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
        """,
        (email, expense.category),
    )
    row = cursor.fetchone()
    total_spent = int(row["total"] or 0)
    remaining = category_budget - total_spent
    over_amount = abs(remaining) if remaining < 0 else 0

    cursor.execute(
        """
        SELECT category, COALESCE(description, '') AS description, amount, timestamp
        FROM manual_expenses
        WHERE lower(user_email) = lower(?)
          AND category = ?
          AND strftime('%Y-%m', timestamp) = strftime('%Y-%m', 'now')
        ORDER BY datetime(timestamp) DESC, id DESC
        LIMIT 5
        """,
        (email, expense.category),
    )
    recent_rows = cursor.fetchall()
    conn.close()

    recent_same_category = [
        {
            "description": (r["description"] or "No description").strip() or "No description",
            "amount": int(r["amount"] or 0),
            "timestamp": r["timestamp"],
        }
        for r in recent_rows
    ]

    return {
        "message": "Expense added successfully",
        "category": expense.category,
        "budget": category_budget,
        "spent": total_spent,
        "remaining": remaining,
        "over_budget": remaining < 0,
        "over_amount": over_amount,
        "recent_same_category": recent_same_category,
    }


@app.get("/manual-expenses")
def get_manual_expenses(email: str):
    return get_monthly_manual_expenses(email)


@app.get("/expenses")
def get_expenses(email: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE lower(email) = lower(?)", (email.strip().lower(),))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return calculate_budget(user)


@app.get("/dashboard-summary")
def dashboard_summary(email: str):
    return build_dashboard_summary(email)


@app.get("/recent-expenses")
def recent_expenses(email: str, limit: int = 8):
    return {"expenses": get_recent_manual_expenses(email, limit)}


@app.get("/monthly-history")
def get_monthly_history(email: str):
    conn = get_connection()
    cursor = conn.cursor()
    # Get last 6 months of data
    cursor.execute(
        """
        SELECT strftime('%Y-%m', timestamp, 'localtime') AS month, SUM(amount) AS total
        FROM manual_expenses
        WHERE lower(user_email) = lower(?)
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
        """,
        (email,),
    )
    rows = cursor.fetchall()
    
    # Analysis logic
    history = [dict(row) for row in rows]
    current_month = datetime.now().strftime('%Y-%m')
    
    current_total = 0
    prev_totals = []
    
    for h in history:
        if h["month"] == current_month:
            current_total = h["total"]
        else:
            prev_totals.append(h["total"])
            
    avg_prev = sum(prev_totals) / len(prev_totals) if prev_totals else 0
    
    status = "On Track"
    if avg_prev > 0:
        if current_total > avg_prev * 1.1:
            status = "Spending Higher than Usual"
        elif current_total < avg_prev * 0.9:
            status = "Excellent - Saving More!"
            
    # AI Insight
    question = f"My current month spending is {current_total} PKR. My previous months average was {avg_prev} PKR. Status: {status}. Give one short line of encouragement or correction for a user in Pakistan."
    ai_insight = ai_agent(question)
    
    conn.close()
    return {
        "history": history,
        "analysis": {
            "status": status,
            "avg_prev": round(avg_prev),
            "current": current_total,
            "ai_insight": ai_insight
        }
    }


@app.post("/ask-ai")
def ask_ai(data: Question):
    answer = ai_agent(data.question)
    return {"answer": answer}

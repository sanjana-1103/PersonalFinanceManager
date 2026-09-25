from flask import Flask, render_template, request, redirect, send_file, session
import sqlite3
from datetime import datetime
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph


app = Flask(__name__)

app.secret_key = "finance_manager_secret_key"

# -----------------------------
# Database Connection
# -----------------------------
import os

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), "finance.db")
    print("Using database:", db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# Home
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            session["user_id"] = user["id"]

            return redirect("/dashboard")
        else:
            return "<h2>Invalid Email or Password</h2><a href='/login'>Try Again</a>"

    return render_template("login.html")


# -----------------------------
# Register
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users(name,email,password) VALUES(?,?,?)",
            (name, email, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# -----------------------------
# Dashboard
# -----------------------------
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Total Income
    cursor.execute(
        "SELECT SUM(amount) FROM income WHERE user_id=?",
        (user_id,)
    )

    total_income = cursor.fetchone()[0]

    if total_income is None:
        total_income = 0

    # Total Expense
    cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id=?",
        (user_id,)
    )

    total_expense = cursor.fetchone()[0]

    if total_expense is None:
        total_expense = 0

    # Balance
    balance = total_income - total_expense

    conn.close()

    return render_template(
        "dashboard.html",
        total_income=total_income,
        total_expense=total_expense,
        balance=balance
    )

# -----------------------------
# Add Expense
# -----------------------------
@app.route("/expense", methods=["GET", "POST"])
def expense():

    if request.method == "POST":

        amount = request.form["amount"]
        category = request.form["category"]
        note = request.form["note"]

        date = datetime.now().strftime("%d-%m-%Y %H:%M")

        conn = get_db_connection()
        cursor = conn.cursor()

        user_id = session["user_id"]

        cursor.execute(
            """
            INSERT INTO expenses(user_id, amount, category, note, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, amount, category, note, date)
        )

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("expense.html")


# -----------------------------
# Add Income
# -----------------------------
@app.route("/income", methods=["GET", "POST"])
def income():

    if request.method == "POST":

        try:
            amount = request.form["amount"]
            source = request.form["source"]
            note = request.form["note"]

            date = datetime.now().strftime("%d-%m-%Y %H:%M")

            conn = get_db_connection()
            cursor = conn.cursor()

            user_id = session["user_id"]

            cursor.execute(
                """
                INSERT INTO income(user_id, amount, source, note, date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, amount, source, note, date)
            )

            conn.commit()
            conn.close()

            print("Income saved successfully!")

            return redirect("/dashboard")

        except Exception as e:
            return f"<h2>Error:</h2><pre>{e}</pre>"

    return render_template("income.html")

# -----------------------------
# Transaction History
# -----------------------------
@app.route("/history")
def history():

    search = request.args.get("search", "")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    if search:

        cursor.execute(
            """
            SELECT id, amount, category AS type_name, note, date,
            'Expense' AS transaction_type
            FROM expenses
            WHERE user_id=? AND (category LIKE ? OR note LIKE ?)

            UNION ALL

            SELECT id, amount, source AS type_name, note, date,
            'Income' AS transaction_type
            FROM income
            WHERE user_id=? AND (source LIKE ? OR note LIKE ?)

            ORDER BY date DESC
            """,
            (
                user_id,
                f"%{search}%",
                f"%{search}%",
                user_id,
                f"%{search}%",
                f"%{search}%"
            )
        )

    else:

        cursor.execute(
            """
            SELECT id, amount, category AS type_name, note, date,
            'Expense' AS transaction_type
            FROM expenses
            WHERE user_id=?

            UNION ALL

            SELECT id, amount, source AS type_name, note, date,
            'Income' AS transaction_type
            FROM income
            WHERE user_id=?

            ORDER BY date DESC
            """,
            (
                user_id,
                user_id
            )
        )

    transactions = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        transactions=transactions,
        search=search
    )


# -----------------------------
# Delete Transaction
# -----------------------------
@app.route("/delete/<transaction_type>/<int:id>")
def delete(transaction_type, id):

    conn = get_db_connection()
    cursor = conn.cursor()

    if transaction_type == "Expense":
        cursor.execute(
            "DELETE FROM expenses WHERE id=?",
            (id,)
        )
    else:
        cursor.execute(
            "DELETE FROM income WHERE id=?",
            (id,)
        )

    conn.commit()
    conn.close()

    return redirect("/history")

# -----------------------------
# Edit Expense
# -----------------------------
@app.route("/edit/expense/<int:id>", methods=["GET", "POST"])
def edit_expense(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        amount = request.form["amount"]
        category = request.form["category"]
        note = request.form["note"]
        

        cursor.execute(
            """
            UPDATE expenses
            SET amount=?, category=?, note=?
            WHERE id=?
            """,
            (amount, category, note, id)
        )

        conn.commit()
        conn.close()

        return redirect("/history")

    cursor.execute(
        "SELECT * FROM expenses WHERE id=?",
        (id,)
    )

    expense = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_expense.html",
        expense=expense
    )


# -----------------------------
# Edit Income
# -----------------------------
@app.route("/edit/income/<int:id>", methods=["GET", "POST"])
def edit_income(id):

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        amount = request.form["amount"]
        source = request.form["source"]
        note = request.form["note"]

        cursor.execute(
            """
            UPDATE income
            SET amount=?, source=?, note=?
            WHERE id=?
            """,
            (amount, source, note, id)
        )

        conn.commit()
        conn.close()

        return redirect("/history")

    cursor.execute(
        "SELECT * FROM income WHERE id=?",
        (id,)
    )

    income = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_income.html",
        income=income
    )


# -----------------------------
# Reports
# -----------------------------
@app.route("/reports")
def reports():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Total Income
    cursor.execute(
        "SELECT SUM(amount) FROM income WHERE user_id=?",
        (user_id,)
    )
    total_income = cursor.fetchone()[0] or 0

    # Total Expense
    cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id=?",
        (user_id,)
    )
    total_expense = cursor.fetchone()[0] or 0

    # Balance
    balance = total_income - total_expense

    # Total Transactions
    cursor.execute(
        "SELECT COUNT(*) FROM income WHERE user_id=?",
        (user_id,)
    )
    income_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id=?",
        (user_id,)
    )
    expense_count = cursor.fetchone()[0]

    total_transactions = income_count + expense_count

    # Today's Income
    today = datetime.now().strftime("%d-%m-%Y")

    cursor.execute(
        "SELECT SUM(amount) FROM income WHERE user_id=? AND date LIKE ?",
        (user_id, today + "%")
    )
    today_income = cursor.fetchone()[0] or 0

    # Today's Expense
    cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id=? AND date LIKE ?",
        (user_id, today + "%")
    )
    today_expense = cursor.fetchone()[0] or 0

    # Expense Category Chart
    cursor.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY category
    """, (user_id,))

    expense_rows = cursor.fetchall()

    categories = []
    category_amounts = []

    for row in expense_rows:
        categories.append(row[0])
        category_amounts.append(row[1])

    # Monthly Income
    cursor.execute("""
        SELECT substr(date,4,7), SUM(amount)
        FROM income
        WHERE user_id=?
        GROUP BY substr(date,4,7)
    """, (user_id,))
    income_rows = cursor.fetchall()

    # Monthly Expense
    cursor.execute("""
        SELECT substr(date,4,7), SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY substr(date,4,7)
    """, (user_id,))
    expense_rows = cursor.fetchall()

    income_dict = {}
    expense_dict = {}

    for row in income_rows:
        income_dict[row[0]] = row[1]

    for row in expense_rows:
        expense_dict[row[0]] = row[1]

    months = sorted(set(income_dict.keys()) | set(expense_dict.keys()))

    monthly_income = []
    monthly_expense = []

    for month in months:
        monthly_income.append(income_dict.get(month, 0))
        monthly_expense.append(expense_dict.get(month, 0))

    conn.close()

    return render_template(
        "reports.html",
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        total_transactions=total_transactions,
        today_income=today_income,
        today_expense=today_expense,
        categories=categories,
        category_amounts=category_amounts,
        months=months,
        monthly_income=monthly_income,
        monthly_expense=monthly_expense
    )
# -----------------------------
# Budget
# -----------------------------
@app.route("/budget", methods=["GET", "POST"])
def budget():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        monthly_budget = request.form["monthly_budget"]

        # Check if budget already exists for this user
        cursor.execute(
            "SELECT id FROM budget WHERE user_id=?",
            (user_id,)
        )

        row = cursor.fetchone()

        if row:

            cursor.execute(
                """
                UPDATE budget
                SET monthly_budget=?
                WHERE user_id=?
                """,
                (monthly_budget, user_id)
            )

        else:

            cursor.execute(
                """
                INSERT INTO budget(user_id, monthly_budget)
                VALUES(?, ?)
                """,
                (user_id, monthly_budget)
            )

        conn.commit()

        return redirect("/budget")

    # Current Budget
    cursor.execute(
        "SELECT monthly_budget FROM budget WHERE user_id=? LIMIT 1",
        (user_id,)
    )

    row = cursor.fetchone()

    if row:
        budget = row["monthly_budget"]
    else:
        budget = 0

    # Total Expenses
    cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id=?",
        (user_id,)
    )

    total_expense = cursor.fetchone()[0] or 0

    remaining = budget - total_expense

    if budget > 0:
        percentage = (total_expense / budget) * 100
        if percentage > 100:
            percentage = 100
    else:
        percentage = 0

    # Monthly Income
    cursor.execute("""
        SELECT substr(date,4,7) AS month,
               SUM(amount)
        FROM income
        WHERE user_id=?
        GROUP BY month
        ORDER BY month
    """, (user_id,))

    income_rows = cursor.fetchall()

    # Monthly Expense
    cursor.execute("""
        SELECT substr(date,4,7) AS month,
               SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY month
        ORDER BY month
    """, (user_id,))

    expense_rows = cursor.fetchall()

    income_dict = {row[0]: row[1] for row in income_rows}
    expense_dict = {row[0]: row[1] for row in expense_rows}

    months = sorted(set(income_dict.keys()) | set(expense_dict.keys()))

    monthly_income = []
    monthly_expense = []

    for month in months:
        monthly_income.append(income_dict.get(month, 0))
        monthly_expense.append(expense_dict.get(month, 0))

    conn.close()

    return render_template(
        "budget.html",
        budget=budget,
        total_expense=total_expense,
        remaining=remaining,
        percentage=percentage,
        months=months,
        monthly_income=monthly_income,
        monthly_expense=monthly_expense
    )

# -----------------------------
# Expense Calendar
# -----------------------------
@app.route("/calendar")
def calendar():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    selected_date = request.args.get("date")

    if selected_date:

        search_date = datetime.strptime(
            selected_date,
            "%Y-%m-%d"
        ).strftime("%d-%m-%Y")

        cursor.execute(
            """
            SELECT *
            FROM expenses
            WHERE user_id=? AND date LIKE ?
            ORDER BY date DESC
            """,
            (user_id, search_date + "%")
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM expenses
            WHERE user_id=?
            ORDER BY date DESC
            """,
            (user_id,)
        )

    expenses = cursor.fetchall()

    conn.close()

    return render_template(
        "calendar.html",
        expenses=expenses,
        selected_date=selected_date
    )
# -----------------------------
# Export Transactions to Excel
# -----------------------------
@app.route("/export_excel")
def export_excel():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT date, category, amount, note
        FROM expenses
        WHERE user_id=?
        ORDER BY date DESC
        """,
        (user_id,)
    )

    expenses = cursor.fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "Expenses"

    ws.append(["Date", "Category", "Amount", "Note"])

    for expense in expenses:
        ws.append([
            expense["date"],
            expense["category"],
            expense["amount"],
            expense["note"]
        ])

    filename = "Expense_Report.xlsx"

    wb.save(filename)

    conn.close()

    return send_file(
        filename,
        as_attachment=True
    )
# -----------------------------
# Export Transactions to PDF
# -----------------------------
@app.route("/export_pdf")
def export_pdf():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT date, category, amount, note
        FROM expenses
        WHERE user_id=?
        ORDER BY date DESC
        """,
        (user_id,)
    )

    expenses = cursor.fetchall()

    pdf_file = "Expense_Report.pdf"

    doc = SimpleDocTemplate(pdf_file)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph("<b>Personal Finance Report</b>", styles["Title"])
    )

    data = [
        ["Date", "Category", "Amount", "Note"]
    ]

    for expense in expenses:

        data.append([
            expense["date"],
            expense["category"],
            f"₹{expense['amount']}",
            expense["note"]
        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),

    ]))

    elements.append(table)

    doc.build(elements)

    conn.close()

    return send_file(
        pdf_file,
        as_attachment=True
    )

# -----------------------------
# Savings Goal
# -----------------------------
@app.route("/savings", methods=["GET", "POST"])
def savings():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        goal_amount = request.form["goal_amount"]

        # Check if the user already has a savings goal
        cursor.execute(
            "SELECT id FROM savings WHERE user_id=?",
            (user_id,)
        )

        row = cursor.fetchone()

        if row:

            cursor.execute(
                """
                UPDATE savings
                SET goal_amount=?
                WHERE user_id=?
                """,
                (goal_amount, user_id)
            )

        else:

            cursor.execute(
                """
                INSERT INTO savings(user_id, goal_amount)
                VALUES(?, ?)
                """,
                (user_id, goal_amount)
            )

        conn.commit()

        return redirect("/savings")

    # Get User Goal
    cursor.execute(
        "SELECT goal_amount FROM savings WHERE user_id=? LIMIT 1",
        (user_id,)
    )

    row = cursor.fetchone()

    if row:
        goal = row["goal_amount"]
    else:
        goal = 0

    # Total Income
    cursor.execute(
        "SELECT SUM(amount) FROM income WHERE user_id=?",
        (user_id,)
    )

    total_income = cursor.fetchone()[0] or 0

    # Total Expense
    cursor.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id=?",
        (user_id,)
    )

    total_expense = cursor.fetchone()[0] or 0

    # Current Savings
    current_savings = total_income - total_expense

    remaining = goal - current_savings

    if remaining < 0:
        remaining = 0

    if goal > 0:
        percentage = (current_savings / goal) * 100
        if percentage > 100:
            percentage = 100
    else:
        percentage = 0

    conn.close()

    return render_template(
        "savings.html",
        goal=goal,
        current_savings=current_savings,
        remaining=remaining,
        percentage=percentage
    )
# -----------------------------
# Bill Reminder
# -----------------------------
@app.route("/reminders", methods=["GET", "POST"])
def reminders():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":

        bill_name = request.form["bill_name"]
        amount = request.form["amount"]
        due_date = request.form["due_date"]

        cursor.execute(
            """
            INSERT INTO reminders(user_id, bill_name, amount, due_date)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, bill_name, amount, due_date)
        )

        conn.commit()

        return redirect("/reminders")

    cursor.execute(
        """
        SELECT *
        FROM reminders
        WHERE user_id=?
        ORDER BY due_date
        """,
        (user_id,)
    )

    reminders = cursor.fetchall()

    conn.close()

    return render_template(
        "reminders.html",
        reminders=reminders
    )
# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")
# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)
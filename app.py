import csv
import io
from flask import Response
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

DB_PATH = Path(__file__).with_name("expenses.db")


def get_db_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@app.route("/reports")
def reports():
    selected_month = request.args.get("month", "").strip()

    if selected_month:
        try:
            datetime.strptime(selected_month, "%Y-%m")
        except ValueError:
            return "Invalid month format.", 400

    with get_db_connection() as connection:
        available_months = connection.execute("""
            SELECT DISTINCT substr(transaction_date, 1, 7) AS month
            FROM transactions
            ORDER BY month DESC
        """).fetchall()

        if selected_month:
            category_rows = connection.execute("""
                SELECT category, SUM(amount) AS total
                FROM transactions
                WHERE transaction_type = 'expense'
                  AND substr(transaction_date, 1, 7) = ?
                GROUP BY category
                ORDER BY total DESC
            """, (selected_month,)).fetchall()

            totals = connection.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN transaction_type = 'income'
                        THEN amount ELSE 0 END), 0) AS income,
                    COALESCE(SUM(CASE WHEN transaction_type = 'expense'
                        THEN amount ELSE 0 END), 0) AS expenses
                FROM transactions
                WHERE substr(transaction_date, 1, 7) = ?
            """, (selected_month,)).fetchone()
        else:
            category_rows = connection.execute("""
                SELECT category, SUM(amount) AS total
                FROM transactions
                WHERE transaction_type = 'expense'
                GROUP BY category
                ORDER BY total DESC
            """).fetchall()

            totals = connection.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN transaction_type = 'income'
                        THEN amount ELSE 0 END), 0) AS income,
                    COALESCE(SUM(CASE WHEN transaction_type = 'expense'
                        THEN amount ELSE 0 END), 0) AS expenses
                FROM transactions
            """).fetchone()

        monthly_rows = connection.execute("""
            SELECT substr(transaction_date, 1, 7) AS month,
                   SUM(CASE WHEN transaction_type = 'income'
                       THEN amount ELSE 0 END) AS income,
                   SUM(CASE WHEN transaction_type = 'expense'
                       THEN amount ELSE 0 END) AS expenses
            FROM transactions
            GROUP BY substr(transaction_date, 1, 7)
            ORDER BY month
        """).fetchall()

    categories = [row["category"] for row in category_rows]
    category_totals = [row["total"] for row in category_rows]

    plt.figure(figsize=(7, 4))
    if categories:
        plt.bar(categories, category_totals)
        plt.title("Expenses by Category")
        plt.ylabel("Amount (₹)")
        plt.xticks(rotation=25, ha="right")
    else:
        plt.text(0.5, 0.5, "No expense data for this period",
                 ha="center", va="center")
        plt.axis("off")
    plt.tight_layout()
    plt.savefig(Path(app.static_folder) / "category_chart.png")
    plt.close()

    months = [row["month"] for row in monthly_rows]
    incomes = [row["income"] for row in monthly_rows]
    expenses = [row["expenses"] for row in monthly_rows]

    plt.figure(figsize=(7, 4))
    if months:
        positions = list(range(len(months)))
        width = 0.35
        plt.bar([p - width / 2 for p in positions],
                incomes, width, label="Income")
        plt.bar([p + width / 2 for p in positions],
                expenses, width, label="Expenses")
        plt.xticks(positions, months, rotation=25)
        plt.legend()
        plt.title("Monthly Income vs Expenses")
        plt.ylabel("Amount (₹)")
    else:
        plt.text(0.5, 0.5, "No transaction data yet", ha="center")
        plt.axis("off")
    plt.tight_layout()
    plt.savefig(Path(app.static_folder) / "monthly_chart.png")
    plt.close()

    return render_template(
        "reports.html",
        selected_month=selected_month,
        available_months=available_months,
        category_rows=category_rows,
        income=totals["income"],
        expenses=totals["expenses"],
        balance=totals["income"] - totals["expenses"]
    )


@app.route("/export")
def export_csv():
    
    selected_month = request.args.get("month", "").strip()

    if selected_month:
        try:
            datetime.strptime(selected_month, "%Y-%m")
        except ValueError:
            return "Invalid month format.", 400

    with get_db_connection() as connection:
        if selected_month:
            rows = connection.execute("""
                SELECT title, amount, transaction_type, category,
                       transaction_date
                FROM transactions
                WHERE substr(transaction_date, 1, 7) = ?
                ORDER BY transaction_date DESC, id DESC
            """, (selected_month,)).fetchall()
        else:
            rows = connection.execute("""
                SELECT title, amount, transaction_type, category,
                       transaction_date
                FROM transactions
                ORDER BY transaction_date DESC, id DESC
            """).fetchall()


    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Description", "Amount", "Type", "Category", "Date"
    ])

    for row in rows:
        writer.writerow([
            row["title"], row["amount"], row["transaction_type"],
            row["category"], row["transaction_date"]
        ])

    return Response(
        "\ufeff" + output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                "attachment; filename=expense_transactions.csv"
        }
    )


def initialize_database():
    with get_db_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                transaction_type TEXT NOT NULL
                    CHECK (transaction_type IN ('income', 'expense')),
                category TEXT NOT NULL,
                transaction_date TEXT NOT NULL
            )
        """)



@app.route("/")
def home():
    search = request.args.get("search", "").strip()
    transaction_type = request.args.get("type", "").strip()
    category = request.args.get("category", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    if transaction_type in ("income", "expense"):
        query += " AND transaction_type = ?"
        params.append(transaction_type)

    if category:
        query += " AND category = ?"
        params.append(category)

    if start_date:
        query += " AND transaction_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND transaction_date <= ?"
        params.append(end_date)

    query += " ORDER BY transaction_date DESC, id DESC"

    with get_db_connection() as connection:
        transactions = connection.execute(query, params).fetchall()

        totals = connection.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN transaction_type = 'income'
                    THEN amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN transaction_type = 'expense'
                    THEN amount ELSE 0 END), 0) AS expenses
            FROM transactions
        """).fetchone()

        categories = connection.execute("""
            SELECT DISTINCT category FROM transactions ORDER BY category
        """).fetchall()

    return render_template(
        "index.html",
        transactions=transactions,
        income=totals["income"],
        expenses=totals["expenses"],
        balance=totals["income"] - totals["expenses"],
        categories=categories,
        search=search,
        selected_type=transaction_type,
        
        selected_category=category,
        start_date=start_date,
        end_date=end_date,
        today=datetime.today().strftime("%d %b %Y")

    )



@app.route("/add", methods=["POST"])
def add_transaction():
    title = request.form.get("title", "").strip()
    amount_text = request.form.get("amount", "").strip()
    transaction_type = request.form.get("transaction_type", "")
    category = request.form.get("category", "").strip()
    transaction_date = request.form.get("transaction_date", "")

    if not all([title, amount_text, transaction_type, category, transaction_date]):
        return "Please fill in every field.", 400

    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return "Amount must be a number greater than zero.", 400

    if transaction_type not in ("income", "expense"):
        return "Invalid transaction type.", 400

    with get_db_connection() as connection:
        connection.execute("""
            INSERT INTO transactions
                (title, amount, transaction_type, category, transaction_date)
            VALUES (?, ?, ?, ?, ?)
        """, (title, amount, transaction_type, category, transaction_date))

    return redirect("/")

@app.route("/edit/<int:transaction_id>", methods=["GET", "POST"])
def edit_transaction(transaction_id):
    with get_db_connection() as connection:
        transaction = connection.execute(
            "SELECT * FROM transactions WHERE id = ?",
            (transaction_id,)
        ).fetchone()

        if transaction is None:
            return "Transaction not found.", 404

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            category = request.form.get("category", "").strip()
            transaction_type = request.form.get("transaction_type", "")
            transaction_date = request.form.get("transaction_date", "")

            try:
                amount = float(request.form.get("amount", ""))
                if amount <= 0:
                    raise ValueError
            except ValueError:
                return "Amount must be greater than zero.", 400

            if not all([title, category, transaction_date]):
                return "Please fill in every field.", 400

            if transaction_type not in ("income", "expense"):
                return "Invalid transaction type.", 400

            connection.execute("""
                UPDATE transactions
                SET title = ?, amount = ?, transaction_type = ?,
                    category = ?, transaction_date = ?
                WHERE id = ?
            """, (
                title, amount, transaction_type, category,
                transaction_date, transaction_id
            ))

            return redirect(url_for("home"))

    return render_template("edit.html", transaction=transaction)


@app.route("/delete/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):
    with get_db_connection() as connection:
        connection.execute(
            "DELETE FROM transactions WHERE id = ?",
            (transaction_id,)
        )

    return redirect(url_for("home"))



initialize_database()

if __name__ == "__main__":
    app.run(debug=True)

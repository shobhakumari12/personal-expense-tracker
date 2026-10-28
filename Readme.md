
# 💰 Personal Expense Tracker

A web-based personal finance application built with Flask and SQLite to help users track income, manage expenses, and understand their spending through reports and charts.

## ✨ Features

- **Dashboard:** View total income, total expenses, and current balance.
- **Transaction Management:** Add, edit, and delete transactions.
- **Search and Filters:** Filter transactions by description, type, category, and date range.
- **Reports and Charts:** Visualize expenses by category and compare monthly income with expenses.
- **CSV Export:** Export transaction records for further analysis.
- **Database Storage:** Store transactions using SQLite.
- **Responsive Interface:** Use the application on desktop and smaller screens.

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, Jinja2
- **Database:** SQLite
- **Data Visualization:** Matplotlib
- **Data Export:** CSV

## 📁 Project Structure

```text
personal-expense-tracker/
├── app.py
├── requirements.txt
├── .gitignore
├── static/
│   ├── style.css
│   ├── category_chart.png
│   └── monthly_chart.png
└── templates/
    ├── index.html
    ├── edit.html
    └── reports.html
```

## 🚀 Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/shobhakumari12/personal-expense-tracker.git
cd personal-expense-tracker
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the application

```bash
python app.py
```

Open your browser at:

http://127.0.0.1:5000

## 🗄️ Database

The application uses SQLite to store transaction records. The database is created locally by the application when it initializes.

The local database file is excluded from Git to avoid publishing personal financial information.

## 🔮 Future Improvements

- Monthly budgets and spending limits
- Pagination for transaction history
- Improved dashboard visualizations
- User authentication and individual accounts
- Production deployment with persistent data storage

## 👩‍💻 Author

**Shobha Kumari**

GitHub: [@shobhakumari12](https://github.com/shobhakumari12)

---

If you find this project useful, feel free to explore the code and suggest improvements.

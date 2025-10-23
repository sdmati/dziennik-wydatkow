from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def generateCategories():
    conn = get_db_connection()
    categories = conn.execute('''SELECT id, name FROM categories''').fetchall()
    categories.append(categories.pop(0))

    return categories

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = get_db_connection()

    # wprowadzanie danych

    if request.method == 'POST':
        name = request.form['name']
        category = int(request.form['category'])
        amount = request.form['amount']
        comment = request.form['comment']
        comment = None if comment == '' else comment
        date = request.form.get('date').strip()
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        privExpense = 1 if request.form.get('privExpense') else 0

        conn.execute('''
                     INSERT INTO expenses (name, category, amount, comment, privExpense, date)
                     VALUES (?, ?, ?, ?, ?, ?)
                     ''', (name, category, amount, comment, privExpense, date))
        conn.commit()
        return redirect('/')
    
    # generowanie danych do tabelki

    expenses = conn.execute('''SELECT e.id, e.name, c.name AS category, e.amount, e.comment, e.privExpense, e.date FROM expenses e 
                                JOIN categories c ON e.category = c.id
                                ORDER BY e.id ASC LIMIT 10''').fetchall()

    # generowanie danych do wykresu

    chartData = conn.execute('''SELECT amount, date FROM expenses WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now') ORDER BY date''').fetchall()

    conn.close()

    labels = [row["date"] for row in chartData]
    values = [row["amount"] for row in chartData]

    return render_template('index.html', expenses = expenses, labels = labels, values = values)

@app.route('/add', methods=['GET', 'POST'])
def add():
    conn = get_db_connection()

    # generowanie kategorii do listy

    categories = generateCategories()

    # wprowadzanie danych

    if request.method == 'POST':
        name = request.form['name']
        category = int(request.form['category'])
        amount = request.form['amount']
        comment = request.form['comment']
        comment = None if comment == '' else comment
        date = request.form.get('date').strip()
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        privExpense = 1 if request.form.get('privExpense') else 0

        conn.execute('''
                     INSERT INTO expenses (name, category, amount, comment, privExpense, date)
                     VALUES (?, ?, ?, ?, ?, ?)
                     ''', (name, category, amount, comment, privExpense, date))
        conn.commit()
        return redirect('/')

    return render_template('add.html', categories = categories)

@app.route('/stats', methods=['GET', 'POST'])
def stats():
    conn = get_db_connection()
    categories = generateCategories()

    if request.method == 'POST':
        firstDate = request.form.get('firstDate').strip()
        secondDate = request.form.get('secondDate').strip()

        if firstDate > secondDate:
            firstDate, secondDate = secondDate, firstDate

        chartData = conn.execute('''SELECT amount, date FROM expenses 
                                    WHERE date BETWEEN ? AND ? ORDER BY date''',(firstDate, secondDate)).fetchall()

        expenses = conn.execute('''SELECT e.id, e.name, c.name AS category, e.amount, e.comment, e.privExpense, e.date FROM expenses e JOIN categories c ON e.category = c.id
                                   WHERE e.date BETWEEN ? AND ? 
                                   ORDER BY e.date ASC LIMIT 10''', (firstDate, secondDate)).fetchall()

        conn.close()

        labels = [row["date"] for row in chartData]
        values = [row["amount"] for row in chartData]

        return render_template('stats.html', labels=labels, values=values, expenses = expenses, categories=categories)

    chartData = conn.execute('''SELECT amount, date FROM expenses
                                ORDER BY date''').fetchall()

    expenses = conn.execute('''SELECT e.id, e.name, c.name AS category, e.amount, e.comment, e.privExpense, e.date
                               FROM expenses e
                                JOIN categories c ON e.category = c.id
                               ORDER BY e.date DESC LIMIT 10''').fetchall()

    conn.close()

    labels = [row["date"] for row in chartData]
    values = [row["amount"] for row in chartData]

    return render_template('stats.html', labels=labels, values=values, expenses = expenses, categories = categories)

@app.route('/report', methods=['GET', 'POST'])
def report():
    conn = get_db_connection()
    return render_template('report.html')

if __name__ == '__main__':
    app.run(debug=True)
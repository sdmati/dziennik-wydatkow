from time import strftime

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

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db_connection()
    categories = generateCategories()
    data = conn.execute('''SELECT e.name, e.id, e.amount, e.category, e.comment, e.privExpense, e.date FROM expenses e WHERE e.id = ?''', (id,)).fetchone()


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

        conn.execute('''UPDATE expenses SET name = ?, category = ?, amount = ?, comment = ?, privExpense = ?, date = ? WHERE id = ?''', (name, category, amount, comment, privExpense, date, id))
        conn.commit()
        data = conn.execute('''SELECT e.name, e.id, e.amount, e.category, e.comment, e.privExpense, e.date
                               FROM expenses e
                               WHERE e.id = ?''', (id,)).fetchone()
        conn.close()
        return render_template('edit.html', categories = categories, data = data)


    return render_template('edit.html', categories = categories, data = data)

@app.route('/stats', methods=['GET', 'POST'])
def stats():
    conn = get_db_connection()
    categories = generateCategories()

    if request.method == 'POST':
        firstDate = request.form.get('firstDate').strip()
        secondDate = request.form.get('secondDate').strip()
        category = request.form.get('category').strip()

        if firstDate == '' or secondDate == '':
            if category == 'every':
                chartQuery = '''SELECT amount, date FROM expenses ORDER BY date ASC'''
                tableQuery = '''SELECT e.id, e.name, c.name AS category, e.amount, e.comment, e.privExpense, e.date FROM expenses e JOIN categories c ON e.category = c.id
                                ORDER BY e.date ASC LIMIT 10'''
                parameters = ()
            else:
                chartQuery = '''SELECT amount, date FROM expenses e JOIN categories c ON e.category = c.id
                           WHERE c.id = ? ORDER BY e.date ASC'''
                tableQuery = '''SELECT e.id, e.name, c.name AS category, e.amount, e.comment, e.privExpense, e.date FROM expenses e JOIN categories c ON e.category = c.id
                             WHERE c.id = ? ORDER BY e.date ASC '''
                parameters = (category,)

        else:
            if firstDate > secondDate:
                firstDate, secondDate = secondDate, firstDate
            if category == 'every':
                chartQuery = '''SELECT e.amount, e.date FROM expenses e
                           WHERE e.date BETWEEN ? AND ? ORDER BY e.date ASC'''
                tableQuery = '''SELECT e.id, e.name, c.name AS category, e.amount, e.comment, e.privExpense, e.date FROM expenses e JOIN categories c ON e.category = c.id
                             WHERE e.date BETWEEN ? AND ? ORDER BY e.date ASC '''
                parameters = (firstDate, secondDate)

            else:
                chartQuery = '''SELECT e.amount, e.date FROM expenses e JOIN categories c ON e.category = c.id
                           WHERE e.date BETWEEN ? AND ? AND c.id = ? ORDER BY e.date ASC'''
                tableQuery = '''SELECT e.id, e.name, c.name AS category, e.amount, e.comment, e.privExpense, e.date FROM expenses e JOIN categories c ON e.category = c.id
                             WHERE e.date BETWEEN ? AND ? AND c.id = ? ORDER BY e.date ASC '''
                parameters = (firstDate, secondDate, category)

        chartData = conn.execute(chartQuery, parameters).fetchall()
        expenses = conn.execute(tableQuery, parameters).fetchall()

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
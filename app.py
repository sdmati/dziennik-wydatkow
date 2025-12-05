from time import strftime
from urllib.parse import uses_relative

from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import io
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
import pandas as pd

app = Flask(__name__)
app.secret_key = "1234"


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def generateCategories():
    conn = get_db_connection()
    categories = conn.execute('''SELECT id, name FROM categories''').fetchall()
    categories.append(categories.pop(0))

    return categories

def userName():
    if 'uid' not in session:
        return "Nie zalogowano"
    conn = get_db_connection()
    name = conn.execute('''SELECT username FROM users WHERE id = ?''', (session['uid'],)).fetchone()
    conn.close()
    if name is None:
        return "Nie zalogowano"
    return name[0]

@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = get_db_connection()
    users = conn.execute('''SELECT id, username FROM users WHERE id != 0''').fetchall()

    if request.method == 'POST':
        uid = request.form.get('user')
        session['uid'] = uid
        return redirect('/')
    return render_template('login.html', users=users, user=userName())

@app.route('/manageUsers', methods=['GET', 'POST'])
def manageUsers():
    if 'uid' not in session:
        return redirect('/login')
    conn = get_db_connection()
    users = conn.execute('''SELECT id, username FROM users WHERE id != 0''').fetchall()
    if request.method == 'POST':
        newUser = request.form['newUser']
        conn.execute('''INSERT INTO users (username) VALUES (?)''', (newUser,))
        conn.commit()

    accounts = conn.execute('''SELECT id, username FROM users WHERE id != 0''').fetchall()
    conn.close()

    return render_template('manageUsers.html', users=users, user=userName(), accounts=accounts)

@app.route('/editUser/<int:id>', methods=['GET', 'POST'])
def editUser(id):
    if 'uid' not in session:
        return redirect('/login')
    conn = get_db_connection()
    account = conn.execute('''SELECT id, username FROM users WHERE id = ? ''', (id,)).fetchone()
    if request.method == 'POST':
        action = request.form['action']
        if action == "Potwierdź zmiane":
            conn.execute('''UPDATE users SET username = ? WHERE id = ?''', (request.form['username'], id) )
            conn.commit()
        elif action == "Usuń tego użytkownika":
            conn.execute('''DELETE FROM users WHERE id = ?''', (id,))
            conn.execute('''UPDATE expenses SET uid = 0 WHERE uid = ?''', (id,))
            conn.commit()
            if id == int(session.get('uid')):
                session.clear()
                conn.close()
                return redirect('/login')

        return redirect('/manageUsers')

    conn.close()

    return render_template('editUser.html', account=account, user=userName())
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'uid' not in session:
        return redirect('/login')
    conn = get_db_connection()
    currentMonth = datetime.now().strftime('%m-%Y')
    # generowanie danych do wykresu

    chartData = conn.execute('''SELECT amount, date FROM expenses WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now') ORDER BY date''').fetchall()
    labels = [row["date"] for row in chartData]
    values = [row["amount"] for row in chartData]
    monthBudget = conn.execute('''SELECT value FROM budget WHERE month = strftime('%Y-%m', 'now')''').fetchone()
    spentMoney = conn.execute('''SELECT sum(amount) AS spent FROM expenses WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')''').fetchone()
    highest = conn.execute('''SELECT name, amount FROM expenses WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now') ORDER BY amount DESC LIMIT 1''').fetchone()
    privPercentage = conn.execute('''SELECT (SUM(CASE WHEN privExpense = 1 THEN amount ELSE 0 END) * 100.0) / SUM(amount) as privPercentage FROM expenses WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')''').fetchone()
    perUser = conn.execute('''SELECT u.username, SUM(e.amount) as totalSpent FROM expenses e LEFT JOIN users u ON e.uid = u.id WHERE strftime('%Y-%m', e.date) = strftime('%Y-%m', 'now') GROUP BY u.username ORDER BY totalSpent DESC LIMIT 5''').fetchall()
    transactions = conn.execute('''SELECT COUNT(*) as value FROM expenses WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')''').fetchone()

    conn.close()

    percent = round((spentMoney[0] / monthBudget[0]) * 100, 2)
    today = datetime.today()
    daysMonth = calendar.monthrange(today.year, today.month)[1]
    daysPassed = today.day
    daysLeft = daysMonth - daysPassed
    privPercent = round((privPercentage[0] / 100) * 100, 2)

    return render_template('index.html', labels = labels, values = values, user=userName(), monthBudget = monthBudget, currentMonth=currentMonth, spentMoney = spentMoney, percent=percent, today=today, daysMonth=daysMonth, daysPassed=daysPassed, daysLeft=daysLeft, highest=highest, privPercent=privPercent, transactions=transactions, perUser=perUser)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'uid' not in session:
        return redirect('/login')
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
                     INSERT INTO expenses (name, category, amount, comment, privExpense, date, uid)
                     VALUES (?, ?, ?, ?, ?, ?, ?)
                     ''', (name, category, amount, comment, privExpense, date, session['uid']))
        conn.commit()
        return redirect('/')

    return render_template('add.html', categories = categories, user=userName())

@app.route('/budget', methods=['GET', 'POST'])
def budget():
    if 'uid' not in session:
        return redirect('/login')
    conn = get_db_connection()
    currentMonth = datetime.now().strftime('%Y-%m')
    lastMonth = datetime.now() - relativedelta(months=1)

    if request.method == 'POST':
        value = float(request.form['value'])
        month = request.form['month']
        conn.execute('''INSERT OR REPLACE INTO budget(month, value) VALUES (?, ?)''', (month, value))
        conn.commit()
        conn.close()
        # return render_template('budget.html', user=userName(), currentMonth=currentMonth, lastMonth=lastMonth)
        return redirect('/budget')

    chart = conn.execute('''SELECT month, value FROM budget ORDER BY month DESC LIMIT 12''').fetchall()
    conn.close()

    return render_template('budget.html', user=userName(), currentMonth=currentMonth, lastMonth=lastMonth, chart=chart)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'uid' not in session:
        return redirect('/login')
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
        return render_template('edit.html', categories = categories, data = data, user=userName())


    return render_template('edit.html', categories = categories, data = data, user=userName())

@app.route('/stats', methods=['GET', 'POST'])
def stats():
    if 'uid' not in session:
        return redirect('/login')
    conn = get_db_connection()
    categories = generateCategories()

    if request.method == 'POST':
        firstDate = request.form.get('firstDate').strip()
        secondDate = request.form.get('secondDate').strip()
        category = request.form.get('category').strip()

        if firstDate == '' or secondDate == '':
            if category == 'every':
                chartQuery = '''SELECT amount, date FROM expenses ORDER BY date ASC'''
                tableQuery = '''SELECT e.id, e.name, c.name AS category, e.amount, e.comment, e.privExpense, e.date, u.username FROM expenses e JOIN categories c ON e.category = c.id JOIN users u ON e.uid = u.id
                                ORDER BY e.date ASC'''
                parameters = ()
            else:
                chartQuery = '''SELECT amount, date FROM expenses e JOIN categories c ON e.category = c.id
                           WHERE c.id = ? ORDER BY e.date ASC'''
                tableQuery = '''SELECT e.id, e.name, c.name AS category, e.amount, e.comment, e.privExpense, e.date, u.username  FROM expenses e JOIN categories c ON e.category = c.id JOIN users u ON e.uid = u.id
                             WHERE c.id = ? ORDER BY e.date ASC '''
                parameters = (category,)

        else:
            if firstDate > secondDate:
                firstDate, secondDate = secondDate, firstDate
            if category == 'every':
                chartQuery = '''SELECT e.amount, e.date FROM expenses e
                           WHERE e.date BETWEEN ? AND ? ORDER BY e.date ASC'''
                tableQuery = '''SELECT e.id, e.name, c.name AS category, e.amount, e.comment, e.privExpense, e.date, u.username  FROM expenses e JOIN categories c ON e.category = c.id JOIN users u ON e.uid = u.id
                             WHERE e.date BETWEEN ? AND ? ORDER BY e.date ASC '''
                parameters = (firstDate, secondDate)

            else:
                chartQuery = '''SELECT e.amount, e.date FROM expenses e JOIN categories c ON e.category = c.id
                           WHERE e.date BETWEEN ? AND ? AND c.id = ? ORDER BY e.date ASC'''
                tableQuery = '''SELECT e.id, e.name, c.name AS category, e.amount, e.comment, e.privExpense, e.date, u.username  FROM expenses e JOIN categories c ON e.category = c.id JOIN users u ON e.uid = u.id
                             WHERE e.date BETWEEN ? AND ? AND c.id = ? ORDER BY e.date ASC '''
                parameters = (firstDate, secondDate, category)

        chartData = conn.execute(chartQuery, parameters).fetchall()
        expenses = conn.execute(tableQuery, parameters).fetchall()

        conn.close()

        labels = [row["date"] for row in chartData]
        values = [row["amount"] for row in chartData]

        return render_template('stats.html', labels=labels, values=values, expenses = expenses, categories=categories, user=userName())

    chartData = conn.execute('''SELECT amount, date FROM expenses
                                ORDER BY date''').fetchall()

    expenses = conn.execute('''SELECT e.id, e.name, c.name AS category, e.amount, e.comment, e.privExpense, e.date, u.username
                               FROM expenses e
                                JOIN categories c ON e.category = c.id  JOIN users u ON e.uid = u.id
                               ORDER BY e.date DESC''').fetchall()

    conn.close()

    labels = [row["date"] for row in chartData]
    values = [row["amount"] for row in chartData]

    return render_template('stats.html', labels=labels, values=values, expenses = expenses, categories = categories, user=userName())

@app.route('/report', methods=['GET', 'POST'])
def report():
    if 'uid' not in session:
        return redirect('/login')
    conn = get_db_connection()
    categories = generateCategories()

    if request.method == 'POST':
        firstDate = request.form.get('firstDate').strip()
        secondDate = request.form.get('secondDate').strip()
        category = request.form.get('category').strip()

        if firstDate == '' or secondDate == '':
            if category == 'every':
                tableQuery = '''SELECT e.id, \
                                       e.name, \
                                       c.name AS category, \
                                       e.amount, \
                                       e.comment, \
                                       e.privExpense, \
                                       e.date, \
                                       u.username \
                                FROM expenses e \
                                         JOIN categories c ON e.category = c.id \
                                         JOIN users u ON e.uid = u.id
                                ORDER BY e.date ASC'''
                parameters = ()
            else:
                tableQuery = '''SELECT e.id, \
                                       e.name, \
                                       c.name AS category, \
                                       e.amount, \
                                       e.comment, \
                                       e.privExpense, \
                                       e.date, \
                                       u.username \
                                FROM expenses e \
                                         JOIN categories c ON e.category = c.id \
                                         JOIN users u ON e.uid = u.id
                                WHERE c.id = ? \
                                ORDER BY e.date ASC '''
                parameters = (category,)

        else:
            if firstDate > secondDate:
                firstDate, secondDate = secondDate, firstDate
            if category == 'every':
                tableQuery = '''SELECT e.id, \
                                       e.name, \
                                       c.name AS category, \
                                       e.amount, \
                                       e.comment, \
                                       e.privExpense, \
                                       e.date, \
                                       u.username \
                                FROM expenses e \
                                         JOIN categories c ON e.category = c.id \
                                         JOIN users u ON e.uid = u.id
                                WHERE e.date BETWEEN ? AND ? \
                                ORDER BY e.date ASC '''
                parameters = (firstDate, secondDate)

            else:
                tableQuery = '''SELECT e.id, \
                                       e.name, \
                                       c.name AS category, \
                                       e.amount, \
                                       e.comment, \
                                       e.privExpense, \
                                       e.date, \
                                       u.username \
                                FROM expenses e \
                                         JOIN categories c ON e.category = c.id \
                                         JOIN users u ON e.uid = u.id
                                WHERE e.date BETWEEN ? AND ? \
                                  AND c.id = ? \
                                ORDER BY e.date ASC '''
                parameters = (firstDate, secondDate, category)

        expenses = conn.execute(tableQuery, parameters).fetchall()
        data = [dict(expense) for expense in expenses]
        df = pd.DataFrame(data)
        conn.close()
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="raport.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    return render_template('report.html', user=userName())

if __name__ == '__main__':
    app.run(debug=True)
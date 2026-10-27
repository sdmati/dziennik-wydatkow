# 💰 Dziennik Wydatków (Expense Tracker)

Webowa aplikacja do zarządzania budżetem domowym oraz śledzenia codziennych wydatków wielu użytkowników, stworzona w oparciu o **Python (Flask)** oraz bazę danych **SQLite**.

## 🚀 Główne funkcjonalności

- **Zarządzanie wydatkami (CRUD)**: dodawanie, edycja i usuwanie wydatków z podziałem na kategorie, daty, komentarze oraz oznaczeniem wydatków prywatnych/wspólnych.
- **Obsługa wielu użytkowników**: przełączanie aktywnego profilu użytkownika oraz zarządzanie listą domowników.
- **Planowanie budżetu miesięcznego**: ustalanie budżetu na bieżący miesiąc, podgląd stopnia wykorzystania budżetu (%), średnich dziennych wydatków oraz kwoty pozostałej na każdy dzień do końca miesiąca.
- **Statystyki i wykresy**: analiza wydatków według kategorii, użytkowników, miesięcy oraz zestawienie TOP 5 największych wydatków.
- **Generowanie raportów Excel (`.xlsx`)**: filtrowanie transakcji po zakresie dat, kategoriach, kwotach oraz bezpośredni eksport zestawienia do arkusza kalkulacyjnego przy użyciu `pandas` i `openpyxl`.

## 🛠️ Technologie

- **Backend**: Python 3, Flask
- **Baza danych**: SQLite3
- **Analiza i eksport danych**: Pandas, Openpyxl, python-dateutil
- **Frontend**: HTML5, CSS3, szablony Jinja2, Chart.js

## 📦 Instalacja i uruchomienie

1. Sklonuj repozytorium:
   ```bash
   git clone https://github.com/sdmati/dziennik-wydatkow.git
   cd dziennik-wydatkow
   ```

2. Utwórz i aktywuj środowisko wirtualne:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Zainstaluj wymagane pakiety:
   ```bash
   pip install -r requirements.txt
   ```

4. Uruchom aplikację:
   ```bash
   python3 app.py
   ```
   Aplikacja będzie dostępna pod adresem `http://127.0.0.1:5000`.

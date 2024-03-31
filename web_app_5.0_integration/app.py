from flask import Flask, redirect, url_for, render_template, flash, session, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators, FloatField, DateField
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_wtf.csrf import CSRFProtect,validate_csrf
from wtforms.validators import ValidationError
from datetime import datetime
from werkzeug.utils import secure_filename
import sqlite3
import subprocess
import json

app = Flask(__name__)
csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = 'your_secret_key'

# Set the path to the database file
database_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'users.db')
# Configure the SQLAlchemy URI to use the SQLite database file
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_path
# Override the database if it already exists
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    expenses = db.relationship('Expense', backref='user', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def update(self, item, amount, category, date):
        self.item = item
        self.amount = amount
        self.category = category
        self.date = date
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Failed to update expense:", e)
            raise

    def delete(self):
        db.session.delete(self)
        db.session.commit()

class ExpenseForm(FlaskForm):
    item = StringField('Item', [validators.DataRequired()])
    amount = FloatField('Amount', [validators.DataRequired()])
    category = StringField('Category', [validators.DataRequired()])
    date = DateField('Date', [validators.DataRequired()])
    submit = SubmitField('Add Expense')

# Define index route and redirect to login
@app.route('/')
def index():
    return redirect(url_for('login'))

class LoginForm(FlaskForm):
    username = StringField('Username', [validators.DataRequired()])
    password = PasswordField('Password', [validators.DataRequired()])
    submit = SubmitField('Log In')

class SignupForm(FlaskForm):
    username = StringField('Username', [validators.DataRequired()])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password')
    submit = SubmitField('Sign Up')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Query database for user
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            # User authenticated, store user ID in session
            session['user_id'] = user.id
            # User authenticated, redirect to homepage
            flash('Login successful!', 'success')
            return redirect(url_for('expense_tracker'))   # Replace 'homepage' with the name of your homepage route
        else:
            # Invalid username or password
            flash('Invalid username or password', 'error')

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!', 'error')
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create new user account
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Sign up successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)

@app.route('/expense_tracker', methods=['GET', 'POST'])
def expense_tracker():
    user_id = session.get('user_id')
    print("User ID from session:", user_id)  # Debugging output
    if user_id is None:
        flash('User not logged in!', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    print("User:", user)  # Debugging output
    if user is None:
        flash('User not found!', 'error')
        print('here')
        return redirect(url_for('login'))

    form = ExpenseForm()
    if form.validate_on_submit():
        item = form.item.data
        amount = form.amount.data
        category = form.category.data
        date = form.date.data

        print("Form data:", item, amount, category, date)  # Debugging output

        # Create new expense
        new_expense = Expense(item=item, amount=amount, category=category, date=date, user_id=user.id)
        print("New Expense User ID:", new_expense.user_id)  # Debugging output
        try:
            db.session.add(new_expense)
            db.session.commit()
            flash('Expense added successfully!', 'success')
            print("Expense added to database:", new_expense)  # Add this line for debugging
            return redirect(url_for('all_expenses'))  # Redirect to the expenses page
        except Exception as e:
            flash(f'Failed to add expense: {str(e)}', 'error')
            print(f'Failed to add expense: {str(e)}')
            print("New Expense Added:", new_expense)  # Print the new expense
            return redirect(url_for('expense_tracker'))
    else:
        print("Form validation errors:", form.errors)  # Debugging output

    expenses = user.expenses  # Fetch all expenses for the user

    # Calculate current year and month
    current_year = datetime.now().year
    current_month = datetime.now().month

    print("User expenses:", expenses)  # Debugging output
    return render_template('expense_tracker.html', form=form, expenses=expenses, user_id=user.id, current_year=current_year, current_month=current_month)

# Route to display all expenses
@app.route('/expenses', methods=['GET'])
def all_expenses():
    user_id = session.get('user_id')
    if user_id is None:
        flash('User not logged in!', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if user is None:
        flash('User not found!', 'error')
        return redirect(url_for('login'))

    expenses = user.expenses  # Fetch all expenses for the user

    form = ExpenseForm()
    print("All Expenses:", expenses)  # Print all expenses retrieved from the database
    return render_template('all_expenses.html', expenses=expenses, form=form)

@app.route('/edit_expense/<int:expense_id>', methods=['POST'])
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    
    # Validate CSRF token
    try:
        validate_csrf(request.form['csrf_token'])
    except ValidationError:
        flash('CSRF token validation failed!', 'error')
        return redirect(url_for('all_expenses'))

    # Get updated data from request
    item = request.form['item']
    amount = request.form['amount']
    category = request.form['category']
    date_str = request.form['date']
    
    # Convert date string to date object
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format!', 'error')
        return redirect(url_for('all_expenses'))

    # Update expense
    expense.update(item, amount, category, date)
    flash('Expense updated successfully!', 'success')
    return redirect(url_for('all_expenses'))


@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    # Delete expense
    expense.delete()
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('all_expenses'))

@app.route('/get_expense/<int:expense_id>', methods=['GET'])
def get_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    # Serialize expense data to dictionary
    expense_data = {
        'id': expense.id,
        'item': expense.item,
        'amount': expense.amount,
        'category': expense.category,
        'date': expense.date.strftime('%Y-%m-%d')  # Format date as string
    }
    return jsonify(expense_data)

@app.route('/expenses-data', methods=['GET'])
def expenses_data():
    user_id = session.get('user_id')
    if user_id is None:
        return jsonify({})  # Return an empty object if user is not logged in

    user = User.query.get(user_id)
    if user is None:
        return jsonify({})  # Return an empty object if user is not found

    expenses = user.expenses
    data = {}

    for expense in expenses:
        if expense.category in data:
            data[expense.category] += expense.amount
        else:
            data[expense.category] = expense.amount

    return jsonify(data)

@app.route('/upload_receipt')
def upload_receipt():
    return render_template('upload_receipt.html')

# Connect to the SQLite database (or create it if it doesn't exist)
connection = sqlite3.connect('C:/Users/gedam/OneDrive/Desktop/Design_Engineering_Features/mydatabase.db') # My database name is mydatabase
# Create a cursor object to execute SQL queries
cursor = connection.cursor()
# Drop the existing receipts table if it exists
cursor.execute('DROP TABLE IF EXISTS receipts')  # Create receipts table in mydatabase
# Create receipts table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS receipts (
        id INTEGER PRIMARY KEY,
        filename TEXT,
        price TEXT
    )
''')
connection.commit()
# Close the cursor and connection
cursor.close()
connection.close()


# Define routes

#upload route
@app.route('/upload', methods=['POST'])
def upload():
    try:
        # Save the uploaded file to the 'uploads' directory
        file = request.files['receiptImage']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.referrer)

        filename = secure_filename(file.filename)
        file_path = os.path.join('C:/Users/gedam/OneDrive/Desktop/Design_Engineering_Features/web_app_5.0_integration/uploads/', filename)
        file.save(file_path)

         # Extract prices from the uploaded image using OCR
        prices = extract_price_from_image(file_path) #do not close cursor in this function otherwise database will be closed

        # Establish connection to SQLite database within the request context
        conn = sqlite3.connect('C:/Users/gedam/OneDrive/Desktop/Design_Engineering_Features/mydatabase.db')
        cursor = conn.cursor()

        # Store filename and price in the database
        print('price before function call: ', prices)
        store_in_database(filename, prices)  #do not close cursor in this function otherwise database will be closed

        # Commit changes and close connection
        conn.commit()
        conn.close()

        # Add extracted items to expenses
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        if user is not None:
            for price in prices:
                new_expense = Expense(item="Receipt Item", amount=price, category="Other", date=datetime.now(), user_id=user.id)
                db.session.add(new_expense)
            db.session.commit()

        flash('File uploaded successfully', 'success')
        return redirect(url_for('confirmation', filename=filename))

    except Exception as e:
        flash('An error occurred while uploading the file', 'error')
        return redirect(url_for('error'))
    
@app.route('/error')
def error():
    return render_template('error.html')

@app.route('/error2')
def error2():
    return render_template('error2.html')

@app.route('/confirmation/<filename>')
def confirmation(filename):
    # Render the upload confirmation template
    return render_template('confirmation.html', filename=filename)   #will redirect to receipts from here

#receipt route
@app.route('/receipt/<filename>')
def receipt(filename):
    try:
         # Establish connection to SQLite database within the request context
        conn = sqlite3.connect('C:/Users/gedam/OneDrive/Desktop/Design_Engineering_Features/mydatabase.db')
        cursor = conn.cursor()

         # Retrieve receipt data for the specified filename
        cursor.execute('SELECT price FROM receipts WHERE filename = ?', (filename,))
        prices_data = cursor.fetchall()

        # Extract the prices from the fetched data
        prices = [price[0] for price in prices_data]
        # Close connection
        conn.close()

        return render_template('receipt.html', prices=prices) # Pass the prices to the template
    
    except Exception as e:
        flash('An error occurred while retrieving receipt data', 'error')
        return redirect(url_for('error2'))

def extract_price_from_image(image_path):
    try:
        #Open OCR Subprocess
        process = subprocess.Popen(['python', 'C:/Users/gedam/OneDrive/Desktop/Design_Engineering_Features/web_app_5.0_integration/ocr1.py', image_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

         #Set a timeout of 60 seconds
        output, _ = process.communicate(timeout=180) 

        print('returned out put : ', output)

        # Decode the byte string and split it into a list of prices
        prices_str = output.decode('utf-8').strip()
        print("Extracted prices string:", prices_str)  # Debugging statement
        
        # Filter out non-numeric values and convert to float
        prices = [float(price) for price in prices_str.split(', ') if price.replace('.', '', 1).isdigit()]
    
    except subprocess.TimeoutExpired:
        # Process timed out
        print("OCR script execution timed out")
        prices = None
    except Exception as e:
        # Other exceptions
        print("Error executing OCR script:", str(e))
        prices = None
        
    return prices

def store_in_database(filename, price):
    try:
        # Establish connection to SQLite database within the request context
        conn = sqlite3.connect('C:/Users/gedam/OneDrive/Desktop/Design_Engineering_Features/mydatabase.db')
        cursor = conn.cursor()

        print('prices before storing : ',price)
         # Insert each price as a separate row
        for prices in price:
            cursor.execute('INSERT INTO receipts (filename, price) VALUES (?, ?)', (filename, prices))

        conn.commit()

        # Close connection
        conn.close()
    except Exception as e:
        print("Error storing data in the database:", str(e))

@app.route('/logout')
def logout():
    session.clear()  # Clear the session data
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))  # Redirect to the login page


@app.route('/statement/<int:year>/<int:month>')
def generate_statement(year, month):
    user_id = session.get('user_id')
    if user_id is None:
        flash('User not logged in!', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if user is None:
        flash('User not found!', 'error')
        return redirect(url_for('login'))

    # Fetch expenses for the specified month and year
    expenses = Expense.query.filter(
        db.extract('year', Expense.date) == year,
        db.extract('month', Expense.date) == month,
        Expense.user_id == user.id
    ).all()

    total_expenses = sum(expense.amount for expense in expenses)

    # Pass the expenses data to the template for rendering
    return render_template('statement.html', expenses=expenses, total_expenses=total_expenses)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

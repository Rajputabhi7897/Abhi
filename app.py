from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import hashlib

app = Flask(__name__)

# Configure MySQL connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your_password'
app.config['MYSQL_DB'] = 'railway_booking'

mysql = MySQL(app)

# Secret key for session management
app.secret_key = 'your_secret_key'

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user and hashlib.sha256(password.encode()).hexdigest() == user['password']:
            session['user_id'] = user['user_id']
            return redirect(url_for('search_trains'))
        else:
            return 'Invalid login details'
    return render_template('login.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users(username, email, password) VALUES (%s, %s, %s)", (username, email, hashed_password))
        mysql.connection.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Search Trains route
@app.route('/search', methods=['GET', 'POST'])
def search_trains():
    if request.method == 'POST':
        source = request.form['source']
        destination = request.form['destination']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM trains WHERE source = %s AND destination = %s", (source, destination))
        trains = cursor.fetchall()
        
        return render_template('search.html', trains=trains)
    return render_template('search.html')

# Book Tickets route
@app.route('/book/<train_id>', methods=['GET', 'POST'])
def book_ticket(train_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        seats = int(request.form['seats'])
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM trains WHERE train_id = %s", (train_id,))
        train = cursor.fetchone()

        if train and train['available_seats'] >= seats:
            cursor.execute("INSERT INTO bookings(user_id, train_id, seats) VALUES (%s, %s, %s)", 
                           (session['user_id'], train_id, seats))
            cursor.execute("UPDATE trains SET available_seats = available_seats - %s WHERE train_id = %s", 
                           (seats, train_id))
            mysql.connection.commit()
            return redirect(url_for('booking_history'))
        else:
            return 'Not enough available seats.'

    return render_template('book.html')

# Booking History route
@app.route('/history')
def booking_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM bookings WHERE user_id = %s", (session['user_id'],))
    bookings = cursor.fetchall()
    return render_template('history.html', bookings=bookings)

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, text
import os
import random
import string

app = Flask(__name__)

# Set environment variables for database connection
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'clothes-shop-428417-b87b866f6d53-sql.json'
os.environ['INSTANCE_CONNECTION_NAME'] = 'clothes-shop-428417:us-central1:clothes-shop'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASS'] = 'Moein1378!@'
os.environ['DB_NAME'] = 'postgres'

# Generate a random secret key for the app
def generate_secret_key(length=24):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

app.secret_key = generate_secret_key()

# Initialize database connection pool
from connect_connector import connect_with_connector  # Ensure the module is in the same directory
engine = connect_with_connector()

def get_db_connection():
    return engine.connect()

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        conn = get_db_connection()
        try:
            conn.execute(text("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)"),
                         {'username': username, 'email': email, 'password': password})
            conn.commit()
        except Exception as e:
            flash('Registration failed. Please try again.')
            return render_template('register.html')
        finally:
            conn.close()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        result = conn.execute(text("SELECT * FROM users WHERE email = :email"), {'email': email})
        user = result.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Please check your credentials and try again.')
    
    return render_template('login.html')

# User Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully.')
    return redirect(url_for('index'))

# Index route
@app.route('/')
def index():
    conn = get_db_connection()
    result = conn.execute(text('SELECT * FROM products'))
    products = result.fetchall()
    conn.close()
    view = request.args.get('view', 'grid')
    return render_template('index.html', products=products, view=view)

# Product details route
@app.route('/product/<int:product_id>')
def product(product_id):
    conn = get_db_connection()
    result = conn.execute(text('SELECT * FROM products WHERE id = :id'), {'id': product_id})
    product = result.fetchone()
    conn.close()
    return render_template('product.html', product=product)

# Cart route
@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    product_ids = list(cart.keys())
    products = []
    if product_ids:
        conn = get_db_connection()
        query = text(f"SELECT * FROM products WHERE id IN ({','.join([':id' + str(i) for i in range(len(product_ids))])})")
        params = {f"id{i}": product_id for i, product_id in enumerate(product_ids)}
        result = conn.execute(query, params)
        products = result.fetchall()
        conn.close()
    return render_template('cart.html', cart=cart, products=products)

# Add to cart route
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    cart = session.get('cart', {})
    str_product_id = str(product_id)
    cart[str_product_id] = cart.get(str_product_id, 0) + 1
    session['cart'] = cart
    return redirect(url_for('cart'))

# Remove from cart route
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    str_product_id = str(product_id)
    if str_product_id in cart:
        if cart[str_product_id] > 1:
            cart[str_product_id] -= 1
        else:
            del cart[str_product_id]
    session['cart'] = cart
    return redirect(url_for('cart'))

if __name__ == '__main__':
    app.run(debug=True)


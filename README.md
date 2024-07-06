# Online Clothing Store

Here are the main files for this project:

```bash
ENGR5590G-Assignment/
├── __pycache__/
├── static/
│   ├── css/
│   │   ├── styles.css
│   ├── js/
│   │   ├── dark-mode.js
├── templates/
│   ├── base.html
│   ├── cart.html 
│   ├── index.html
│   ├── login.html
│   ├── product.html
│   ├── register.html
├── app.py
├── app.yaml
├── connect_connector.py
├── README.md
└── tables.sql

```

 ### Create Root Files

 ## 1. Create app.py

This code sets up a Flask web application for an e-commerce platform with user registration, login, product display, cart management, and database connectivity using SQLAlchemy.

```python
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, text
import os
import random
import string

app = Flask(__name__)

# Set environment variables for database connection
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'Your JSON File Path'
os.environ['INSTANCE_CONNECTION_NAME'] = 'Your Instance Connection Name'
os.environ['DB_USER'] = 'Your Data Base User Name'
os.environ['DB_PASS'] = 'Your Data Base Password'
os.environ['DB_NAME'] = 'Your Data Base Name'

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

 ```

## 2. Create connect_connector.py

This file establishes a connection pool to a Google Cloud SQL instance using the Cloud SQL Python Connector and SQLAlchemy for a Postgres database.

```python
import os
from google.cloud.sql.connector import Connector, IPTypes
import pg8000
import sqlalchemy

def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    """
    Initializes a connection pool for a Cloud SQL instance of Postgres.

    Uses the Cloud SQL Python Connector package.
    """
    instance_connection_name = os.environ[
        "INSTANCE_CONNECTION_NAME"
    ]  # e.g. 'project:region:instance'
    db_user = os.environ["DB_USER"]  # e.g. 'my-db-user'
    db_pass = os.environ["DB_PASS"]  # e.g. 'my-db-password'
    db_name = os.environ["DB_NAME"]  # e.g. 'my-database'

    ip_type = IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC

    # initialize Cloud SQL Python Connector object
    connector = Connector()

    def getconn() -> pg8000.dbapi.Connection:
        conn: pg8000.dbapi.Connection = connector.connect(
            instance_connection_name,
            "pg8000",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type=ip_type,
        )
        return conn

    pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,  # 30 seconds
        pool_recycle=1800,  # 30 minutes

    )
    return pool
```
## 3. Create tables.sql

This SQL script creates a schema for an e-commerce platform with the following tables and relationships:

- `users`: Stores user information with unique usernames and emails.
- `products`: Stores product details including name, description, price, stock, and an optional image URL.
- `carts`: Stores cart details linked to users.
- `cart_items`: Stores items in carts linked to specific products.
- `orders`: Stores order details linked to users with the total amount.
- `order_items`: Stores items in orders linked to specific products, along with quantity and price.

Each table includes appropriate primary keys and foreign key references to maintain relationships between users, carts, products, and orders.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INT DEFAULT 0,
    image_url VARCHAR(255)
);

CREATE TABLE carts (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cart_items (
    id SERIAL PRIMARY KEY,
    cart_id INT REFERENCES carts(id),
    product_id INT REFERENCES products(id),
    quantity INT DEFAULT 1
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    total DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);
```
## 4. Create Sample Data for Tables

USERS
```sql
INSERT INTO users (username, email, password) VALUES
('john_doe', 'john@example.com', 'hashed_password_1'),
('jane_smith', 'jane@example.com', 'hashed_password_2'),
('alice_jones', 'alice@example.com', 'hashed_password_3'),
('bob_brown', 'bob@example.com', 'hashed_password_4'),
('charlie_clark', 'charlie@example.com', 'hashed_password_5'),
('dave_davis', 'dave@example.com', 'hashed_password_6'),
('eve_evans', 'eve@example.com', 'hashed_password_7'),
('frank_franklin', 'frank@example.com', 'hashed_password_8'),
('grace_green', 'grace@example.com', 'hashed_password_9'),
('henry_hill', 'henry@example.com', 'hashed_password_10');
```
Products
```sql
INSERT INTO products (name, description, price, stock, image_url) VALUES
('Laptop', 'A high-performance laptop', 999.99, 10, 'http://example.com/images/laptop.png'),
('Smartphone', 'Latest model smartphone', 799.99, 25, 'http://example.com/images/smartphone.png'),
('Headphones', 'Noise-cancelling headphones', 199.99, 50, 'http://example.com/images/headphones.png'),
('Keyboard', 'Mechanical keyboard', 89.99, 30, 'http://example.com/images/keyboard.png'),
('Mouse', 'Wireless mouse', 49.99, 40, 'http://example.com/images/mouse.png'),
('Monitor', '24-inch monitor', 129.99, 20, 'http://example.com/images/monitor.png'),
('Printer', 'All-in-one printer', 159.99, 15, 'http://example.com/images/printer.png'),
('Webcam', 'HD webcam', 79.99, 35, 'http://example.com/images/webcam.png'),
('Tablet', '10-inch tablet', 299.99, 25, 'http://example.com/images/tablet.png'),
('Charger', 'Fast charging USB-C charger', 29.99, 100, 'http://example.com/images/charger.png');
```
Carts

```sql
INSERT INTO carts (user_id) VALUES
(1),
(2),
(3),
(4),
(5),
(6),
(7),
(8),
(9),
(10);
```

Cart Items

```sql
INSERT INTO cart_items (cart_id, product_id, quantity) VALUES
(1, 1, 1),
(1, 2, 2),
(2, 3, 1),
(2, 4, 1),
(3, 5, 1),
(3, 6, 1),
(4, 7, 1),
(4, 8, 1),
(5, 9, 1),
(5, 10, 1);
```

Orders

```sql
INSERT INTO orders (user_id, total) VALUES
(1, 2599.97),
(2, 289.98),
(3, 219.98),
(4, 239.98),
(5, 329.98),
(6, 459.98),
(7, 499.98),
(8, 559.98),
(9, 299.98),
(10, 29.99);
```

Order Items

```sql
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
(1, 1, 1, 999.99),
(1, 2, 2, 799.99),
(2, 3, 1, 199.99),
(2, 4, 1, 89.99),
(3, 5, 1, 49.99),
(3, 6, 1, 129.99),
(4, 7, 1, 159.99),
(4, 8, 1, 79.99),
(5, 9, 1, 299.99),
(5, 10, 1, 29.99);
```
## 5. Create app.yaml 

This YAML configuration file sets up a Flask application deployment on Google App Engine (Standard Environment) with Python 3.9, configuring environment variables for PostgreSQL database connection, static file serving, Gunicorn as the entrypoint, and automatic scaling based on CPU utilization.

```yaml
runtime: python39

env_variables:
  INSTANCE_CONNECTION_NAME: [Cloud SQL instance connection name]
  DB_USER: [Database username]
  DB_PASS: [Database password]
  DB_NAME: [Database name]
  DB_HOST: [Database host IP address]
  DB_PORT: [Database port]

handlers:
- url: /static
  static_dir: static

- url: /.*
  script: auto

entrypoint: gunicorn -b :$PORT app:app

# optional, but recommended to avoid long timeouts
instance_class: F2

# optional, but recommended for Flask applications with sessions
# increasing max idle instances to improve startup time
automatic_scaling:
  target_cpu_utilization: 0.65
  min_instances: 1
  max_instances: 5


```

### Create Templates Folder

1. In the project directory, create a folder named `templates`.
2. Inside `templates`, create six HTML files: `base.html`, `index.html`, `product.html`, `cart.html`, `login.html`, and `register.html`.

## 1. Create index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
    <title>Online Shop</title>
</head>
<body>
    <header>
        <h1>Online Clothing Store</h1>
        <nav>
            <a href="{{ url_for('index') }}">Home</a>
            <a href="{{ url_for('cart') }}">Cart</a>
            {% if session['user_id'] %}
                <a href="{{ url_for('logout') }}">Logout</a>
            {% else %}
                <a href="{{ url_for('login') }}">Login</a>
                <a href="{{ url_for('register') }}">Register</a>
            {% endif %}
        </nav>
        <button id="toggle-dark-mode">Toggle Dark Mode</button>
    </header>
    <main>
        {% block content %}{% endblock %}
    </main>
    <footer>
        <p>&copy; 2024 Online Shop</p>
    </footer>
    <script src="{{ url_for('static', filename='js/dark-mode.js') }}"></script>
</body>
</html>

```

## 2. Create base.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
    <title>Online Shop</title>
</head>
<body>
    <header>
        <h1>Online Clothing Store</h1>
        <nav>
            <a href="{{ url_for('index') }}">Home</a>
            <a href="{{ url_for('cart') }}">Cart</a>
            {% if session['user_id'] %}
                <a href="{{ url_for('logout') }}">Logout</a>
            {% else %}
                <a href="{{ url_for('login') }}">Login</a>
                <a href="{{ url_for('register') }}">Register</a>
            {% endif %}
        </nav>
        <button id="toggle-dark-mode">Toggle Dark Mode</button>
    </header>
    <main>
        {% block content %}{% endblock %}
    </main>
    <footer>
        <p>&copy; 2024 Online Shop</p>
    </footer>
    <script src="{{ url_for('static', filename='js/dark-mode.js') }}"></script>
</body>
</html>
```

## 3. Create cart.html

```html
{% extends "base.html" %}

{% block content %}
<h1>Cart</h1>
<ul class="cart-list">
    {% set total_items = 0 %}
    {% set total_price = 0 %}
    {% for product in products %}
        {% set product_id = product.id | string %}
        {% if product_id in cart %}
            <li class="cart-item">
                <img src="{{ product.image_url }}" alt="{{ product.name }}" class="product-image">
                <div class="product-details">
                    <h3>{{ product.name }}</h3>
                    <p>Quantity: {{ cart[product_id] }}</p>
                    <p>Total: ${{ product.price * cart[product_id] }}</p>
                </div>
            </li>
            {% set total_items = total_items + cart[product_id] %}
            {% set total_price = total_price + (product.price * cart[product_id]) %}
        {% else %}
            <li>Product ID {{ product.id }} not found in cart</li>
        {% endif %}
    {% endfor %}
</ul>
<p>Total Items: {{ total_items }}</p>
<p>Total Price: ${{ total_price }}</p>
<a href="{{ url_for('index') }}">Continue Shopping</a>
{% endblock %}
```


## 4. Create product.html

```html
{% extends "base.html" %}

{% block content %}
<h2>{{ product[1] }}</h2>
<img src="{{ product[5] }}" alt="{{ product[1] }}" class="product-image">
<p>{{ product[2] }}</p>
<p>${{ product[3] }}</p>
<a href="{{ url_for('add_to_cart', product_id=product[0]) }}" class="btn-add-to-cart">Add to Cart</a>
{% endblock %}
```

## 5. Create login.html

```html
{% extends "base.html" %}

{% block content %}
<h2>Login</h2>
<form method="POST" action="{{ url_for('login') }}">
    <label for="email">Email:</label>
    <input type="email" name="email" id="email" required>
    <label for="password">Password:</label>
    <input type="password" name="password" id="password" required>
    <button type="submit">Login</button>
</form>
{% endblock %}
```

## 6. Create register.html

```html
{% extends "base.html" %}

{% block content %}
<h2>Register</h2>
<form method="POST" action="{{ url_for('register') }}">
    <label for="username">Username:</label>
    <input type="text" name="username" id="username" required>
    <label for="email">Email:</label>
    <input type="email" name="email" id="email" required>
    <label for="password">Password:</label>
    <input type="password" name="password" id="password" required>
    <button type="submit">Register</button>
</form>
{% endblock %}
```

## Add CSS for Better UI

### Create Static Folder and Subfolders

1. In the project directory, create a folder named `static`.
2. Inside `static`, create two folders named `css` and `js`.
3. Inside `static/css`, create a file named `styles.css`.
4. Inside `static/js`, create a file named `dark-mode.js`.

## Create styles.css

```css
/* Improved base styles */
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f9f9f9;
    transition: background-color 0.3s, color 0.3s;
}

body.dark-mode {
    background-color: #121212;
    color: #ffffff;
}

header {
    background-color: #333;
    color: #fff;
    padding: 1rem;
    text-align: center;
}

header.dark-mode {
    background-color: #000;
}

nav a {
    color: #fff;
    margin: 0 1rem;
    text-decoration: none;
}

nav a:hover {
    text-decoration: underline;
}

main {
    padding: 2rem;
}

footer {
    background-color: #333;
    color: #fff;
    text-align: center;
    padding: 1rem;
    position: fixed;
    bottom: 0;
    width: 100%;
}

footer.dark-mode {
    background-color: #000;
}

ul {
    list-style: none;
    padding: 0;
}

.product-item {
    border: 1px solid #ccc;
    padding: 1rem;
    margin: 1rem 0;
    text-align: center;
    background-color: #fff;
    transition: background-color 0.3s, border-color 0.3s;
}

.product-item:hover {
    border-color: #999;
    background-color: #f1f1f1;
}

.product-image {
    max-width: 200px;
    max-height: 200px;
    display: block;
    margin: 0 auto 1rem;
}

.grid-view .product-item {
    display: inline-block;
    width: 30%;
    margin: 1%;
}

.list-view .product-item {
    display: block;
    width: 100%;
}

.btn-add-to-cart,
.btn-view,
.btn-remove {
    background-color: #333;
    color: #fff;
    padding: 0.5rem 1rem;
    text-decoration: none;
    border-radius: 5px;
    display: inline-block;
}

.btn-add-to-cart:hover,
.btn-view:hover,
.btn-remove:hover {
    background-color: #555;
}

.cart-list .cart-item {
    display: flex;
    align-items: center;
    border: 1px solid #ccc;
    padding: 1rem;
    margin: 1rem 0;
}

.cart-list .product-image {
    max-width: 100px;
    max-height: 100px;
    margin-right: 1rem;
}

.cart-list .product-details {
    flex-grow: 1;
}
```
## Create dark-mode.js

```js
document.getElementById('toggle-dark-mode').addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    document.querySelector('header').classList.toggle('dark-mode');
    document.querySelector('footer').classList.toggle('dark-mode');
});
```
### Create database on Google Cloud SQL

## PostgreSQL

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click on the project dropdown and select the project you created for this tutorial.
3. In the search bar, type "SQL" and select "Cloud SQL" from the results.
4. Click on "Create Instance".
5. Fill in the required information for your Cloud SQL instance, such as the instance name, region, and machine type.
6. Click "Create".
7. Wait for the instance to be created.
8. Once the instance is created, click on the instance name to open its details page.
9. In the left navigation menu, click on "Users and permissions".
10. Click on "Add user".
11. Fill in the required information for the user, such as the username, password, and host.
12. Click "Create".
13. Wait for the user to be added.
14. Click on the instance name to open its details page.
15. In the left navigation menu, click on "Connections".
16. Click on "Add connection".
17. Fill in the required information for the connection, such as the connection name, IP address, and port.
18. Click "Create".
19. Wait for the connection to be added.
20. Click on the instance name to open its details page.
21. In the left navigation menu, click on "Databases".
22. Click on "Add database".
23. Fill in the required information for the database, such as the database name.
24. Click "Create".
25. Wait for the database to be created.
26. Click on the instance name to open its details page.
27. Add sample data to the database


## Run the Application

### Set up a service account

Create and configure a Google Cloud service account that has the Cloud SQL Client role with permissions to connect to Cloud SQL. After you create a service account, you might need to wait for 60 seconds or more before you use the service account.

#### 1. Create a service account

1. In the Google Cloud console, go to the Create service account page.
[Go to Create service account](https://console.cloud.google.com/projectselector/iam-admin/serviceaccounts/create?_ga=2.61800879.2088878077.1720018590-848580627.1719238841&_gac=1.247005942.1720135752.CjwKCAjwkJm0BhBxEiwAwT1AXDvLwJTqp1fycYjMK4i8xCh5do_1vf_YU2cxqYaNtPkF5rx7hcV5LhoCI_YQAvD_BwEr)
2. Select a Google Cloud project.
3. Enter a quickstart-service-account as the service account name.
4. Optional: Enter a description of the service account.
5. Click Create and continue and continue to the next step.
6. Choose the Cloud SQL Client role to grant to the service account on the project.
7. Click Continue.
8. Click Done to finish creating the service account.

#### 2. Create and download the service account key file

For more information, see this website.

[Connect to Cloud SQL for PostgreSQL from your local computer](https://cloud.google.com/sql/docs/postgres/connect-instance-local-computer#python_3)

1. In the Google Cloud console, go to the Service accounts page.
[Go to Service accounts](https://console.cloud.google.com/iam-admin/serviceaccounts?_ga=2.64872876.2088878077.1720018590-848580627.1719238841&_gac=1.83633636.1720135752.CjwKCAjwkJm0BhBxEiwAwT1AXDvLwJTqp1fycYjMK4i8xCh5do_1vf_YU2cxqYaNtPkF5rx7hcV5LhoCI_YQAvD_BwE)
2. Select a project.
3. Click the email address of the quickstart-service-account service account that you want to create a key for.
4. Click the Keys tab.
5. Click the Add key drop-down menu, then select Create new key.
6. Select JSON as the Key type and click Create.

Clicking Create downloads a service account key file. After you download the key file, you cannot download it again.

Make sure to store the key file securely, because it can be used to authenticate as your service account. You can move and rename this file however you would like.

### Install the Required Variables

Windows:

```bash
setx GOOGLE_APPLICATION_CREDENTIALS path/to/service/account/key.json
setx INSTANCE_CONNECTION_NAME INSTANCE_CONNECTION_NAME"
setx DB_PORT 5432
setx DB_NAME ""
setx DB_USER ""
setx DB_PASS ""
```

### Run the Flask App

1. In Visual Studio, set the startup file to `OnlineShopping.py` if not already set.
2. Click **Run** or press **F5** to start the server.
3. Open your web browser and navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/).


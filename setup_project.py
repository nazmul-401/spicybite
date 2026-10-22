import os

files = {
    "database/database.sql": """-- Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products / Menu Table (CRUD Operations)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    image TEXT NOT NULL
);

-- Messages Table (Contact/Feedback System)
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders Table
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    item_name TEXT NOT NULL,
    price REAL NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""",

    "backend/app.py": """from flask import Flask, request, jsonify, session, send_from_directory
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

FRONTEND_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../database/restaurant.db'))

app = Flask(__name__, static_folder=FRONTEND_FOLDER, static_url_path='')
app.secret_key = 'spicebite_secret_key_for_assignment'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL,
        category TEXT NOT NULL,
        image TEXT NOT NULL
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT NOT NULL,
        item_name TEXT NOT NULL,
        price REAL NOT NULL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        sample_foods = [
            ('Classic Beef Burger', 'Juicy grilled beef patty with cheddar cheese, fresh lettuce, and house sauce.', 350.0, 'Burger', 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=80'),
            ('Margherita Pizza', 'Traditional Italian pizza topped with fresh mozzarella, tomatoes, and basil leaves.', 650.0, 'Pizza', 'https://images.unsplash.com/photo-1604382355076-af4b0eb60143?w=600&auto=format&fit=crop&q=80'),
            ('Hyderabadi Chicken Biryani', 'Aromatic basmati rice cooked with tender spiced chicken, saffron, and herbs.', 420.0, 'Rice', 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80'),
            ('Creamy Alfredo Pasta', 'Fettuccine pasta tossed in rich parmesan cream sauce with grilled chicken.', 380.0, 'Pasta', 'https://images.unsplash.com/photo-1621996346565-e3d5d6281298?w=600&auto=format&fit=crop&q=80'),
            ('Crispy Fried Chicken', 'Golden crunchy fried chicken pieces served with spicy garlic dip.', 290.0, 'Snacks', 'https://images.unsplash.com/photo-1626645738196-c2a7c87a8f58?w=600&auto=format&fit=crop&q=80'),
            ('Chocolate Lava Cake', 'Warm rich chocolate cake with a molten chocolate center and vanilla ice cream.', 220.0, 'Dessert', 'https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=600&auto=format&fit=crop&q=80')
        ]
        cursor.executemany('INSERT INTO products (name, description, price, category, image) VALUES (?, ?, ?, ?, ?)', sample_foods)
    
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(FRONTEND_FOLDER, path)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    if not name or not email or len(password) < 6:
        return jsonify({'error': 'All fields are required and password must be at least 6 characters.'}), 400
        
    hashed_pw = generate_password_hash(password)
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, hashed_pw))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Registration successful! You can now log in.'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists! Try logging in.'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['user_id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        return jsonify({'message': 'Login successful!', 'user': {'name': user['name'], 'email': user['email']}}), 200
    return jsonify({'error': 'Invalid email or password!'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/session', methods=['GET'])
def get_session():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'name': session['user_name'], 'email': session['user_email']})
    return jsonify({'logged_in': False})

@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    price = data.get('price')
    category = data.get('category', '').strip()
    image = data.get('image', '').strip() or 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=80'
    
    if not name or not description or not price or not category:
        return jsonify({'error': 'Please fill all required fields!'}), 400
        
    conn = get_db_connection()
    conn.execute('INSERT INTO products (name, description, price, category, image) VALUES (?, ?, ?, ?, ?)',
                 (name, description, float(price), category, image))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Food item added successfully!'}), 201

@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.json
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    price = data.get('price')
    category = data.get('category', '').strip()
    
    if not name or not description or not price or not category:
        return jsonify({'error': 'All fields are required for update!'}), 400
        
    conn = get_db_connection()
    conn.execute('UPDATE products SET name = ?, description = ?, price = ?, category = ? WHERE id = ?',
                 (name, description, float(price), category, id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Food item updated successfully!'})

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Food item deleted successfully!'})

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    data = request.json
    user_name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    message = data.get('message', '').strip()
    
    if not user_name or not email or not message:
        return jsonify({'error': 'All fields are required!'}), 400
        
    conn = get_db_connection()
    conn.execute('INSERT INTO messages (user_name, email, message) VALUES (?, ?, ?)', (user_name, email, message))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Thank you! Your message has been stored in our database.'}), 201

@app.route('/api/orders', methods=['POST'])
def place_order():
    data = request.json
    item_name = data.get('item_name')
    price = data.get('price')
    user_email = session.get('user_email', 'Guest User')
    
    conn = get_db_connection()
    conn.execute('INSERT INTO orders (user_email, item_name, price) VALUES (?, ?, ?)', (user_email, item_name, price))
    conn.commit()
    conn.close()
    return jsonify({'message': f'Order placed for {item_name} (৳{price}) by {user_email}!'}), 201

if __name__ == '__main__':
    init_db()
    print("Server running at: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
""",

    "frontend/css/style.css": """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

body {
    background-color: #faf9f6;
    color: #333;
    line-height: 1.6;
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

header {
    background-color: #1e272e;
    color: #fff;
    padding: 1rem 5%;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
}

.logo {
    font-size: 1.8rem;
    font-weight: bold;
    color: #ff5e57;
    text-decoration: none;
}

.nav-links {
    list-style: none;
    display: flex;
    gap: 1.5rem;
    align-items: center;
}

.nav-links a {
    color: #fff;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s;
}

.nav-links a:hover, .nav-links a.active {
    color: #ff5e57;
}

main {
    flex: 1;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
    padding: 2rem 5%;
}

.hero {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 2rem;
    background: linear-gradient(135deg, #fff5f5 0%, #ffe3e3 100%);
    padding: 3rem;
    border-radius: 15px;
    margin-bottom: 3rem;
}

.hero-text {
    flex: 1;
}

.hero-text h1 {
    font-size: 2.8rem;
    color: #1e272e;
    margin-bottom: 1rem;
}

.hero-text p {
    font-size: 1.1rem;
    color: #555;
    margin-bottom: 1.5rem;
}

.hero-image {
    flex: 1;
    text-align: center;
}

.hero-image img {
    max-width: 100%;
    border-radius: 15px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.btn {
    display: inline-block;
    background-color: #ff5e57;
    color: #fff;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    text-decoration: none;
    font-size: 1rem;
    font-weight: 600;
    transition: background 0.3s;
}

.btn:hover {
    background-color: #ff3f34;
}

.btn-secondary {
    background-color: #485460;
}

.btn-danger {
    background-color: #e84118;
}

.section-title {
    text-align: center;
    font-size: 2rem;
    margin-bottom: 2rem;
    color: #1e272e;
}

.grid-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 2rem;
}

.card {
    background: #fff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    display: flex;
    flex-direction: column;
    transition: transform 0.3s;
}

.card:hover {
    transform: translateY(-5px);
}

.card img {
    width: 100%;
    height: 200px;
    object-fit: cover;
}

.card-body {
    padding: 1.5rem;
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.badge {
    background: #ffeaa7;
    color: #d35400;
    padding: 0.2rem 0.6rem;
    border-radius: 5px;
    font-size: 0.8rem;
    font-weight: bold;
    display: inline-block;
    margin-bottom: 0.5rem;
}

.price {
    font-size: 1.3rem;
    font-weight: bold;
    color: #2ecc71;
    margin: 0.8rem 0;
}

.card-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
    flex-wrap: wrap;
}

.form-container {
    background: #fff;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    max-width: 600px;
    margin: 2rem auto;
}

.form-group {
    margin-bottom: 1.2rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.4rem;
    font-weight: 600;
}

.form-group input, .form-group select, .form-group textarea {
    width: 100%;
    padding: 0.8rem;
    border: 1px solid #ccc;
    border-radius: 6px;
    font-size: 1rem;
}

.alert {
    padding: 0.8rem 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
    display: none;
}

.alert-error {
    background: #ffd2d2;
    color: #d8000c;
}

.alert-success {
    background: #dff2bf;
    color: #4f8a10;
}

.auth-wrapper {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

footer {
    background-color: #1e272e;
    color: #fff;
    text-align: center;
    padding: 1.5rem;
    margin-top: auto;
}

@media (max-width: 768px) {
    .hero {
        flex-direction: column;
        text-align: center;
        padding: 2rem 1rem;
    }
    .navbar {
        flex-direction: column;
        gap: 1rem;
    }
    .nav-links {
        flex-wrap: wrap;
        justify-content: center;
    }
}
""",

    "frontend/js/script.js": """document.addEventListener('DOMContentLoaded', () => {
    checkSession();
    if (document.getElementById('menu-grid')) {
        loadProducts();
    }
    if (document.getElementById('featured-grid')) {
        loadFeaturedProducts();
    }
});

async function checkSession() {
    try {
        const res = await fetch('/api/session');
        const data = await res.json();
        const authLink = document.getElementById('auth-link');
        if (authLink) {
            if (data.logged_in) {
                authLink.innerHTML = `<a href="#" onclick="logoutUser()">Logout (${data.name})</a>`;
            } else {
                authLink.innerHTML = `<a href="login.html">Login / Register</a>`;
            }
        }
    } catch (e) {
        console.error('Session check failed', e);
    }
}

async function logoutUser() {
    await fetch('/api/logout', { method: 'POST' });
    window.location.href = 'index.html';
}

function showMessage(elementId, text, isError = false) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.style.display = 'block';
    el.textContent = text;
    el.className = isError ? 'alert alert-error' : 'alert alert-success';
    setTimeout(() => { el.style.display = 'none'; }, 5000);
}

async function loadFeaturedProducts() {
    const grid = document.getElementById('featured-grid');
    const res = await fetch('/api/products');
    const products = await res.json();
    grid.innerHTML = products.slice(0, 3).map(item => `
        <article class="card">
            <img src="${item.image}" alt="${item.name}">
            <div class="card-body">
                <div>
                    <span class="badge">${item.category}</span>
                    <h3>${item.name}</h3>
                    <p>${item.description}</p>
                </div>
                <div>
                    <div class="price">৳${item.price}</div>
                    <a href="menu.html" class="btn">View Full Menu</a>
                </div>
            </div>
        </article>
    `).join('');
}

async function loadProducts() {
    const grid = document.getElementById('menu-grid');
    const res = await fetch('/api/products');
    const products = await res.json();
    
    grid.innerHTML = products.map(item => `
        <article class="card">
            <img src="${item.image}" alt="${item.name}">
            <div class="card-body">
                <div>
                    <span class="badge">${item.category}</span>
                    <h3>${item.name}</h3>
                    <p>${item.description}</p>
                </div>
                <div>
                    <div class="price">৳${item.price}</div>
                    <div class="card-actions">
                        <button class="btn" onclick="orderFood('${item.name.replace(/'/g, "\\\\'")}', ${item.price})">Order Now</button>
                        <button class="btn btn-secondary" onclick="populateEditForm(${item.id}, '${item.name.replace(/'/g, "\\\\'")}', '${item.description.replace(/'/g, "\\\\'")}', ${item.price}, '${item.category}')">Edit</button>
                        <button class="btn btn-danger" onclick="deleteProduct(${item.id})">Delete</button>
                    </div>
                </div>
            </div>
        </article>
    `).join('');
}

async function orderFood(itemName, price) {
    const res = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_name: itemName, price: price })
    });
    const data = await res.json();
    alert(data.message);
}

async function handleProductSubmit(event) {
    event.preventDefault();
    const id = document.getElementById('product-id').value;
    const name = document.getElementById('food-name').value.trim();
    const description = document.getElementById('food-desc').value.trim();
    const price = document.getElementById('food-price').value;
    const category = document.getElementById('food-category').value;
    const image = document.getElementById('food-image').value.trim();

    if (!name || !description || price <= 0) {
        showMessage('crud-msg', 'Please enter valid food name, description, and positive price!', true);
        return;
    }

    const payload = { name, description, price, category, image };
    const url = id ? `/api/products/${id}` : '/api/products';
    const method = id ? 'PUT' : 'POST';

    const res = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok) {
        showMessage('crud-msg', data.message, false);
        document.getElementById('product-form').reset();
        document.getElementById('product-id').value = '';
        document.getElementById('form-submit-btn').textContent = 'Add Food Item';
        loadProducts();
    } else {
        showMessage('crud-msg', data.error, true);
    }
}

function populateEditForm(id, name, desc, price, category) {
    document.getElementById('product-id').value = id;
    document.getElementById('food-name').value = name;
    document.getElementById('food-desc').value = desc;
    document.getElementById('food-price').value = price;
    document.getElementById('food-category').value = category;
    document.getElementById('form-submit-btn').textContent = 'Update Food Item';
    document.getElementById('product-form').scrollIntoView({ behavior: 'smooth' });
}

async function deleteProduct(id) {
    if (!confirm('Are you sure you want to delete this food item?')) return;
    const res = await fetch(`/api/products/${id}`, { method: 'DELETE' });
    if (res.ok) {
        loadProducts();
    }
}

async function handleContactSubmit(event) {
    event.preventDefault();
    const name = document.getElementById('contact-name').value.trim();
    const email = document.getElementById('contact-email').value.trim();
    const message = document.getElementById('contact-message').value.trim();

    const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
    if (name.length < 2) {
        showMessage('contact-msg', 'Please enter a valid name (at least 2 characters).', true);
        return;
    }
    if (!emailRegex.test(email)) {
        showMessage('contact-msg', 'Please enter a valid email address.', true);
        return;
    }
    if (message.length < 10) {
        showMessage('contact-msg', 'Message must be at least 10 characters long.', true);
        return;
    }

    const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, message })
    });
    const data = await res.json();
    if (res.ok) {
        showMessage('contact-msg', data.message, false);
        document.getElementById('contact-form').reset();
    } else {
        showMessage('contact-msg', data.error, true);
    }
}

async function handleRegisterSubmit(event) {
    event.preventDefault();
    const name = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;

    const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
    if (name.length < 3) {
        showMessage('reg-msg', 'Name must be at least 3 characters long.', true);
        return;
    }
    if (!emailRegex.test(email)) {
        showMessage('reg-msg', 'Invalid email address.', true);
        return;
    }
    if (password.length < 6) {
        showMessage('reg-msg', 'Password must be at least 6 characters long.', true);
        return;
    }

    const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password })
    });
    const data = await res.json();
    if (res.ok) {
        showMessage('reg-msg', data.message, false);
        document.getElementById('register-form').reset();
    } else {
        showMessage('reg-msg', data.error, true);
    }
}

async function handleLoginSubmit(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    if (!email || !password) {
        showMessage('login-msg', 'Please enter both email and password.', true);
        return;
    }

    const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (res.ok) {
        showMessage('login-msg', 'Login successful! Redirecting...', false);
        setTimeout(() => { window.location.href = 'menu.html'; }, 1000);
    } else {
        showMessage('login-msg', data.error, true);
    }
}
""",

    "frontend/index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SpiceBite | Home - Online Restaurant & Food Ordering</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <nav class="navbar">
            <a href="index.html" class="logo">🌶️ SpiceBite</a>
            <ul class="nav-links">
                <li><a href="index.html" class="active">Home</a></li>
                <li><a href="menu.html">Menu & Order</a></li>
                <li><a href="about.html">About Us</a></li>
                <li><a href="contact.html">Contact</a></li>
                <li id="auth-link"><a href="login.html">Login / Register</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <section class="hero">
            <div class="hero-text">
                <h1>Delicious Food Delivered To Your Doorstep</h1>
                <p>Experience authentic flavors crafted by master chefs using fresh organic ingredients. Order online now for hot and fast delivery!</p>
                <a href="menu.html" class="btn">Explore Full Menu</a>
            </div>
            <div class="hero-image">
                <img src="https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=700&auto=format&fit=crop&q=80" alt="Delicious Restaurant Platter">
            </div>
        </section>

        <section>
            <h2 class="section-title">Popular Dishes</h2>
            <div id="featured-grid" class="grid-container"></div>
        </section>
    </main>

    <footer>
        <p>&copy; 2026 SpiceBite Restaurant. Designed & Developed for Web Development Assignment.</p>
    </footer>
    <script src="js/script.js"></script>
</body>
</html>
""",

    "frontend/menu.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SpiceBite | Food Menu & CRUD Management</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <nav class="navbar">
            <a href="index.html" class="logo">🌶️ SpiceBite</a>
            <ul class="nav-links">
                <li><a href="index.html">Home</a></li>
                <li><a href="menu.html" class="active">Menu & Order</a></li>
                <li><a href="about.html">About Us</a></li>
                <li><a href="contact.html">Contact</a></li>
                <li id="auth-link"><a href="login.html">Login / Register</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <section>
            <h1 class="section-title">Our Delicious Menu</h1>
            <div id="menu-grid" class="grid-container"></div>
        </section>

        <section class="form-container">
            <h2 class="section-title">Manage Menu Item (CRUD Operations)</h2>
            <div id="crud-msg" class="alert"></div>
            <form id="product-form" onsubmit="handleProductSubmit(event)">
                <input type="hidden" id="product-id">
                <div class="form-group">
                    <label for="food-name">Food Name *</label>
                    <input type="text" id="food-name" placeholder="e.g., Tandoori Chicken Pizza" required>
                </div>
                <div class="form-group">
                    <label for="food-category">Category *</label>
                    <select id="food-category" required>
                        <option value="Burger">Burger</option>
                        <option value="Pizza">Pizza</option>
                        <option value="Rice">Rice & Biryani</option>
                        <option value="Pasta">Pasta</option>
                        <option value="Snacks">Snacks</option>
                        <option value="Dessert">Dessert</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="food-price">Price (BDT ৳) *</label>
                    <input type="number" id="food-price" min="1" step="0.01" placeholder="350" required>
                </div>
                <div class="form-group">
                    <label for="food-image">Image URL (Optional)</label>
                    <input type="url" id="food-image" placeholder="https://images.unsplash.com/...">
                </div>
                <div class="form-group">
                    <label for="food-desc">Description *</label>
                    <textarea id="food-desc" rows="3" placeholder="Describe the ingredients and taste..." required></textarea>
                </div>
                <button type="submit" id="form-submit-btn" class="btn">Add Food Item</button>
            </form>
        </section>
    </main>

    <footer>
        <p>&copy; 2026 SpiceBite Restaurant. All Rights Reserved.</p>
    </footer>
    <script src="js/script.js"></script>
</body>
</html>
""",

    "frontend/about.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SpiceBite | About Us</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <nav class="navbar">
            <a href="index.html" class="logo">🌶️ SpiceBite</a>
            <ul class="nav-links">
                <li><a href="index.html">Home</a></li>
                <li><a href="menu.html">Menu & Order</a></li>
                <li><a href="about.html" class="active">About Us</a></li>
                <li><a href="contact.html">Contact</a></li>
                <li id="auth-link"><a href="login.html">Login / Register</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <section class="hero">
            <div class="hero-text">
                <h1>About SpiceBite Restaurant</h1>
                <p>Founded with a passion for authentic culinary artistry, SpiceBite brings farm-fresh ingredients and unforgettable recipes straight to your table. Whether you dine in or order online, quality and hygiene are our top priorities.</p>
            </div>
            <div class="hero-image">
                <img src="https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=700&auto=format&fit=crop&q=80" alt="Restaurant Interior">
            </div>
        </section>

        <section>
            <h2 class="section-title">Why Choose Us?</h2>
            <div class="grid-container">
                <article class="card">
                    <div class="card-body">
                        <h3>🥗 100% Fresh Ingredients</h3>
                        <p>We source local organic vegetables and premium cuts of meat daily to ensure maximum flavor and nutrition.</p>
                    </div>
                </article>
                <article class="card">
                    <div class="card-body">
                        <h3>👨‍🍳 Master Culinary Chefs</h3>
                        <p>Our kitchen is led by experienced chefs specializing in Continental, Italian, and South Asian delicacies.</p>
                    </div>
                </article>
                <article class="card">
                    <div class="card-body">
                        <h3>🚀 Super Fast Delivery</h3>
                        <p>Hot and fresh meals delivered to your doorstep within 30–45 minutes of placing your online order.</p>
                    </div>
                </article>
            </div>
        </section>
    </main>

    <footer>
        <p>&copy; 2026 SpiceBite Restaurant. All Rights Reserved.</p>
    </footer>
    <script src="js/script.js"></script>
</body>
</html>
""",

    "frontend/contact.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SpiceBite | Contact & Feedback</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <nav class="navbar">
            <a href="index.html" class="logo">🌶️ SpiceBite</a>
            <ul class="nav-links">
                <li><a href="index.html">Home</a></li>
                <li><a href="menu.html">Menu & Order</a></li>
                <li><a href="about.html">About Us</a></li>
                <li><a href="contact.html" class="active">Contact</a></li>
                <li id="auth-link"><a href="login.html">Login / Register</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <section class="form-container">
            <h1 class="section-title">Contact Us / Send Feedback</h1>
            <p style="text-align:center; margin-bottom: 1.5rem;">Have a question or feedback? Fill out the form below and it will be saved directly to our database.</p>
            <div id="contact-msg" class="alert"></div>
            <form id="contact-form" onsubmit="handleContactSubmit(event)" novalidate>
                <div class="form-group">
                    <label for="contact-name">Your Name *</label>
                    <input type="text" id="contact-name" placeholder="Enter your full name" required>
                </div>
                <div class="form-group">
                    <label for="contact-email">Your Email *</label>
                    <input type="email" id="contact-email" placeholder="example@mail.com" required>
                </div>
                <div class="form-group">
                    <label for="contact-message">Your Message / Feedback *</label>
                    <textarea id="contact-message" rows="4" placeholder="Write at least 10 characters..." required></textarea>
                </div>
                <button type="submit" class="btn">Send Message</button>
            </form>
        </section>
    </main>

    <footer>
        <p>&copy; 2026 SpiceBite Restaurant. All Rights Reserved.</p>
    </footer>
    <script src="js/script.js"></script>
</body>
</html>
""",

    "frontend/login.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SpiceBite | Login & Registration</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <nav class="navbar">
            <a href="index.html" class="logo">🌶️ SpiceBite</a>
            <ul class="nav-links">
                <li><a href="index.html">Home</a></li>
                <li><a href="menu.html">Menu & Order</a></li>
                <li><a href="about.html">About Us</a></li>
                <li><a href="contact.html">Contact</a></li>
                <li id="auth-link"><a href="login.html" class="active">Login / Register</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <h1 class="section-title">User Authentication</h1>
        <section class="auth-wrapper">
            <article class="form-container" style="margin: 0;">
                <h2>Login to Account</h2>
                <div id="login-msg" class="alert"></div>
                <form id="login-form" onsubmit="handleLoginSubmit(event)" novalidate>
                    <div class="form-group">
                        <label for="login-email">Email Address *</label>
                        <input type="email" id="login-email" placeholder="Enter registered email" required>
                    </div>
                    <div class="form-group">
                        <label for="login-password">Password *</label>
                        <input type="password" id="login-password" placeholder="Enter password" required>
                    </div>
                    <button type="submit" class="btn">Login</button>
                </form>
            </article>

            <article class="form-container" style="margin: 0;">
                <h2>New User Registration</h2>
                <div id="reg-msg" class="alert"></div>
                <form id="register-form" onsubmit="handleRegisterSubmit(event)" novalidate>
                    <div class="form-group">
                        <label for="reg-name">Full Name *</label>
                        <input type="text" id="reg-name" placeholder="Minimum 3 characters" required>
                    </div>
                    <div class="form-group">
                        <label for="reg-email">Email Address *</label>
                        <input type="email" id="reg-email" placeholder="valid@email.com" required>
                    </div>
                    <div class="form-group">
                        <label for="reg-password">Password *</label>
                        <input type="password" id="reg-password" placeholder="Minimum 6 characters" required>
                    </div>
                    <button type="submit" class="btn">Register Now</button>
                </form>
            </article>
        </section>
    </main>

    <footer>
        <p>&copy; 2026 SpiceBite Restaurant. All Rights Reserved.</p>
    </footer>
    <script src="js/script.js"></script>
</body>
</html>
"""
}

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ All folders and files have been created successfully!")
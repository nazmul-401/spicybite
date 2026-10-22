from flask import Flask, request, jsonify, session, send_from_directory
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

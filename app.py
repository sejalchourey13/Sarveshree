from flask import Flask, render_template, request, redirect, url_for, session, jsonify,flash
import sqlite3
from datetime import datetime
import json
import razorpay
import os
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.permanent_session_lifetime = timedelta(days=7)

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)



def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    products TEXT,
                    quantity INTEGER,
                    total TEXT,
                    payment_method TEXT,
                    payment_screenshot TEXT,
                    razorpay_order_id TEXT,
                    razorpay_payment_id TEXT,
                    razorpay_signature TEXT,
                    payment_status TEXT,
                    date TEXT
                )''')
    conn.commit()
    conn.close()


init_db()  # Ensure DB and table exist

def init_users_table():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT UNIQUE,
                    phone TEXT,
                    password TEXT
                )''')
    
    
    conn.commit()
    conn.close()
    
init_users_table()

# Temporary storage for orders (in-memory list)
orders = []

@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        # password = request.form['password']

        conn = sqlite3.connect('orders.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (name, email, phone) VALUES (?, ?, ?)",
                      (name, email, phone))
            conn.commit()
            conn.close()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return "⚠️ This email is already registered!"
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']

        if role == 'user':
            email = request.form['email']
            phone = request.form['phone']
            # password = request.form['password']
            conn = sqlite3.connect('orders.db')
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE email=? AND phone=?", (email, phone))
            user = c.fetchone()
            conn.close()

            if user:
                # ✅ Permanent session enable
                session.permanent = True
                session.clear()  # pehle ka data hata do
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                # session['cart'] = []
                return redirect('/index')
            else:
                return "❌ Invalid User Credentials!"

        elif role == 'admin':
            password = request.form['password']
            if password == "admin123":
                session['admin'] = True
                return redirect('/admin_orders')
            else:
                return "🚫 Invalid Admin Credentials!"
            
    # agar already login hai to direct redirect kar do
    if 'user_id' in session:
        return redirect('/index')
    if 'admin' in session:
        return redirect('/admin_orders')
    
    return render_template('login.html')

@app.route('/index')
def index():
    if 'user_id' in session:
        return render_template('index.html', user_name=session['user_name'])
    else:
        return redirect('/login')

# Admin Login Route
@app.route('/login_admin', methods=['POST'])
def login_admin():
    username = request.form['username']
    password = request.form['password']

    # Static admin credentials
    if username == "admin" and password == "admin123":
        session['admin'] = True
        return redirect('/admin_orders')  # admin -> admin dashboard
    else:
        return "🚫 Invalid Admin credentials!"

@app.route('/admin_orders')
def admin_orders():
    if 'admin' not in session:
        return redirect('/login')
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = c.fetchall()
    conn.close()
    return render_template('admin_orders.html', orders=orders)

# Add to Cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Login required"}), 401

    user_id = session['user_id']
    product_name = request.form.get('name')
    product_price = request.form.get('price')

    if not product_name or not product_price:
        return jsonify({"success": False, "message": "Invalid product data"}), 400

    conn = sqlite3.connect('orders.db')
    c = conn.cursor()

    # Check if product already exists in cart
    c.execute('SELECT id, quantity FROM cart WHERE user_id = ? AND product_name = ?', (user_id, product_name))
    existing = c.fetchone()

    if existing:
        c.execute('UPDATE cart SET quantity = quantity + 1 WHERE id = ?', (existing[0],))
    else:
        c.execute('INSERT INTO cart (user_id, product_name, product_price, quantity) VALUES (?, ?, ?, ?)',
                  (user_id, product_name, float(product_price), 1))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"{product_name} added to cart!"})



@app.route('/cart')
def view_cart():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # c.execute('SELECT * FROM cart WHERE user_id = ?', (user_id,))
    c.execute('SELECT id, product_name, product_price, quantity FROM cart WHERE user_id = ?', (user_id,))
    cart = c.fetchall()

    total = sum(row['product_price'] * row['quantity'] for row in cart)
    conn.close()

    return render_template('cart.html', cart=cart, total=total)

# Remove Item from Cart
@app.route('/remove_from_cart/<int:item_id>')
def remove_from_cart(item_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_cart'))


# Increase Quantity
@app.route('/increase_quantity/<int:item_id>')
def increase_quantity(item_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE cart SET quantity = quantity + 1 WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_cart'))

# Decrease Quantity
@app.route('/decrease_quantity/<int:item_id>')
def decrease_quantity(item_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()

    # Decrease only if quantity > 1
    cursor.execute("SELECT quantity FROM cart WHERE id = ?", (item_id,))
    qty = cursor.fetchone()
    if qty and qty[0] > 1:
        cursor.execute("UPDATE cart SET quantity = quantity - 1 WHERE id = ?", (item_id,))
    else:
        # If quantity = 1, remove item
        cursor.execute("DELETE FROM cart WHERE id = ?", (item_id,))

    conn.commit()
    conn.close()
    return redirect(url_for('view_cart'))


import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/place_order', methods=['POST'])
def place_order():
    
    # get the logged in user's id
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect('/login')
    
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    products = request.form.get('products')
    quantity = request.form.get('quantity', 1)
    # price_per_unit = float(request.form.get('price'))
    price_per_unit = request.form.get('price') or request.form.get('product_price')
    total = request.form.get('total')
    payment_method = request.form.get('payment_method')

    # --- handle screenshot upload ---
    screenshot_file = request.files.get('payment_screenshot')
    screenshot_path = None
    if screenshot_file and screenshot_file.filename:
        filename = secure_filename(screenshot_file.filename)
        file_save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        screenshot_file.save(file_save_path)
        
        screenshot_path = f"/static/uploads/{filename}"

    # timestamp
    order_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- insert into DB (column order must match init_db()) ---
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''INSERT INTO orders
        (name, phone, email, address, products,quantity,price_per_unit, total, payment_method, payment_screenshot,
         razorpay_order_id, razorpay_payment_id, razorpay_signature, payment_status, date, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?)''',
        (name, phone, email, address, products, quantity,price_per_unit,
         f"{products} (x{quantity}) @ ₹{price_per_unit}", payment_method,
         screenshot_path, None, None, None, None, order_datetime, user_id))
    conn.commit()
    conn.close()

    # clear cart
    session.pop('cart', None)

    order = {
        "name": name,
        "phone": phone,
        "email": email,
        "address": address,
        "products": products,
        "quantity": quantity,
        "price_per_unit": price_per_unit,
        "total": total,
        "payment_method": payment_method,
        "payment_screenshot": screenshot_path,
        "date": order_datetime,
        "user_id":user_id
    }

    print("\n📦 New Order Received:")
    print(order)

    return render_template('success.html', order=order)

@app.route('/my_orders')
def my_orders():
    # check if user is logged in
    if 'user_id' not in session:
        return redirect('/login')

    user_id = int(session['user_id'])

    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute("SELECT id, products, quantity, price_per_unit, payment_method, date, payment_screenshot FROM orders WHERE user_id = ?ORDER BY id DESC", (user_id,))
    orders = c.fetchall()
    conn.close()

    # Convert to list of dicts for template
    # ✅ Calculate total dynamically and prepare list for template
    orders_data = []
    for order in orders:
        order_id, products, quantity, price_per_unit, payment_method, date, payment_screenshot = order
        try:
            total = int(quantity) * float(price_per_unit)
        except (TypeError, ValueError):
            total = 0  # <-- 👈 formula here
        orders_data.append({
            "id": order_id,
            "products": products,
            "quantity": quantity,
            "price_per_unit": price_per_unit,
            "total": total,
            "payment_method": payment_method,
            "date": date,
            "payment_screenshot": payment_screenshot
        })

    # ✅ Pass processed orders to template
    return render_template('my_orders.html', orders=orders_data)

@app.route('/place_cart_order', methods=['POST'])
def place_cart_order():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    name = request.form['name']
    address = request.form['address']
    products = request.form.get('products')
    price_per_unit = request.form.get('price') or request.form.get('product_price')
    payment_method = request.form['payment_method']
    phone = request.form.get('phone')
    email = request.form.get('email')
    payment_status = "Pending"

    # conn = sqlite3.connect('orders.db')
    # cursor = conn.cursor()
    
    # --- handle screenshot upload ---
    screenshot_file = request.files.get('payment_screenshot')
    screenshot_path = None
    if screenshot_file and screenshot_file.filename:
        filename = secure_filename(screenshot_file.filename)
        file_save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        screenshot_file.save(file_save_path)
        
        screenshot_path = f"/static/uploads/{filename}"
    
    # order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    # Get all cart items for the user
    cursor.execute('SELECT id, product_name, product_price, quantity FROM cart WHERE user_id = ?', (user_id,))
    cart_items = cursor.fetchall()

    if not cart_items:
        conn.close()
        flash("Your cart is empty!", "warning")
        return redirect(url_for('view_cart'))

    # Insert each cart item as an order
    for item in cart_items:
        _, products, price_per_unit, quantity = item
        total = price_per_unit * quantity
        order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
        cursor.execute("""
            INSERT INTO orders (user_id, name, address, products, price_per_unit, quantity, total, payment_method,payment_status, payment_screenshot,date,phone, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?)""",
            (user_id, name, address, products, price_per_unit, quantity, 
            f"(x{quantity}) @ ₹{price_per_unit}", payment_method,payment_status, screenshot_path,order_date,phone, email)
        )

    # Clear the cart
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash("Order placed successfully!", "success")
    return redirect(url_for('my_orders'))


@app.route('/check_orders')
def check_orders():
    import sqlite3
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, payment_screenshot FROM orders")
    data = cursor.fetchall()
    conn.close()
    return {'orders': data}

# ✅ Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)

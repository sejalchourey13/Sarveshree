import sqlite3

conn = sqlite3.connect('orders.db')
cursor = conn.cursor()

cursor.execute('DROP TABLE IF EXISTS orders')

cursor.execute('''
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    products TEXT,
    total TEXT,
    payment_method TEXT,
    payment_screenshot TEXT,
    razorpay_order_id TEXT,
    razorpay_payment_id TEXT,
    razorpay_signature TEXT,
    payment_status TEXT,
    date TEXT
)
''')

conn.commit()
conn.close()

print("✅ Database recreated successfully with all correct columns!")

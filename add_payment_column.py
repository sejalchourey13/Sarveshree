import sqlite3
conn = sqlite3.connect('orders.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(orders);")
print(cursor.fetchall())
conn.close()

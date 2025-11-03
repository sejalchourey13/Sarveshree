import sqlite3

conn = sqlite3.connect('orders.db')
c = conn.cursor()
c.execute("PRAGMA table_info(orders)")
for col in c.fetchall():
    print(col)
conn.close()

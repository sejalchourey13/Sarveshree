import sqlite3

# Step 1: Connect to the database
conn = sqlite3.connect('orders.db')  # make sure orders.db is in same folder
c = conn.cursor()

# Step 2: Fetch all orders
c.execute("SELECT * FROM orders")
all_orders = c.fetchall()

# Step 3: Print orders nicely
print("\n📦 All Orders:")
for order in all_orders:
    print(f"ID: {order[0]}")
    print(f"Name: {order[1]}")
    print(f"Phone: {order[2]}")
    print(f"Email: {order[3]}")
    print(f"Address: {order[4]}")
    print(f"Products: {order[5]}")
    print(f"Total: {order[6]}")
    print("-" * 40)

# Step 4: Close the connection
conn.close()

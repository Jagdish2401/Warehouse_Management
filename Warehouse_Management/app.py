from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
import matplotlib.pyplot as plt
import io
import base64


app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages

# Database Path
DB_PATH = "data/inventory.db"

# Ensure database exists
if not os.path.exists("data"):
    os.makedirs("data")

# Create database table if it doesn't exist
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL
            )
        ''')
        conn.commit()

init_db()

# Home Route
@app.route('/')
def home():
    return render_template('index.html')

# View Inventory with Search, Low Stock Alert, and Sorting
@app.route('/inventory')
def inventory():
    sort_order = request.args.get('sort', 'asc')  # Default to ascending
    search_query = request.args.get('search', '').strip()
    order_by = "ASC" if sort_order == "asc" else "DESC"

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if search_query:
            cursor.execute(f"SELECT * FROM products WHERE name LIKE ? ORDER BY price {order_by}", (f"%{search_query}%",))
        else:
            cursor.execute(f"SELECT * FROM products ORDER BY price {order_by}")
        products = cursor.fetchall()

        # Identify low stock products (threshold: 5)
        low_stock_products = [p for p in products if p[2] < 5]  # p[2] is quantity
        if low_stock_products:
            flash("⚠️ Some products are running low on stock!", "warning")

    return render_template('inventory.html', products=products, sort_order=sort_order, search_query=search_query)

# Add Product Route (Prevents Duplicates & Updates Quantity)
@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name'].strip().lower()  # Normalize input
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])

        if not name or quantity <= 0 or price <= 0:
            flash("All fields are required, and values must be greater than zero!", "danger")
            return redirect(url_for('add_product'))

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Check if the product already exists
            cursor.execute("SELECT id, quantity FROM products WHERE LOWER(name) = ?", (name,))
            existing_product = cursor.fetchone()

            if existing_product:
                # If product exists, update its quantity
                new_quantity = existing_product[1] + quantity
                cursor.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_quantity, existing_product[0]))
                flash(f"Updated {name}'s quantity to {new_quantity}.", "success")
            else:
                # Otherwise, add as a new product
                cursor.execute("INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)", (name, quantity, price))
                flash("Product added successfully!", "success")

            conn.commit()

        return redirect(url_for('inventory'))

    return render_template('add_product.html')

# Update Product Route
@app.route('/update/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()

        if not product:
            flash("Product not found!", "danger")
            return redirect(url_for('inventory'))

    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET name=?, quantity=?, price=? WHERE id=?", (name, quantity, price, product_id))
            conn.commit()

        flash("Product updated successfully!", "success")
        return redirect(url_for('inventory'))

    return render_template('update_product.html', product=product)

# Delete Product Route
@app.route('/delete/<int:product_id>')
def delete_product(product_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()

    flash("Product deleted successfully!", "success")
    return redirect(url_for('inventory'))

# Manage Products Route
@app.route('/manage')
def manage_products():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
    return render_template('manage.html', products=products)

# Generate inventory graph
def generate_chart():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, quantity FROM products")
        data = cursor.fetchall()

    if not data:
        return None  # No data available

    names = [row[0] for row in data]
    quantities = [row[1] for row in data]

    plt.figure(figsize=(10, max(5, len(names) * 0.5)))  # Dynamically adjust height
    plt.bar(names, quantities, color='royalblue')  # Vertical bars instead of horizontal
    plt.xlabel("Products")
    plt.ylabel("Quantity")
    plt.title("Warehouse Inventory Levels")
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Save the plot to a BytesIO buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches="tight")  # Prevent overlap
    buf.seek(0)
    graph_url = base64.b64encode(buf.getvalue()).decode('utf8')
    plt.close()

    return f"data:image/png;base64,{graph_url}"

# Route to show the chart
@app.route('/graph')
def graph():
    graph_url = generate_chart()
    return render_template('graph.html', graph_url=graph_url)

if __name__ == '__main__':
    app.run(debug=True)

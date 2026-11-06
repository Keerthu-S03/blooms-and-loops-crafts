import os
import sqlite3
from pathlib import Path
from functools import wraps

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)

from flask_wtf.csrf import CSRFProtect
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# --------------------------------
# FLASK CONFIGURATION
# --------------------------------

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-only-change-this-key"
)

csrf = CSRFProtect(app)

DB_PATH = Path(__file__).resolve().parent / "crafts.db"


# --------------------------------
# PRODUCT DETAILS
# --------------------------------

PRODUCTS = [
    {
        "id": 1,
        "name": "Pipe Cleaner Tulip Bouquet",
        "category": "Pipe Cleaner",
        "price": 299,
        "description": "Colourful handmade tulips arranged as a gift bouquet.",
        "emoji": "🌷",
        "image": "tulip.jpg"
    },
    {
        "id": 2,
        "name": "Pipe Cleaner Daisy Bouquet",
        "category": "Pipe Cleaner",
        "price": 399,
        "description": "Beautiful handmade daisy flowers.",
        "emoji": "🌼",
        "image": "daisy_flower.jpg"
    },
    {
        "id": 3,
        "name": "Crochet Flower Keychain",
        "category": "Crochet",
        "price": 129,
        "description": "A cute handmade flower accessory.",
        "emoji": "🌸",
        "image": "key.jpg"
    },
    {
        "id": 4,
        "name": "Pipe Cleaner Rose and Sunflower",
        "category": "Pipe Cleaner",
        "price": 99,
        "description": "A handmade rose for a thoughtful gift.",
        "emoji": "🌹",
        "image": "rose.jpg"
    },
    {
        "id": 5,
        "name": "Crochet Mini Plushie",
        "category": "Crochet",
        "price": 249,
        "description": "A small handmade crochet creation.",
        "emoji": "🧸",
        "image": "crochet_plushie.jpg"
    },
    {
        "id": 6,
        "name": "Custom Flower Bouquet",
        "category": "Custom",
        "price": 499,
        "description": "A customised bouquet with your preferred colours.",
        "emoji": "💐",
        "image": "custom_bouquet.jpg"
    },
    {
        "id": 7,
        "name": "Pipe Cleaner Flower Pot",
        "category": "Pipe Cleaner",
        "price": 299,
        "description": "A beautiful handmade flower pot.",
        "emoji": "🪴",
        "image": "flower_pot.jpg"
    },
    {
        "id": 8,
        "name": "Pipe Cleaner Flower Frame",
        "category": "Pipe Cleaner",
        "price": 349,
        "description": "A colourful handmade flower frame.",
        "emoji": "🌸",
        "image": "flower_frame.jpg"
    },
    {
        "id": 9,
        "name": "Crochet Bouquet",
        "category": "Crochet",
        "price": 499,
        "description": "A beautiful handmade crochet bouquet.",
        "emoji": "💐",
        "image": "crochet_bouquet.jpg"
    },
    {
        "id": 10,
        "name": "Crochet Hair Clip",
        "category": "Crochet",
        "price": 149,
        "description": "A cute handmade crochet flower hair clip.",
        "emoji": "🌸",
        "image": "crochet_hairclip.jpg"
    }
]


# --------------------------------
# DATABASE CONNECTION
# --------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# --------------------------------
# CREATE DATABASE TABLES
# --------------------------------

def init_db():

    with get_db() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                customer_name TEXT NOT NULL,
                email TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL DEFAULT 0,
                notes TEXT,
                payment_method TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)

        columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(orders)"
            ).fetchall()
        }

        migrations = {
            "customer_id": "INTEGER",
            "price": "REAL DEFAULT 0",
            "created_at": "TEXT",
            "payment_method": "TEXT DEFAULT 'COD'",
            "notes": "TEXT",
            "status": "TEXT DEFAULT 'Pending'"
        }

        for column, definition in migrations.items():
            if column not in columns:
                conn.execute(
                    f"ALTER TABLE orders ADD COLUMN {column} {definition}"
                )

        conn.execute("""
            UPDATE orders
            SET created_at = CURRENT_TIMESTAMP
            WHERE created_at IS NULL
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS customer_addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER UNIQUE NOT NULL,
                recipient_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address_line TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                pincode TEXT NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)


# --------------------------------
# CUSTOMER LOGIN PROTECTION
# --------------------------------

def customer_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "customer_id" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# --------------------------------
# CUSTOMER LOGIN
# --------------------------------

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():

    if "customer_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get("password", "")

        with get_db() as conn:

            customer = conn.execute(
                "SELECT * FROM customers WHERE email = ?",
                (email,)
            ).fetchone()

        if customer and check_password_hash(
            customer["password"], password
        ):

            session.clear()
            session["customer_id"] = customer["id"]
            session["customer_email"] = customer["email"]

            return redirect(url_for("home"))

        flash("Invalid email or password.")

    return render_template("login.html")


# --------------------------------
# CUSTOMER REGISTRATION
# --------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if "customer_id" in session:
        return redirect(url_for("home"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if (
            not name
            or len(name) > 100
            or not email
            or len(email) > 254
            or "@" not in email
            or len(password) < 8
        ):

            flash(
                "Enter valid details. Password must be at least 8 characters."
            )

            return render_template("register.html")

        hashed_password = generate_password_hash(password)

        try:

            with get_db() as conn:

                conn.execute("""
                    INSERT INTO customers
                    (name, email, password)
                    VALUES (?, ?, ?)
                """, (name, email, hashed_password))

            flash("Account created successfully! Please login.")

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash("This email is already registered.")

    return render_template("register.html")


# --------------------------------
# CUSTOMER LOGOUT
# --------------------------------

@app.route("/customer-logout", methods=["POST"])
@customer_required
def customer_logout():

    session.clear()

    return redirect(url_for("login"))


# --------------------------------
# HOME PAGE
# --------------------------------

@app.route("/home")
@customer_required
def home():

    return render_template(
        "index.html",
        products=PRODUCTS[:3]
    )


# --------------------------------
# PRODUCTS PAGE
# --------------------------------

@app.route("/products")
@customer_required
def products():

    categories = [
        "All", "Pipe Cleaner", "Crochet", "Custom"
    ]

    category = request.args.get("category", "All")

    if category not in categories:
        category = "All"

    filtered = [
        p for p in PRODUCTS
        if category == "All" or p["category"] == category
    ]

    price_range = request.args.get("price_range", "").strip()

    if price_range:

        try:

            if price_range.endswith("+"):

                minimum = float(price_range[:-1])

                filtered = [
                    p for p in filtered
                    if p["price"] >= minimum
                ]

            elif "-" in price_range:

                minimum, maximum = map(
                    float, price_range.split("-", 1)
                )

                filtered = [
                    p for p in filtered
                    if minimum <= p["price"] <= maximum
                ]

        except ValueError:
            pass

    return render_template(
        "products.html",
        products=filtered,
        categories=categories,
        selected_category=category
    )


# --------------------------------
# ORDER PAGE
# --------------------------------

@app.route("/order", methods=["GET", "POST"])
@customer_required
def order():

    product_id = request.args.get("product", type=int)

    selected = next(
        (p for p in PRODUCTS if p["id"] == product_id),
        None
    )

    if request.method == "POST":

        name = request.form.get(
            "customer_name", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip().lower()

        product_name = request.form.get(
            "product_name", ""
        ).strip()

        quantity_text = request.form.get(
            "quantity", "1"
        ).strip()

        notes = request.form.get(
            "notes", ""
        ).strip()

        payment_method = request.form.get(
            "payment_method", ""
        ).strip()

        try:
            quantity = int(quantity_text)
        except (TypeError, ValueError):
            quantity = 0

        product = next(
            (p for p in PRODUCTS if p["name"] == product_name),
            None
        )

        if (
            not name
            or len(name) > 100
            or not email
            or len(email) > 254
            or "@" not in email
            or not product
            or not 1 <= quantity <= 20
            or len(notes) > 1000
            or payment_method not in ("COD", "ONLINE")
        ):

            flash("Please check your details and try again.")

        else:

            with get_db() as conn:

                conn.execute("""
                    INSERT INTO orders (
                        customer_id,
                        customer_name,
                        email,
                        product_name,
                        quantity,
                        price,
                        notes,
                        payment_method,
                        status,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    session["customer_id"],
                    name,
                    email,
                    product_name,
                    quantity,
                    product["price"],
                    notes,
                    payment_method,
                    "Pending"
                ))

            flash("Your order request has been saved!")

            return redirect(url_for("my_orders"))

    return render_template(
        "order.html",
        products=PRODUCTS,
        selected=selected
    )


# --------------------------------
# MY ORDERS
# --------------------------------

@app.route("/my-orders")
@customer_required
def my_orders():

    with get_db() as conn:

        orders = conn.execute("""
            SELECT *
            FROM orders
            WHERE customer_id = ?
            ORDER BY id DESC
        """, (session["customer_id"],)).fetchall()

    return render_template(
        "my_orders.html",
        orders=orders
    )


# --------------------------------
# CANCEL CUSTOMER ORDER
# --------------------------------

@app.route("/cancel-order/<int:order_id>", methods=["POST"])
@customer_required
def cancel_order(order_id):

    with get_db() as conn:

        order_record = conn.execute("""
            SELECT * FROM orders
            WHERE id = ? AND customer_id = ?
        """, (
            order_id,
            session["customer_id"]
        )).fetchone()

        if not order_record:

            flash("Order not found.")

            return redirect(url_for("my_orders"))

        if order_record["status"] not in ["Pending", "Confirmed"]:

            flash("This order can no longer be cancelled.")

            return redirect(url_for("my_orders"))

        conn.execute("""
            UPDATE orders
            SET status = 'Cancelled'
            WHERE id = ? AND customer_id = ?
        """, (
            order_id,
            session["customer_id"]
        ))

    flash("Your order has been cancelled successfully!")

    return redirect(url_for("my_orders"))


# --------------------------------
# ABOUT PAGE
# --------------------------------

@app.route("/about")
@customer_required
def about():

    return render_template("about.html")


# --------------------------------
# CONTACT PAGE
# --------------------------------

@app.route("/contact")
@customer_required
def contact():

    return render_template("contact.html")


# --------------------------------
# ADD TO CART
# --------------------------------

@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
@customer_required
def add_to_cart(product_id):

    if not any(p["id"] == product_id for p in PRODUCTS):

        flash("Product not found.")

        return redirect(url_for("products"))

    cart = session.get("cart", {})

    key = str(product_id)

    current_quantity = cart.get(key, 0)

    if not isinstance(current_quantity, int):
        current_quantity = 0

    if current_quantity >= 20:

        flash("Maximum quantity is 20.")

    else:

        cart[key] = current_quantity + 1

        session["cart"] = cart

        flash("Product added to cart!")

    return redirect(url_for("cart"))


# --------------------------------
# SHOPPING CART
# --------------------------------

@app.route("/cart")
@customer_required
def cart():

    cart_items = []
    total = 0
    total_items = 0

    for product_id, quantity in session.get("cart", {}).items():

        product = next(
            (
                p for p in PRODUCTS
                if str(p["id"]) == str(product_id)
            ),
            None
        )

        if product and isinstance(quantity, int) and 1 <= quantity <= 20:

            item_total = product["price"] * quantity

            total += item_total
            total_items += quantity

            cart_items.append({
                "product": product,
                "quantity": quantity,
                "item_total": item_total
            })

    with get_db() as conn:

        address = conn.execute("""
            SELECT * FROM customer_addresses
            WHERE customer_id = ?
        """, (session["customer_id"],)).fetchone()

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total,
        total_items=total_items,
        address=address
    )


# --------------------------------
# SAVE CUSTOMER ADDRESS
# --------------------------------

@app.route("/add-address", methods=["POST"])
@customer_required
def add_address():

    recipient_name = request.form.get(
        "recipient_name", ""
    ).strip()

    phone = request.form.get(
        "phone", ""
    ).strip()

    address_line = request.form.get(
        "address_line", ""
    ).strip()

    city = request.form.get("city", "").strip()

    state = request.form.get("state", "").strip()

    pincode = request.form.get("pincode", "").strip()

    if (
        not recipient_name
        or len(recipient_name) > 100
        or len(phone) != 10
        or not phone.isdigit()
        or not address_line
        or len(address_line) > 300
        or not city
        or len(city) > 100
        or not state
        or len(state) > 100
        or not pincode.isdigit()
        or len(pincode) != 6
    ):

        flash("Please enter valid delivery address details.")

        return redirect(url_for("cart"))

    with get_db() as conn:

        existing = conn.execute("""
            SELECT id FROM customer_addresses
            WHERE customer_id = ?
        """, (session["customer_id"],)).fetchone()

        if existing:

            conn.execute("""
                UPDATE customer_addresses
                SET recipient_name = ?,
                    phone = ?,
                    address_line = ?,
                    city = ?,
                    state = ?,
                    pincode = ?
                WHERE customer_id = ?
            """, (
                recipient_name,
                phone,
                address_line,
                city,
                state,
                pincode,
                session["customer_id"]
            ))

        else:

            conn.execute("""
                INSERT INTO customer_addresses (
                    customer_id,
                    recipient_name,
                    phone,
                    address_line,
                    city,
                    state,
                    pincode
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session["customer_id"],
                recipient_name,
                phone,
                address_line,
                city,
                state,
                pincode
            ))

    flash("Delivery address saved successfully!")

    return redirect(url_for("cart"))


# --------------------------------
# UPDATE CART QUANTITY
# --------------------------------

@app.route("/update_cart/<int:product_id>", methods=["POST"])
@customer_required
def update_cart(product_id):

    cart = session.get("cart", {})

    key = str(product_id)

    action = request.form.get("action")

    if key in cart and isinstance(cart[key], int):

        if action == "increase":

            if cart[key] < 20:
                cart[key] += 1
            else:
                flash("Maximum quantity is 20.")

        elif action == "decrease":

            cart[key] -= 1

            if cart[key] <= 0:
                cart.pop(key)

    session["cart"] = cart

    return redirect(url_for("cart"))


# --------------------------------
# REMOVE PRODUCT FROM CART
# --------------------------------

@app.route("/remove_from_cart/<int:product_id>", methods=["POST"])
@customer_required
def remove_from_cart(product_id):

    cart = session.get("cart", {})

    cart.pop(str(product_id), None)

    session["cart"] = cart

    flash("Product removed from cart.")

    return redirect(url_for("cart"))

# --------------------------------
# PLACE ORDER FROM CART
# --------------------------------

@app.route("/place-order", methods=["POST"])
@customer_required
def place_order():

    cart = session.get("cart", {})

    if not cart:
        flash("Your cart is empty.")
        return redirect(url_for("cart"))

    with get_db() as conn:

        address = conn.execute("""
            SELECT * FROM customer_addresses
            WHERE customer_id = ?
        """, (session["customer_id"],)).fetchone()

        if not address:
            flash("Please add your delivery address first.")
            return redirect(url_for("cart"))

        for product_id, quantity in cart.items():

            product = next(
                (
                    p for p in PRODUCTS
                    if str(p["id"]) == str(product_id)
                ),
                None
            )

            if not product or not isinstance(quantity, int) or not 1 <= quantity <= 20:
                flash("Invalid cart item.")
                return redirect(url_for("cart"))

            conn.execute("""
                INSERT INTO orders (
                    customer_id,
                    customer_name,
                    email,
                    product_name,
                    quantity,
                    price,
                    notes,
                    payment_method,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                session["customer_id"],
                address["recipient_name"],
                session.get("customer_email", ""),
                product["name"],
                quantity,
                product["price"],
                "",
                "COD",
                "Pending"
            ))

    session["cart"] = {}

    flash("Your order has been placed successfully!")

    return redirect(url_for("my_orders"))


# --------------------------------
# RUN APPLICATION
# --------------------------------

if __name__ == "__main__":

    init_db()

    app.run(debug=True)
import pandas as pd
import datetime
from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String, Float, ForeignKey, Date
)


def create_db():
    # Create a persistent SQLite database in a file
    engine = create_engine("sqlite:///electrical_parts.db", echo=True)
    metadata = MetaData()

    # 1. Define suppliers table
    suppliers = Table(
        "suppliers", metadata,
        Column("supplier_id", Integer, primary_key=True, autoincrement=True),
        Column("name", String, nullable=False),
        Column("contact_name", String),
        Column("phone", String),
        Column("address", String)
    )

    # 2. Define categories table
    categories = Table(
        "categories", metadata,
        Column("category_id", Integer, primary_key=True, autoincrement=True),
        Column("name", String, nullable=False)
    )

    # 3. Define products table
    products = Table(
        "products", metadata,
        Column("product_id", Integer, primary_key=True, autoincrement=True),
        Column("name", String, nullable=False),
        Column("category_id", Integer, ForeignKey("categories.category_id")),
        Column("supplier_id", Integer, ForeignKey("suppliers.supplier_id")),
        Column("price", Float),
        Column("stock_quantity", Integer)
    )

    # 4. Define customers table
    customers = Table(
        "customers", metadata,
        Column("customer_id", Integer, primary_key=True, autoincrement=True),
        Column("name", String, nullable=False),
        Column("email", String, unique=True),
        Column("phone", String),
        Column("address", String),
        Column("state",String)
    )

    # 5. Define orders table
    orders = Table(
        "orders", metadata,
        Column("order_id", Integer, primary_key=True, autoincrement=True),
        Column("customer_id", Integer, ForeignKey("customers.customer_id")),
        Column("order_date", Date),
        Column("total_amount", Float)
    )

    # 6. Define order_items table
    order_items = Table(
        "order_items", metadata,
        Column("order_item_id", Integer, primary_key=True, autoincrement=True),
        Column("order_id", Integer, ForeignKey("orders.order_id")),
        Column("product_id", Integer, ForeignKey("products.product_id")),
        Column("quantity", Integer),
        Column("unit_price", Float)
    )

    # 7. Define taxes table with state as the primary key
    taxes = Table(
    "taxes", metadata,
    Column("state", String, primary_key=True, nullable=False),  # Use state as the primary key
    Column("tax_rate", Float, nullable=False)  # Store tax rate as a percentage (e.g., 0.07 for 7%)
)


    # Create all tables
    metadata.create_all(engine)

    # Insert initial data
    with engine.begin() as conn:
        conn.execute(suppliers.insert(), [
            {"name": "ElectroSupply Inc.", "contact_name": "John Doe", "phone": "555-1234", "address": "123 Electric Ave"},
            {"name": "Voltage Solutions", "contact_name": "Jane Smith", "phone": "555-5678", "address": "456 Current St"},
            {"name": "Wattage Wholesale", "contact_name": "Mike Johnson", "phone": "555-9101", "address": "789 Circuit Rd"}
        ])

        conn.execute(categories.insert(), [
            {"name": "Wires & Cables"},
            {"name": "Switches & Sockets"},
            {"name": "Lighting"},
            {"name": "Transformers"}
        ])

        conn.execute(products.insert(), [
            {"name": "Copper Wire 10m", "category_id": 1, "supplier_id": 1, "price": 25.99, "stock_quantity": 100},
            {"name": "LED Light Bulb 10W", "category_id": 3, "supplier_id": 2, "price": 5.49, "stock_quantity": 500},
            {"name": "Electrical Socket", "category_id": 2, "supplier_id": 3, "price": 3.75, "stock_quantity": 300},
            {"name": "Mini Transformer 220V-110V", "category_id": 4, "supplier_id": 1, "price": 45.99, "stock_quantity": 50}
        ])

        conn.execute(customers.insert(), [
            {"name": "Alice Cooper", "email": "alice@email.com", "phone": "555-1111", "address": "101 Main St", "state": "california"},
            {"name": "Bob Martin", "email": "bob@email.com", "phone": "555-2222", "address": "202 Elm St","state":"florida"},
            {"name": "Martin", "email": "martin@email.com", "phone": "555-2222", "address": "202 Elm St","state":"arizona"}
        ])

        # Add this import at the top

        # Replace the orders insertion with:
        conn.execute(orders.insert(), [
            {"customer_id": 1, "order_date": datetime.date(2024, 2, 10), "total_amount": 51.48},
            {"customer_id": 2, "order_date": datetime.date(2024, 2, 15), "total_amount": 23.97}
        ])


        conn.execute(order_items.insert(), [
            {"order_id": 1, "product_id": 1, "quantity": 2, "unit_price": 25.99},
            {"order_id": 2, "product_id": 2, "quantity": 3, "unit_price": 5.49},
            {"order_id": 2, "product_id": 3, "quantity": 2, "unit_price": 3.75}
        ])

        conn.execute(taxes.insert(), [
            {"state": "california", "tax_rate": 0.07},  # Example tax rate 7%
            {"state": "florida", "tax_rate": 0.06}  # Example tax rate 6%
        ])

if __name__ == "__main__":
    create_db()

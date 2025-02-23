# from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String, select
# import json
# from datetime import datetime


# def place_order(customer_id, order_items):
#     engine = create_engine(f"sqlite:///electrical_parts.db", echo=True)
#     metadata = MetaData()

#     # Reflect tables from the database
#     customers = Table('customers', metadata, autoload_with=engine)
#     products = Table('products', metadata, autoload_with=engine)
#     orders = Table('orders', metadata, autoload_with=engine)
#     order_items_table = Table('order_items', metadata, autoload_with=engine)

#     response = {}
#     try:
#         with engine.begin() as connection:
#             # Check if the customer exists
#             result = connection.execute(
#                 select(customers).where(customers.c.customer_id == customer_id)
#             ).fetchone()

#             if not result:
#                 response["status"] = "error"
#                 response["message"] = f"Customer ID {customer_id} does not exist."
#                 return json.dumps(response)

#             total_amount = 0.0
#             updated_stock = []

#             # Verify products and calculate total
#             for item in order_items:
#                 product_id = item["product_id"]
#                 quantity = item["quantity"]

#                 product = connection.execute(
#                     select(products).where(products.c.product_id == product_id)
#                 ).fetchone()

#                 if not product:
#                     response["status"] = "error"
#                     response["message"] = f"Product ID {product_id} does not exist."
#                     return json.dumps(response)

#                 price = product.price
#                 stock_quantity = product.stock_quantity
#                 if stock_quantity < quantity:
#                     response["status"] = "error"
#                     response["message"] = f"Not enough stock for Product ID {product_id}. Available: {stock_quantity}"
#                     return json.dumps(response)

#                 total_amount += price * quantity
#                 updated_stock.append((stock_quantity - quantity, product_id))

#             # Round off total amount
#             total_amount = round(total_amount, 2)

#             # Insert order using SQLAlchemy Core API
#             order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             result = connection.execute(
#                 orders.insert().values(
#                     customer_id=customer_id,
#                     order_date=order_date,
#                     total_amount=total_amount
#                 )
#             )
#             # Retrieve the auto-generated order ID
#             order_id = connection.execute(select(orders.c.order_id).order_by(orders.c.order_id.desc())).scalar()

#             # Insert order items and update stock
#             for item in order_items:
#                 product_id = item["product_id"]
#                 quantity = item["quantity"]
#                 unit_price = connection.execute(
#                     select(products).where(products.c.product_id == product_id)
#                 ).fetchone().price

#                 connection.execute(
#                     order_items_table.insert().values(
#                         order_id=order_id,
#                         product_id=product_id,
#                         quantity=quantity,
#                         unit_price=unit_price
#                     )
#                 )

#             for new_stock, product_id in updated_stock:
#                 connection.execute(
#                     products.update().where(products.c.product_id == product_id).values(
#                         stock_quantity=new_stock
#                     )
#                 )

#             response["status"] = "success"
#             response["message"] = f"Order placed successfully with Order ID: {order_id}"
#             response["order_id"] = order_id

#     except Exception as e:
#         response["status"] = "error"
#         response["message"] = f"Failed to place order: {str(e)}"

#     return json.dumps(response)

# if __name__ == "__main__":
#     order = [
#         {"product_id": 1, "quantity": 2},
#         {"product_id": 2, "quantity": 3}
#     ]
#     print(place_order(customer_id=1, order_items=order))


# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ V2
from sqlalchemy import create_engine, text


def insert_order(order_id, customer_id, order_date, total_amount):
    # Connect to the existing SQLite database
    engine = create_engine("sqlite:///electrical_parts.db", echo=True)

    # SQL insert statement
    insert_query = text(
        """
        INSERT INTO orders (order_id,customer_id, order_date, total_amount)
        VALUES (:order_id,:customer_id, :order_date, :total_amount)
    """
    )

    order_id = result.lastrowid

    # Execute the insert statement
    with engine.connect() as conn:
        conn.execute(
            insert_query,
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_date": order_date,
                "total_amount": total_amount,
            },
        )
        conn.commit()
        print("Order inserted successfully!")


# Example usage
if __name__ == "__main__":
    insert_order(1, 2, "2024-02-25", 452.99)

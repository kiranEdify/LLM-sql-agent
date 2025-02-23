from sqlalchemy import text, create_engine
import json

def cancel_order(order_id):
    engine = create_engine(f"sqlite:///electrical_parts.db", echo=True)

    response = {}
    try:
        with engine.begin() as connection:
            # Check if the order exists
            result = connection.execute(
                text(f"SELECT * FROM orders WHERE order_id = {order_id}")
            ).fetchone()

            if not result:
                response["status"] = "error"
                response["message"] = f"Order ID {order_id} does not exist."
                return json.dumps(response)

            # Retrieve the order items for restocking
            order_items = connection.execute(
                text(f"SELECT product_id, quantity FROM order_items WHERE order_id = {order_id}")
            ).fetchall()

            if not order_items:
                response["status"] = "error"
                response["message"] = f"No items found for Order ID {order_id}."
                return json.dumps(response)

            # Restock products
            for product_id, quantity in order_items:
                connection.execute(
                    text(f"UPDATE products SET stock_quantity = stock_quantity + {quantity} WHERE product_id = {product_id}")
                )

            # Delete order items
            connection.execute(
                text(f"DELETE FROM order_items WHERE order_id = {order_id}")
            )

            # Delete the order
            connection.execute(
                text(f"DELETE FROM orders WHERE order_id = {order_id}")
            )

            response["status"] = "success"
            response["message"] = f"Order ID {order_id} has been canceled and stock has been updated."

    except Exception as e:
        response["status"] = "error"
        response["message"] = f"Failed to cancel order: {str(e)}"

    return json.dumps(response)

if __name__ == "__main__":
    print(cancel_order(order_id=3))

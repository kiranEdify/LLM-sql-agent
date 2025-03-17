from sqlalchemy import text, create_engine
import json
from datetime import datetime
from db_setup.tax_check_v3 import check_tax_rate, store_tax_rate  # Import functions from tax_check_v3

def place_order(customer_id, order_items):
    engine = create_engine("sqlite:///electrical_parts.db", echo=True)

    response = {}
    try:
        with engine.begin() as connection:
            # Check if the customer exists
            result = connection.execute(
                text("SELECT * FROM customers WHERE customer_id = :customer_id"),
                {"customer_id": customer_id},
            ).fetchone()
            if not result:
                response["status"] = "error"
                response["message"] = f"Customer ID {customer_id} does not exist."
                return json.dumps(response)

            total_amount = 0.0
            updated_stock = []

            # Verify products and calculate total
            for item in order_items:
                product_id = item["product_id"]
                quantity = item["quantity"]

                product = connection.execute(
                    text(
                        "SELECT price, stock_quantity FROM products WHERE product_id = :product_id"
                    ),
                    {"product_id": product_id},
                ).fetchone()

                if not product:
                    response["status"] = "error"
                    response["message"] = f"Product ID {product_id} does not exist."
                    return json.dumps(response)

                price, stock_quantity = product
                if stock_quantity < quantity:
                    response["status"] = "error"
                    response["message"] = (
                        f"Not enough stock for Product ID {product_id}. Available: {stock_quantity}"
                    )
                    return json.dumps(response)

                total_amount += price * quantity
                updated_stock.append((stock_quantity - quantity, product_id))

            # Round off total amount
            total_amount = round(total_amount, 2)

            # Apply standard tax rate of 1%
            standard_tax_rate = 0.01  # 1% tax rate
            standard_tax_amount = total_amount * standard_tax_rate

            # Get the customer's state
            customer_state = result[5]  # Assuming 'state' is at index 5
            customer_state = customer_state.lower()
            
            # Get the state-specific tax rate from the taxes table
            state_tax_result = connection.execute(
                text("SELECT tax_rate FROM taxes WHERE state = :state"),
                {"state": customer_state},
            ).fetchone()

            if not state_tax_result:
                # If tax rate is not found, check ChromaDB using tax_check_v3
                print(f"No tax information available for {customer_state}, checking ChromaDB...")
                tax_response = json.loads(check_tax_rate(customer_state))
                if tax_response.get("status") == "success" and "tax_rate" in tax_response:
                    state_tax_rate = tax_response["tax_rate"]
                    print(f"Fetched tax rate from ChromaDB: {state_tax_rate * 100}%")
                    store_tax_rate(customer_state, state_tax_rate)  # Store in SQLite
                else:
                    response["status"] = "error"
                    response["message"] = f"No tax information available for state: {customer_state}."
                    return json.dumps(response)
            else:
                state_tax_rate = state_tax_result[0]  # Accessing tax_rate by index

            state_tax_amount = total_amount * state_tax_rate

            # Add both standard tax and state-specific tax to the total amount
            total_tax_amount = standard_tax_amount + state_tax_amount
            total_amount_with_tax = round(total_amount + total_tax_amount, 2)

            # Get the maximum order_id and add 1, or start with 1 if no orders exist
            result = connection.execute(
                text("SELECT COALESCE(MAX(order_id), 0) FROM orders")
            ).fetchone()
            order_id = result[0] + 1

            order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            connection.execute(
                text(
                    "INSERT INTO orders (order_id, customer_id, order_date, total_amount) VALUES (:order_id, :customer_id, :order_date, :total_amount)"
                ),
                {
                    "order_id": order_id,
                    "customer_id": customer_id,
                    "order_date": order_date,
                    "total_amount": total_amount_with_tax,  # Store total amount including both taxes
                },
            )

            # Insert order items and update stock
            for item in order_items:
                product_id = item["product_id"]
                quantity = item["quantity"]
                unit_price = connection.execute(
                    text("SELECT price FROM products WHERE product_id = :product_id"),
                    {"product_id": product_id},
                ).fetchone()[0]

                connection.execute(
                    text(
                        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (:order_id, :product_id, :quantity, :unit_price)"
                    ),
                    {
                        "order_id": order_id,
                        "product_id": product_id,
                        "quantity": quantity,
                        "unit_price": unit_price,
                    },
                )

            # Update stock quantities
            for new_stock, product_id in updated_stock:
                connection.execute(
                    text(
                        "UPDATE products SET stock_quantity = :new_stock WHERE product_id = :product_id"
                    ),
                    {"new_stock": new_stock, "product_id": product_id},
                )

            response["status"] = "success"
            response["message"] = f"Order placed successfully with Order ID: {order_id}"
            response["order_id"] = order_id
            response["total_amount"] = total_amount_with_tax
            response["standard_tax_amount"] = standard_tax_amount
            response["state_tax_amount"] = state_tax_amount
            response["total_tax_amount"] = total_tax_amount

    except Exception as e:
        response["status"] = "error"
        response["message"] = f"Failed to place order: {str(e)}"

    return json.dumps(response)


if __name__ == "__main__":
    order = [{"product_id": 1, "quantity": 50}, {"product_id": 2, "quantity": 3}]
    print(place_order(customer_id=2, order_items=order))

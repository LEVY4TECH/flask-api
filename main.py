# REST API is a backend API that follows the 4 ruels below:
# 1. It has to have a route
# 2. It has to have a method(GET/POST/PUT/DELETE)
# 3. It has to have a status code(200, 403, 201)
# 4. It has to return data as JSON(key : value pairs)

import sentry_sdk
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_bcrypt import Bcrypt
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models import Base, Product, User, Sale, SaleDetail, Payment, Purchase
from datetime import datetime
from mpesa import make_stk_push
from generate_receipts import create_pdf


sentry_sdk.init(
    dsn="https://79b824f662d94ca63adff8facd141f40@o4512045969178624.ingest.us.sentry.io/4512046187085824",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "HSDBHFBCSJBCHDB"
jwt = JWTManager(app)

bcrypt = Bcrypt(app)

# Create a connection to the database using SQLAlchemy engine
engine = create_engine("sqlite:///./flask_duka_api.db", echo=True)

# Create the Tables into the database using SQLAlchemy
Base.metadata.create_all(engine)

# Create a session to do sql transactions
session = Session(engine)

allowed_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

@app.before_request
def before_request():
    try:
        pass
    except:
        pass
        
@app.route("/", methods = allowed_methods)
def home():
    if request.method == "GET":
        data = {"Flask API" : "Version 1"}
        return jsonify(data), 200
    else:
        error = {"Error" : "Method not allowed"}
        return jsonify(error), 403
    
@app.route("/dashboard", methods = allowed_methods)
def dashboard():
    if request.method == "GET":
        data = {"Flask API" : "Version 1"}
        return jsonify(data), 200
    else:
        error = {"Error" : "Method not allowed"}
        return jsonify(error), 403

# REGISTER
@app.route("/register", methods=allowed_methods)
def register():
    try:
        if request.method == "GET":
            query = select(User)
            users = session.scalars(query)

            results = []

            for user in users:
                u = {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email
                    
                }
                results.append(u)

            return jsonify(results), 200

        elif request.method == "POST":
            data = request.get_json()

            full_name = data["full_name"]
            email = data["email"]
            password = data["password"]
           

            if data["full_name"] == "" or data["email"] == "" or data["password"] == "":
                return jsonify({
                    "Error": "Ensure all fields are set"
                }), 400

            # Checking if email already exists
            existing_user = session.query(User).filter_by(email=email).first()

            if existing_user:
                return jsonify({
                    "Error": "Email is already registered"
                }), 409

            # Hash password
            hashed_password = bcrypt.generate_password_hash(password)

            # Create new user
            new_user = User(
                full_name=full_name,
                email=email,
                password=hashed_password.decode("utf-8")
                
            )

            session.add(new_user)
            session.commit()

            access_token = create_access_token(identity=email)

            return jsonify({
                "id": new_user.id,
                "full_name" : new_user.full_name,
                "email" : new_user.email,
                "Message": "User added successfully",
                "access_token": access_token,
                "url": "http://127.0.0.1:5000/login"
            }), 201

        else:
            error = {"Error": "Method not allowed"}
            return jsonify(error), 405

    except Exception as error:
        session.rollback()
        return jsonify({"Error": str(error)}), 500


# @app.route("/login", methods = allowed_methods)
# def login():
#     if request.method == "GET":
#         error = {"Error": "Method Not Allowed"}
#         return jsonify(error), 405
#     elif request.method == "POST":
#         data = request.get_json()
        
#         email = data["email"]
#         password = data["password"]
        
#         if data["email"] == "" or data["password"] == "":
#             error = {"Error": "Ensure email and password are set"}
#             return jsonify(error), 403
        
#         query = select(User).filter_by(email = data["email"])
#         existing_user = session.scalars(query).first()
        
#         if not existing_user:
#             error = {"Error" : "Invalid Email"}
#             return jsonify(error), 403
        
#         if not bcrypt.check_password_hash(existing_user.password, password):
#             error = {"Error" : "Invalid password"}
#             return jsonify(error), 403
        
#         token = create_access_token(identity=email)
#         return jsonify({"Message": "User logged in successfully", "token" : token}), 200
#     else:
#         error = {"Error": "Method Not Allowed"}
#         return jsonify(error), 405

# LOGIN
@app.route("/login", methods=allowed_methods)
def login():
    try:
        if request.method == "GET":
            return jsonify({
                "Message": "Please enter your login details"
            }), 200

        elif request.method == "POST":
            data = request.get_json()

            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return jsonify({
                    "Error": "Ensure all fields are set"
                }), 403

            existing_user = session.query(User).filter_by(email=email).first()

            if not existing_user:
                return jsonify({
                    "Error": "Invalid email or password"
                }), 401

            if not bcrypt.check_password_hash(
                existing_user.password,
                password
            ):
                return jsonify({
                    "Error": "Invalid email or password"
                }), 401

            token = create_access_token(
                identity=existing_user.email
            )

            return jsonify({
                "id": existing_user.id,
                "email": existing_user.email,
                "full_name": existing_user.full_name,
                "token": token,
                "Message": "login successful"
            }), 200

        else:
            return jsonify({
                "error": "Method not allowed"
            }), 405

    except Exception as error:
        return jsonify({
            "Error": str(error)
        }), 500
           
    

@app.route("/products", methods=["GET", "POST"])
@jwt_required()
def products():
    email = get_jwt_identity()

    user = session.scalars(
        select(User).where(User.email == email)
    ).first()

    if not user:
        return jsonify({"Error": "User not found"}), 404

    if request.method == "GET":
        product_list = session.scalars(
            select(Product).where(Product.user_id == user.id)
        ).all()

        results = [
            {
                "id": p.id,
                "product_name": p.product_name,
                "buying_price": p.buying_price,
                "selling_price": p.selling_price,
                "stock_quantity": p.stock_quantity
            }
            for p in product_list
        ]

        return jsonify(results), 200

    data = request.get_json(silent=True) or {}

    product_name = data.get("product_name")
    buying_price = data.get("buying_price")
    selling_price = data.get("selling_price")
    stock_quantity = data.get("stock_quantity")

    if (
        not product_name
        or buying_price is None
        or selling_price is None
        or stock_quantity is None
    ):
        return jsonify({
            "Error": "Product name, buying price, selling price and stock quantity are required"
        }), 400

    try:
        buying_price = float(buying_price)
        selling_price = float(selling_price)
        stock_quantity = int(stock_quantity)

        if buying_price < 0 or selling_price < 0:
            return jsonify({"Error": "Prices cannot be negative"}), 400

        if stock_quantity < 0:
            return jsonify({"Error": "Stock cannot be negative"}), 400

        new_product = Product(
            user_id=user.id,
            product_name=product_name.strip(),
            buying_price=buying_price,
            selling_price=selling_price,
            stock_quantity=stock_quantity
        )

        session.add(new_product)
        session.commit()

        return jsonify({
            "Message": "A new product has been added successfully",
            "product": {
                "id": new_product.id,
                "product_name": new_product.product_name,
                "buying_price": new_product.buying_price,
                "selling_price": new_product.selling_price,
                "stock_quantity": new_product.stock_quantity
            }
        }), 201

    except (ValueError, TypeError):
        session.rollback()
        return jsonify({
            "Error": "Prices must be numeric and stock quantity must be a whole number"
        }), 400

    except Exception as error:
        session.rollback()
        print(f"Create product error: {error}")
        return jsonify({"Error": "Failed to create product"}), 500

    


@app.route("/sales", methods=["GET", "POST"])
@jwt_required()
def sales():
    email = get_jwt_identity()

    user = session.scalars(
        select(User).where(User.email == email)
    ).first()

    if not user:
        return jsonify({"Error": "User not found"}), 404

    if request.method == "GET":
        sales_list = session.scalars(
            select(Sale)
            .where(Sale.user_id == user.id)
            .order_by(Sale.created_at.desc())
        ).all()

        results = [
            {
                "id": sale.id,
                "product_id": sale.product_id,
                "quantity": sale.quantity,
                "created_at": (
                    sale.created_at.isoformat()
                    if sale.created_at else None
                )
            }
            for sale in sales_list
        ]

        return jsonify(results), 200

    data = request.get_json(silent=True) or {}

    product_id = data.get("product_id")
    quantity = data.get("quantity")
    created_at = data.get("created_at")

    if product_id is None or quantity is None or not created_at:
        return jsonify({
            "Error": "Product, quantity and date are required"
        }), 400

    try:
        product_id = int(product_id)
        quantity = int(quantity)

        if product_id < 1 or quantity < 1:
            return jsonify({
                "Error": "Product ID and quantity must be positive integers"
            }), 400

        sale_date = datetime.fromisoformat(
            created_at.replace("Z", "+00:00")
        )

    except (ValueError, TypeError):
        return jsonify({
            "Error": "Invalid product ID, quantity or date"
        }), 400

    try:
        # Lock the product row while checking and updating stock.
        product = session.scalars(
            select(Product)
            .where(
                Product.id == product_id,
                Product.user_id == user.id
            )
            .with_for_update()
        ).first()

        if not product:
            session.rollback()
            return jsonify({"Error": "Product not found"}), 404

        if quantity > product.stock_quantity:
            session.rollback()
            return jsonify({
                "Error": "Insufficient stock",
                "available_stock": product.stock_quantity
            }), 400

        product.stock_quantity -= quantity

        new_sale = Sale(
            user_id=user.id,
            product_id=product.id,
            quantity=quantity,
            created_at=sale_date
        )

        session.add(new_sale)
        session.commit()

        return jsonify({
            "Message": "Sale recorded successfully",
            "sale": {
                "id": new_sale.id,
                "product_id": new_sale.product_id,
                "quantity": new_sale.quantity,
                "created_at": new_sale.created_at.isoformat()
            },
            "remaining_stock": product.stock_quantity
        }), 201

    except Exception as error:
        session.rollback()
        print(f"Create sale error: {error}")
        return jsonify({"Error": "Failed to record sale"}), 500

    
@app.route("/sale_details", methods = allowed_methods)
@jwt_required()
def sale_details():
    
    id = get_jwt_identity()
    
    sale = session.scalars(select(Sale).where(Sale.id==id)).first()
    
    if request.method == "GET":
        query = select(SaleDetail)
        sale_details = session.scalars(query)
        
        results = []
        for sale_detail in sale_details:
            sd = {"id" : sale_detail.id,
                  "quantity" : sale_detail.quantity,
                  "selling_price" : sale_detail.quantity,
                  "created_at" : sale_detail.created_at}
            results.append(sd)
        return jsonify(results), 200
    elif request.method == "POST":
        data = request.get_json()
        if data["quantity"] == "" or data["selling_price"] == "" or data["created_at"] == "":
            error = {"error" : "Ensure all fields are set"}
            return jsonify(error), 403
        else:
            new_sale_detail = SaleDetail(
                sale_id = sale["id"],
                product_id = float(data["product_id"]),
                quantity = float(data["quantity"]),
                selling_price = float(data["selling_price"]),
                created_at = data["created_at"]
            )
            session.add(new_sale_detail)
            session.commit()
            return jsonify({"Message" : "A new sale detail has been added successfully"}), 201
    else:
        error = {"Error" : "Method Not Allowed"}
        return jsonify(error), 405

@app.route("/purchases", methods = allowed_methods)
@jwt_required()
def purchases():
    
    id = get_jwt_identity()
    
    product = session.scalars(select(Product).where(Product.id==id)).first()
    
    if request.method == "GET":
        query = select(Purchase)
        purchases = session.scalars(query)
        
        results = []
        for pur in purchases:
            p = {"id" : pur.id,
                 "quantity" : pur.quantity,
                 "buying_price" : pur.buying_price,
                 "created_at" : pur.created_at}
            results.append(p)
        return jsonify(results), 200
    elif request.method == "POST":
        data = request.get_json()
        if data["quantity"] == "" or data["buying_price"] == "" or data["created_at"] == "":
            error = {"Eror" : "Ensure all fields are set"}
            return jsonify(error), 403
        else:
            new_purchase = Purchase(
                product_id = product["id"],
                quantity = float(data["quantity"]),
                buying_price = float(data["buying_price"]),
                created_at = data["created_at"]
            )
            session.add(new_purchase)
            session.commit()
            return jsonify({"Message" : "A new purchase has been made"}), 201
    else:
        error = {"Error" : "Method Not Allowed"}
        return jsonify(error), 405
    
@app.route("/payments", methods = allowed_methods)
@jwt_required()
def payments():
    
    id = get_jwt_identity()
    
    sale = session.scalars(select(Sale).where(Sale.id==id)).first()
    
    if request.method == "GET":
        query = select(Payment)
        payments = session.scalars(query)
        
        results = []
        for pay in payments:
            pa = {"id" : pay.id,
                  "amount" : pay.amount,
                  "payment_method" : pay.payment_method,
                  "created_at" : pay.created_at}
            results.append(pa)
        return jsonify(results), 200
    elif request.method == "POST":
        data = request.get_json()
        if data["amount"] == "" or data["payment_method"] == "" or data["created_at"] == "":
            error = {"Error" : "Ensure all fields are set"}
            return jsonify(error), 403
        else:
            new_payment = Payment(
                sale_id = sale["id"],
                amount = float(data["amount"]),
                payment_method = data["payment_method"],
                created_at = data["created_at"]
            )
            session.add(new_payment)
            session.commit()
            return jsonify({"Message" : "A new payment has been made"}), 201
    else:
        error = {"Error": "Method Not Allowed"}
        return jsonify(error), 405

@app.route("/stk_push", methods = ["POST"])    
def stk_push():
    try:
        payload = request.get_json()

        if not payload:
            return {"message": "Request body must contain JSON"}, 400
        
        response = make_stk_push(payload)
        new_payment = Payment(sale_id=payload["sale_id"],
                             amount=payload["amount"],
                             phone_number=payload["phone_number"],
                             mrid=response.get("MerchantRequestID"),
                             crid=response.get("CheckoutRequestID"),
                             status="pending")
        session.add(new_payment)
        session.commit()
        return("stk push initiated")
    
    except Exception as e:
        print("stk push error")
        return {"message":"stk push failed"}

    

@app.route("/saf-callback", methods=["POST"])
def saf_callback():
    body = request.get_json()
    try:
        stkCallback = body.get("Body", {}).get("stkCallback", {})
        result_code = stkCallback.get("ResultCode")
        mrid = stkCallback.get("MerchantRequestID")
        crid = stkCallback.get("CheckoutRequestID")

        payment = session.execute(
            select(Payment).where(Payment.mrid == mrid, Payment.crid == crid)
        ).scalars().first()

        if payment:
            if result_code == 0:
                callback_metadata = stkCallback.get("CallbackMetadata", {}).get("Item", [])
                for item in callback_metadata:
                    if item.get("Name") == "MpesaReceiptNumber":
                        payment.transaction_code = item.get("Value")
                payment.status = "completed"
            else:
                payment.status = "failed"

            # Commit payment status FIRST - this is critical
            session.commit()
            
            text=f"Transaction Code {payment.transaction_code}, Amount: {payment.amount}, Date : {payment.created_at} "
            create_pdf(text,payment.transaction_code)

    except Exception as e:
        print("Error Processing Callback:", e)
        session.rollback()
        
    

    return {"message": "callback received"}
    








    

        
    
app.run(debug=True)
    
        
    
    

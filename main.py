# REST API is a backend API that follows the 4 ruels below:
# 1. It has to have a route
# 2. It has to have a method(GET/POST/PUT/DELETE)
# 3. It has to have a status code(200, 403, 201)
# 4. It has to return data as JSON(key : value pairs)

from flask import Flask, request, jsonify
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models import Base, Product


app = Flask(__name__)

# Create a connection to the database using SQLAlchemy engine
engine = create_engine("sqlite:///./flask_duka_api.db", echo=True)

# Create the Tables into the database using SQLAlchemy
Base.metadata.create_all(engine)

# Create a session to do sql transactions
session = Session(engine)


@app.route("/")
def home():
    if request.method == "GET":
        data = {"Flask API" : "Version 1"}
        return jsonify(data), 200
    else:
        error = {"Error" : "Method not allowed"}
        return jsonify(error), 403
    
    
@app.route("/products")
def products():
    if request.method == "GET":
        # Fetch data from the database
        query = select(Product)
        products = session.scalars(query)
        
        results = []
        for prod in products:
            p = {"id" : prod.id,
                 "product_name" : prod.product_name,
                 "buying_price" : prod.buying_price,
                 "selling_price" : prod.selling_price}
            results.append(p)
        return jsonify(results), 200
    
    elif request.method == "POST":
        data = request.get_json()
        if data["product_name"] == "" or data["buying_price"] == "" or data["selling_price"] == "" :
            error = {"error" : "Ensure all fields are set"}
            return jsonify(error), 403
        else:
            #Store in the database
            pass
    else:
        error = {"Error": "Method not allowed"}
        return jsonify(error), 405
    
app.run(debug=True)
#!/usr/bin/env python3
from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_restful import Api, Resource
from werkzeug.exceptions import BadRequest
from models import db, Restaurant, Pizza, RestaurantPizza

app = Flask(__name__)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
api = Api(app)

@app.route("/")
def index():
    return "<h1>Pizza Place</h1>"

# GET /restaurants - Return all restaurants
class RestaurantsResource(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return jsonify([restaurant.to_dict(only=("id", "name", "address")) for restaurant in restaurants])

# GET /restaurants/<int:id> - Return specific restaurant and its pizzas
@app.route('/restaurants/<int:id>', methods=['GET'])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404  # Adjusted error format
    return jsonify(restaurant.to_dict()), 200

# DELETE /restaurants/<int:id> - Delete a restaurant (cascade delete RestaurantPizzas)
@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({'error': 'Restaurant not found'}), 404  # Adjusted error format
    db.session.delete(restaurant)
    db.session.commit()
    return '', 204  # Changed to 204 for successful deletion

class RestaurantResource(Resource):
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant:
            return jsonify(restaurant.to_dict(rules=("-restaurant_pizzas.restaurant",)))
        return jsonify({"error": "Restaurant not found"}), 404

    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant:
            db.session.delete(restaurant)
            db.session.commit()
            return "", 204  # Changed to 204 for successful deletion
        return jsonify({"error": "Restaurant not found"}), 404

# GET /pizzas - Return all pizzas
class PizzasResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return jsonify([pizza.to_dict(only=("id", "name", "ingredients")) for pizza in pizzas])

# POST /restaurant_pizzas - Create a new RestaurantPizza with validation
@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()
    price = data.get('price')
    if price is None or price < 1 or price > 30:
        return jsonify({"errors": ["validation errors"]}), 400
    pizza_id = data.get('pizza_id')
    restaurant_id = data.get('restaurant_id')

    # Ensure valid pizza and restaurant IDs
    if not pizza_id or not restaurant_id:
        return jsonify({"error": "Pizza and restaurant IDs must be provided"}), 400

    pizza = Pizza.query.get(pizza_id)
    restaurant = Restaurant.query.get(restaurant_id)

    if not pizza or not restaurant:
        return jsonify({"error": "Invalid pizza or restaurant ID"}), 404

    new_restaurant_pizza = RestaurantPizza(
        price=price, pizza_id=pizza.id, restaurant_id=restaurant.id
    )
    db.session.add(new_restaurant_pizza)
    db.session.commit()

    return jsonify(new_restaurant_pizza.to_dict()), 201

class RestaurantPizzasResource(Resource):
    def post(self):
        data = request.get_json()

        try:
            price = data.get("price")
            restaurant_id = data.get("restaurant_id")
            pizza_id = data.get("pizza_id")

            # Ensure all fields are provided
            if not all([price, restaurant_id, pizza_id]):
                return jsonify({"errors": ["Missing required fields"]}), 400

            # Ensure price is valid
            if not (1 <= price <= 30):
                return jsonify({"errors": ["Price must be between 1 and 30"]}), 400

            # Ensure restaurant and pizza exist
            restaurant = Restaurant.query.get(restaurant_id)
            pizza = Pizza.query.get(pizza_id)
            if not restaurant or not pizza:
                return jsonify({"errors": ["Invalid restaurant or pizza ID"]}), 400

            # Create and save new RestaurantPizza
            new_restaurant_pizza = RestaurantPizza(price=price, restaurant_id=restaurant_id, pizza_id=pizza_id)
            db.session.add(new_restaurant_pizza)
            db.session.commit()

            return jsonify(new_restaurant_pizza.to_dict()), 201

        except ValueError as e:
            return jsonify({"errors": [str(e)]}), 400

# Add resources to the API
api.add_resource(RestaurantsResource, "/restaurants")
api.add_resource(RestaurantResource, "/restaurants/<int:id>")
api.add_resource(PizzasResource, "/pizzas")
api.add_resource(RestaurantPizzasResource, "/restaurant_pizzas")

if __name__ == "__main__":
    app.run(port=5555, debug=True)


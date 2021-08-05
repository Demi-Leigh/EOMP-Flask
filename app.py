import hmac
import sqlite3
from flask_mail import Mail, Message
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS


class UserInfo(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def user_table():
    with sqlite3.connect('point_of_sale.db') as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users ("
                       "user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                       "full_name TEXT NOT NULL,"
                       "username TEXT NOT NULL,"
                       "password TEXT NOT NULL)")

        print("user table created successfully")


def fetch_users():
    with sqlite3.connect('point_of_sale.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

        user_data = []
        for data in users:
            user_data.append(UserInfo(data[0], data[2], data[3]))
    return user_data


def product_table():
    with sqlite3.connect('point_of_sale.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "name TEXT NOT NULL,"
                     "price TEXT NOT NULL,"
                     "description TEXT NOT NULL,"
                     "type TEXT NOT NULL)")
    print("product table created successfully.")


user_table()
product_table()

users = fetch_users()


username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
CORS(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'demijay2323@gmail.com'
app.config['MAIL_PASSWORD'] = '1a2a3a4a5a6a7a8a'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


@app.route('/user-registration/', methods=["POST"])
def user_registration():
    response = {}

    if request.method == "POST":

        full_name = request.form['full_name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        with sqlite3.connect("point_of_sale.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users("
                           "full_name,"
                           "username,"
                           "password,"
                           "email) VALUES(?, ?, ?, ?)", (full_name, username, password, email))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201
            if response["status_code"] == 201:
                msg = Message('WELCOME', sender='demijay2323@gmail.com', recipients=[email])
                msg.body = "You have successfully registered"
                mail.send(msg)
                return "Send email"


@app.route('/add-product/', methods=["POST"])
@jwt_required()
def add_product():
    response = {}

    if request.method == "POST":
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        type = request.form['type']

        with sqlite3.connect('point_of_sale.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO products("
                           "name,"
                           "price,"
                           "description,"
                           "type) VALUES (?, ?, ?,?)", (name, price, description, type))
            conn.commit()
            response["status_code"] = 201
            response['description'] = "product added successfully"
        return response


@app.route('/view-products/', methods=["GET"])
def view_products():
    response = {}
    with sqlite3.connect("point_of_sale.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")

        products = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = products
    return response


@app.route("/delete-product/<int:id>/")
@jwt_required()
def delete_product(id):
    response = {}
    with sqlite3.connect("point_of_sale.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=" + str(id))
        conn.commit()
        response['status_code'] = 200
        response['message'] = "product deleted successfully."
    return response


@app.route('/edit-product/<int:id>/', methods=["PUT"])
@jwt_required()
def edit_product(id):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect('point_of_sale.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("name") is not None:
                put_data["name"] = incoming_data.get("name")
                with sqlite3.connect('point_of_sale.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE products SET name =? WHERE id=?", (put_data["name"], id))
                    conn.commit()
                    response['message'] = "Updated successfully"
                    response['status_code'] = 200

            elif incoming_data.get("price") is not None:
                put_data['price'] = incoming_data.get('price')

                with sqlite3.connect('point_of_sale.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE products SET price =? WHERE id=?", (put_data["price"], id))
                    conn.commit()

                    response["message"] = "updated successfully"
                    response["status_code"] = 200

            elif incoming_data.get("description") is not None:
                put_data['description'] = incoming_data.get('description')

                with sqlite3.connect('point_of_sale.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE products SET description =? WHERE id=?", (put_data["description"], id))
                    conn.commit()

                    response["message"] = "updated successfully"
                    response["status_code"] = 200

            elif incoming_data.get("type") is not None:
                put_data['type'] = incoming_data.get('type')

                with sqlite3.connect('point_of_sale.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE products SET type =? WHERE id=?", (put_data["type"], id))
                    conn.commit()

                    response["message"] = "updated successfully"
                    response["status_code"] = 200
    return response


@app.route('/view-product/<int:id>/', methods=["GET"])
def view_product(id):
    response = {}
    with sqlite3.connect("point_of_sale.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id=?", str(id))

        products = cursor.fetchone()

    response['status_code'] = 200
    response['data'] = products
    return jsonify(response)

if __name__ == '__main__':
    app.run()

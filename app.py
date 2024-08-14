from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
import mysql.connector
from dotenv import load_dotenv
from config import Config
import requests
import os

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db_config = {
    'user': app.config['DB_USER'],
    'password': app.config['DB_PASSWORD'],
    'host': app.config['DB_HOST'],
    'database': app.config['DB_NAME']
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if "send_email" in request.form:  # Check if the form is for sending an email
            restaurant_id = request.form.get("restaurant_id")
            email = request.form.get("email")
            
            if not email:
                flash("Please provide a valid email address.", "form_error")
                return redirect(url_for("home"))
            
            # Fetch restaurant data from the database
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM restaurants WHERE id = %s", (restaurant_id,))
            restaurant = cursor.fetchone()
            cursor.close()
            connection.close()

            if not restaurant:
                flash("Restaurant not found.", "form_error")
                return redirect(url_for("home"))

            restaurant_data = {
                "name": restaurant['name'],
                "rating": restaurant['rating'],
                "cuisine": restaurant['cuisine'],
                "price": restaurant['price'],
                "ammenities": restaurant['ammenities'],
                "comments": restaurant['comments']
            }

            # Send data to Microservice B
            api_url = "https://microservice-b-cs361-1bdbe3050a21.herokuapp.com/send-restaurant-info"
            response = requests.post(api_url, json={"email": email, "restaurant": restaurant_data})

            if response.status_code == 200:
                flash("Email sent successfully!", "success")
            else:
                flash("Failed to send email. Please try again.", "error")

            return redirect(url_for("home"))

        else:
            restaurant_id = request.form.get("restaurant_id", "").strip()
            restaurant_name = request.form.get("restaurant_name", "").strip()
            rating = int(request.form.get("rating", "").strip())
            cuisine = request.form.get("cuisine", "").strip()
            price = request.form.get("price", "").strip()
            ammenities = request.form.getlist("ammenities")
            comments = request.form.get("user-comments", "").strip()

            if not restaurant_name or not rating or not cuisine or not price:
                flash("All fields except ammenities and comments are required.", "form_error")
                return redirect(url_for("home"))

            if 0 < len(comments) < 20:
                flash("Please enter at least 20 characters at a minimum or none at all.", "form_error")
                return redirect(url_for("home"))

            ammenities_str = ', '.join(ammenities)

            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    if restaurant_id:
                        cursor.execute("""
                            UPDATE restaurants
                            SET name = %s, rating = %s, cuisine = %s, price = %s, comments = %s, ammenities = %s
                            WHERE id = %s
                            """, (
                                restaurant_name,
                                rating,
                                cuisine,
                                price,
                                comments if comments else None,
                                ammenities_str if ammenities_str else None,
                                restaurant_id
                            ))
                        flash("Restaurant updated successfully!", "success")
                    else:
                        cursor.execute("""
                            INSERT INTO restaurants (name, rating, cuisine, price, comments, ammenities)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """, (
                                restaurant_name,
                                rating,
                                cuisine,
                                price,
                                comments if comments else None,
                                ammenities_str if ammenities_str else None
                            ))
                        flash("Restaurant added successfully!", "success")
                connection.commit()
            return redirect(url_for("home", page=1))

    # Pull restaurants from the database
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    with get_db_connection() as connection:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM restaurants")
            total = cursor.fetchone()['total']
            total_pages = (total + per_page - 1) // per_page

            cursor.execute("SELECT * FROM restaurants LIMIT %s OFFSET %s", (per_page, offset))
            restaurants = cursor.fetchall()

    title = "Expand Here for Instructions"
    add_title = "Add a Restaurant"
    view_title = "View Your Restaurants"
    contents = "Welcome to the Restaurant Explorer! This tool will allow you to add, edit, delete, filter, and view restaurants. If you would like to edit an entry, the 'Add a Restaurant' section will turn into a section to edit the selected restaurant entry. If you're feeling unsure about what to pick, try out the 'Let's Go!' button at the bottom of this page!"
    note = "Note: Add a restaurant entry and see it show up under 'View Your Restaurants' below. Ammenities and Comments are optional when adding a restaurant."
    end_note = "Can't Decide? Let us pick for you."

    return render_template('index.html', title=title, contents=contents, note=note, end_note=end_note, add_title=add_title, view_title=view_title, restaurants=restaurants, page=page, total_pages=total_pages)


@app.route("/delete/<int:restaurant_id>", methods=["POST"])
def delete_restaurant(restaurant_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM restaurants WHERE id = %s", (restaurant_id,))
        connection.commit()
        flash("Restaurant has been deleted.", "delete_success")
    except Exception as e:
        print("Database deletion error:", e)
        flash("Restaurant could not be deleted.", "delete_error")
    finally:
        cursor.close()
        connection.close()
    return redirect(url_for("home"))

@app.route("/get_restaurant_data/<int:restaurant_id>", methods=["GET"])
def get_restaurant_data(restaurant_id):
    # Pull restaurant data based on the restaurant_id
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT name FROM restaurants WHERE id = %s", (restaurant_id,))
    restaurant = cursor.fetchone()
    cursor.close()
    connection.close()

    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    restaurant_name = restaurant['name']
    url = "https://8tq8xw2094.execute-api.us-west-2.amazonaws.com/prod/restaurants"
    params = {'restaurant_name': restaurant_name}

    # Get the API key from the environment variable
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')

    # Make the GET request to the microservice
    response = requests.get(url, params=params)

    if response.status_code == 200:
        restaurant_data = response.json()

        # Generate the photo URL
        if 'photo' in restaurant_data and 'photo_reference' in restaurant_data['photo']:
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={restaurant_data['photo']['photo_reference']}&key={api_key}"
        else:
            photo_url = None  # Handle case where there is no photo

        # Pass the photo_url to the template along with other data
        return render_template('restaurant_details.html', restaurant_data=restaurant_data, photo_url=photo_url)
    else:
        return jsonify({"error": "Failed to fetch data"}), response.status_code



@app.route("/show_all", methods=["GET"])
def show_all():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM restaurants")
    restaurants = cursor.fetchall()
    cursor.close()
    connection.close()

    title = "Expand Here for Instructions"
    add_title = "Add a Restaurant"
    view_title = "View Your Restaurants"
    contents = "Welcome to the Restaurant Explorer! This tool will allow you to add, edit, delete, filter, and view restaurants. If you would like to edit an entry, the 'Add a Restaurant' section will turn into a section to edit the selected restaurant entry. If you're feeling unsure about what to pick, try out the 'Let's Go!' button at the bottom of this page!"
    note = "Note: Add a restaurant entry and see it show up under 'View Your Restaurants' below. Ammenities and Comments are optional when adding a restaurant."
    end_note = "Can't Decide? Let us pick for you."

    return render_template('index.html', title=title, contents=contents, note=note, end_note=end_note, add_title=add_title, view_title= view_title, restaurants=restaurants, page=1, total_pages=1)

@app.route("/random", methods=["POST"])
def random_restaurant():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM restaurants ORDER BY RAND() LIMIT 1")
    random_entry = cursor.fetchone()
    cursor.close()
    connection.close()

    title = "Expand Here for Instructions"
    add_title = "Add a Restaurant"
    view_title = "View Your Restaurants"
    contents = "Welcome to the Restaurant Explorer! This tool will allow you to add, edit, delete, filter, and view restaurants. If you would like to edit an entry, the 'Add a Restaurant' section will turn into a section to edit the selected restaurant entry. If you're feeling unsure about what to pick, try out the 'Let's Go!' button at the bottom of this page!"
    note = "Note: Add a restaurant entry and see it show up under 'View Your Restaurants' below. Ammenities and Comments are optional when adding a restaurant."
    end_note = "Can't Decide? Let us pick for you."

    return render_template('index.html', title=title, contents=contents, note=note, end_note=end_note, add_title=add_title, view_title=view_title, restaurants=[random_entry] if random_entry else [], page=1, total_pages=1, random_selection=True)

if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

@app.route('/get_restaurant_data', methods=['GET'])
def get_restaurant_data():
    restaurant_name = "Chipotle Walnut CA"
    url = "https://8tq8xw2094.execute-api.us-west-2.amazonaws.com/prod/restaurants"
    params = {'restaurant_name': restaurant_name}
    
    # Make the GET request to the microservice
    response = requests.get(url, params=params)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Use jsonify to return the JSON response
        return jsonify(response.json())
    else:
        # Handle the error
        return jsonify({"error": "Failed to fetch data"}), response.status_code

if __name__ == '__main__':
    app.run(debug=True)

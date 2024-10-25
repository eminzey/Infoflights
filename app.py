from flask import Flask, request, render_template
import requests
import json

app = Flask(__name__)

# Flight search URL
flight_search_url = "https://test.api.amadeus.com/v2/shopping/flight-offers"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    # Get user input from the form
    origin = request.form['origin']
    destination = request.form['destination']
    departure_date = request.form['departureDate']
    return_date = request.form['returnDate']
    travel_class = request.form['travelClass']
    adults = request.form['adults']

    # Set up headers with the access token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Define the parameters for the flight search
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "returnDate": return_date,
        "travelClass": travel_class,
        "adults": adults,
        "max": 3  # Limit results to 3 flights
    }

    # Make the flight search request
    response = requests.get(flight_search_url, headers=headers, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        flight_data = response.json()
        flights = []
        for flight in flight_data.get("data", [])[:3]:
            offer_id = flight.get("id", "N/A")
            price = flight.get("price", {}).get("total", "N/A")
            airline = flight.get("validatingAirlineCodes", ["N/A"])[0]
            flights.append({"offer_id": offer_id, "price": price, "airline": airline})
        return render_template('results.html', flights=flights)
    else:
        return f"Error: {response.status_code} - {response.text}"

if __name__ == "__main__":
    app.run(debug=True)

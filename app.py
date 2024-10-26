from flask import Flask, request, render_template
import requests
import json

app = Flask(__name__)

# Authentication URL
auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"

# Replace with your Amadeus credentials
client_id = "E0kWNS0pHXmJ8ggvaqJnCreGFAtDQ2r0"
client_secret = "Xj6DkJByszRh4G76"

# Request body for authentication
auth_data = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret
}

# Get an access token
auth_response = requests.post(auth_url, data=auth_data)

if auth_response.status_code == 200:
    access_token = auth_response.json().get("access_token")
else:
    raise Exception(f"Failed to get access token: {auth_response.status_code} - {auth_response.text}")

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

    try:
        # Make the flight search request
        response = requests.get(flight_search_url, headers=headers, params=params)
        response.raise_for_status()

        # Check if the request was successful
        flight_data = response.json()
        flights = []
        for flight in flight_data.get("data", [])[:3]:
            offer_id = flight.get("id", "N/A")
            price = flight.get("price", {}).get("total", "N/A")
            airline = flight.get("validatingAirlineCodes", ["N/A"])[0]
            flights.append({"offer_id": offer_id, "price": price, "airline": airline})

        # Suggest alternative dates for cheaper flights
        alternative_dates = get_alternative_dates(origin, destination, travel_class, adults)

        return render_template('results.html', flights=flights, alternative_dates=alternative_dates)
    except requests.exceptions.RequestException as e:
        return render_template('error.html', error_message="An error occurred while fetching flight data. Please check your input or try again later.")

# Function to get alternative dates for cheaper flights
def get_alternative_dates(origin, destination, travel_class, adults):
    # Define alternative dates to check
    alternative_dates = ["2024-12-14", "2024-12-16", "2024-12-18"]
    cheaper_flights = []

    # Set up headers with the access token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    for date in alternative_dates:
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": date,
            "travelClass": travel_class,
            "adults": adults,
            "max": 1  # Limit results to 1 flight per date
        }

        try:
            response = requests.post(flight_search_url, headers=headers, json=params)

        
            response.raise_for_status()
            flight_data = response.json()
            if flight_data.get("data"):
                flight = flight_data["data"][0]
                price = flight.get("price", {}).get("total", "N/A")
                cheaper_flights.append({"date": date, "price": f"${price}"})
        except requests.exceptions.RequestException:
            continue

    return cheaper_flights

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, request, render_template
import requests

app = Flask(__name__)

# Amadeus API Credentials
client_id = "kCwc4lbI68ll1ET4nC75qQQuAEL1vbpr"
client_secret = "r05gfAspJobZ5WTf"

# Function to get an access token
def get_access_token():
    auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    auth_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    auth_response = requests.post(auth_url, data=auth_data)
    if auth_response.status_code == 200:
        return auth_response.json().get("access_token")
    else:
        raise Exception(f"Failed to get access token: {auth_response.status_code} - {auth_response.text}")

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

    # Get a fresh access token
    access_token = get_access_token()

    # Set up headers with the access token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/vnd.amadeus+json",
        "X-HTTP-Method-Override": "GET"
    }

    # Define the request body for the flight search
    body = {
        "currencyCode": "USD",
        "originDestinations": [
            {
                "id": "1",
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDateTimeRange": {
                    "date": departure_date
                }
            }
        ],
        "travelers": [
            {
                "id": "1",
                "travelerType": "ADULT"
            }
        ],
        "sources": [
            "GDS"
        ]
    }

    try:
        # Make the flight search request (using POST with method override)
        response = requests.post("https://test.api.amadeus.com/v2/shopping/flight-offers", headers=headers, json=body)
        response.raise_for_status()

        # Check if the request was successful
        flight_data = response.json()
        flights = []
        for flight in flight_data.get("data", [])[:3]:
            offer_id = flight.get("id", "N/A")
            price = flight.get("price", {}).get("total", "N/A")
            airline = flight.get("validatingAirlineCodes", ["N/A"])[0]
            flights.append({"offer_id": offer_id, "price": price, "airline": airline})

        return render_template('results.html', flights=flights)
    except requests.exceptions.RequestException as e:
        return render_template('error.html', error_message="An error occurred while fetching flight data. Please check your input or try again later.")

if __name__ == "__main__":
    app.run(debug=True)

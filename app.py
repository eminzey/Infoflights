from flask import Flask, request, render_template
import requests
import json

app = Flask(__name__)

# Replace with your Amadeus credentials
client_id = "E0kWNS0pHXmJ8ggvaqJnCreGFAtDQ2r0"
client_secret = "Xj6DkJByszRh4G76"

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
        response = requests.post(flight_search_url, headers=headers, json=body)
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

    # Get a fresh access token
    access_token = get_access_token()

    # Set up headers with the access token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/vnd.amadeus+json",
        "X-HTTP-Method-Override": "GET"
    }

    for date in alternative_dates:
        body = {
            "currencyCode": "USD",
            "originDestinations": [
                {
                    "id": "1",
                    "originLocationCode": origin,
                    "destinationLocationCode": destination,
                    "departureDateTimeRange": {
                        "date": date
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
            response = requests.post(flight_search_url, headers=headers, json=body)
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

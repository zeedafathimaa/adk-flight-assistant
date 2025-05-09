import os
from dotenv import load_dotenv
import json
import urllib.parse
import requests
from typing import Optional
from flight_search_agent.utils.validate_date_format import validate_date_format
from google.adk.tools.tool_context import ToolContext

# Load environment variables
load_dotenv()
# SerpAPI key
serp_api_key = os.getenv('SERP_API_KEY')

def get_flight_prices(
    tool_context: ToolContext,
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: Optional[str] = None
) -> dict:
    """Search flight prices for a given source and destination.

    Args:
        tool_context (ToolContext): Context for managing tool state
        departure_id (str): Source/From Airport code (IATA, e.g., BLR, IXE)
        arrival_id (str): Destination/To Airport code (IATA, e.g., BOM, DEL)
        outbound_date (str): Departure date in YYYY-MM-DD format
        return_date (Optional[str]): Return date in YYYY-MM-DD format. Defaults to None for one-way.

    Returns:
        dict: Status and flight results or error message
    """
    if not serp_api_key:
        return {
            "status": "error",
            "error_message": "SERP_API_KEY not found in environment variables."
        }

    # Track search history in state
    searches = tool_context.state.get("flight_searches", [])
    current_search = {
        "departure": departure_id,
        "arrival": arrival_id,
        "outbound_date": outbound_date,
        "return_date": return_date
    }
    searches.append(current_search)
    tool_context.state["flight_searches"] = searches

    # Validate date formats
    if not validate_date_format(outbound_date):
        return {
            "status": "error",
            "error_message": f"Invalid outbound date format: '{outbound_date}'. Please use YYYY-MM-DD."
        }

    if return_date and not validate_date_format(return_date):
        return {
            "status": "error",
            "error_message": f"Invalid return date format: '{return_date}'. Please use YYYY-MM-DD."
        }

    # Validate airport codes (simple validation)
    if not (departure_id and len(departure_id) == 3 and departure_id.isalpha()):
        return {
            "status": "error",
            "error_message": f"Invalid departure airport code: '{departure_id}'. Please provide a valid 3-letter IATA code."
        }

    if not (arrival_id and len(arrival_id) == 3 and arrival_id.isalpha()):
        return {
            "status": "error",
            "error_message": f"Invalid arrival airport code: '{arrival_id}'. Please provide a valid 3-letter IATA code."
        }

    # Prepare query parameters for SerpAPI Google Flights engine
    query_params = {
        "api_key": serp_api_key,
        "engine": "google_flights",
        "hl": "en",
        "gl": "in", # Adjust country code if needed
        "departure_id": departure_id.upper(), # Ensure codes are uppercase
        "arrival_id": arrival_id.upper(),     # Ensure codes are uppercase
        "outbound_date": outbound_date,
        "currency": "INR" # Adjust currency if needed
    }
    
    if return_date:
        query_params["return_date"] = return_date
        trip_type = "round-trip"
    else:
        query_params["type"] = 2 # One-way flight
        trip_type = "one-way"

    url = f"https://serpapi.com/search?{urllib.parse.urlencode(query_params)}"

    print(f"DEBUG: Making flight search request to URL: {url}") # Keep for debugging

    try:
        headers = {'Accept': 'application/json'} # Prefer JSON response
        response = requests.get(url, headers=headers, timeout=30)  # Increased timeout

        print(f"DEBUG: Response status code: {response.status_code}") # Keep for debugging

        # Handle specific HTTP error codes
        if response.status_code == 401:
            return {"status": "error", "error_message": "API Authentication Failed (401). Check SerpAPI key."}
        elif response.status_code == 429:
            return {"status": "error", "error_message": "API Rate Limit Exceeded (429). Try again later."}
        elif response.status_code >= 400:
             # General client/server error
             error_detail = f"HTTP Error {response.status_code}. Response: {response.text[:200]}..."
             print(f"DEBUG: {error_detail}")
             return {"status": "error", "error_message": f"Flight search failed with HTTP {response.status_code}. Check parameters or try again."}


        # Try parsing the response as JSON
        try:
            flight_data = response.json()
        except json.JSONDecodeError:
            print(f"DEBUG: Failed JSON parse. Response text: {response.text[:500]}...")
            return {"status": "error", "error_message": "Failed to parse API response. Service might be unavailable."}

        # Check for SerpAPI error messages within the JSON response
        if "error" in flight_data:
             print(f"DEBUG: SerpAPI Error Response: {flight_data['error']}")
             return {"status": "error", "error_message": f"API Error: {flight_data['error']}"}

        # Check if flight results exist
        best_flights = flight_data.get('best_flights', [])
        other_flights = flight_data.get('other_flights', []) # Check for 'other_flights' too
        price_insights = flight_data.get('price_insights') # Useful context

        if not best_flights and not other_flights:
            print(f"DEBUG: No flights found. Full response sample: {json.dumps(flight_data, indent=2)[:500]}")
            message = f"No flights found for {departure_id} to {arrival_id} on {outbound_date}"
            if return_date:
                message += f" returning {return_date}."
            else:
                 message += " (one-way)."
            if price_insights:
                 message += f" Price insights: {price_insights.get('lowest_price', 'N/A')}, typical range: {price_insights.get('price_level', 'N/A')}."

            return {
                "status": "no_results", # Use a specific status
                "message": message,
                "flight_search_params": {
                    "from": departure_id, "to": arrival_id, "outbound_date": outbound_date,
                    "return_date": return_date, "trip_type": trip_type
                }
            }

        # Process and structure flight data
        processed_results = {
            "status": "success",
            "flight_search_params": {
                "from": departure_id, "to": arrival_id, "outbound_date": outbound_date,
                "return_date": return_date, "trip_type": trip_type
            },
            "best_flights": best_flights,
            "other_flights": other_flights, # Include other flights if available
            "price_insights": price_insights # Include price insights
            # "airlines": flight_data.get('airlines', []) # Less critical, can add if needed
        }

        # Store successful results in state
        tool_context.state["last_flight_search"] = processed_results

        return processed_results

    except requests.exceptions.Timeout:
        return {"status": "error", "error_message": "Flight search request timed out. Please try again later."}
    except requests.exceptions.RequestException as e:
        print(f"DEBUG: Request exception: {str(e)}")
        return {"status": "error", "error_message": f"Network error during flight search: {str(e)}"}
    except Exception as e:
        print(f"DEBUG: Unexpected exception in get_flight_prices: {str(e)}")
        return {"status": "error", "error_message": f"An unexpected error occurred: {str(e)}"}
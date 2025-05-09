import os
import json
import urllib.parse
import requests
from dotenv import load_dotenv
from google.adk.tools.tool_context import ToolContext

# Load environment variables
load_dotenv()
# SerpAPI key
serp_api_key = os.getenv('SERP_API_KEY')

def get_airport_code(
    tool_context: ToolContext,
    city_name: str
) -> dict:
    """Get IATA airport code for a given city.

    Args:
        tool_context (ToolContext): Context for managing tool state
        city_name (str): Name of the city

    Returns:
        dict: Status and airport details or error message
    """
    if not serp_api_key:
        return {
            "status": "error",
            "error_message": "SERP_API_KEY not found in environment variables."
        }
        
    try:
        # Store search history in state
        search_history = tool_context.state.get("airport_searches", [])
        print("search history/////////",search_history)
        search_history.append(city_name)
        tool_context.state["airport_searches"] = search_history

        # Use SerpAPI to search for airport codes
        query_params = {
            "api_key": serp_api_key,
            "engine": "google",
            "q": f"{city_name} airport IATA code",
            "hl": "en",
            "gl": "in" # Adjust country code if needed
        }

        url = f"https://serpapi.com/search?{urllib.parse.urlencode(query_params)}"
        response = requests.get(url, timeout=15) # Added timeout
        response.raise_for_status()
        data = json.loads(response.text)

        # Extract knowledge graph if available
        if 'knowledge_graph' in data:
            result = {
                "status": "success",
                "airport_details": data['knowledge_graph']
            }
            # Save successful results to state
            tool_context.state["last_airport_code"] = result
            return result
        # Otherwise return organic results as fallback
        elif 'organic_results' in data:
            result = {
                "status": "success",
                "search_results": data['organic_results'][:3] # Limit results
            }
            # Save successful results to state
            tool_context.state["last_airport_code"] = result
            return result
        else:
            return {
                "status": "error",
                "error_message": f"Could not find airport code for {city_name}"
            }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_message": "Airport code search request timed out."
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error_message": f"Error during airport code search request: {e}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"An unexpected error occurred during airport code search: {e}"
        }


# A Conversational Flight Finder using ADK

## Overview
A simple AI assistant that understands natural language requests for flights.
Can find airport codes for cities.
Searches for flight prices using real-time data (via an API).

## Project Structure

flight_search_assistant/
├── flight_search_agent/
│   ├── agent.py           # The main "brain"
│   ├── tools/
│   │   ├── get_airport_code.py
│   │   └── get_flight_prices.py
│   └── utils/
│       └── validate_date_format.py
├── .env                   # SECRET API KEYS GO HERE!
└── requirements.txt       # List of software needed

## Setup
1. **Clone the Repository**
   ```bash
   git clone https://github.com/zeedafathimaa/adk-flight-assistant.git
   cd adk-flight-assistant
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Create a `.env` file in the root directory with the following content:
   ```
   SERP_API_KEY=
   GOOGLE_API_KEY=
   ```

5. **Start the Assistant Web Interface**
   ```bash
   adk run flight_search_agent
   ```
   or
   ```bash
   adk web 
   ```

## Example Queries
* "Find flights from Mumbai to Delhi on 2025-05-20."
* "Find flights from mumbai to srinagar on 2025-05-11 and return on 2025-05-20."
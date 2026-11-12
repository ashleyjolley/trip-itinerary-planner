

import streamlit as st
import requests
from datetime import timedelta

# -----------------------------
# App setup
# -----------------------------

st.title("Trip Itinerary Planner")

st.write(
    "Create a personalized travel itinerary using real "
    "attractions and destinations from Wikipedia and Wikidata."
)

# API endpoints
WIKIDATA_URL = "https://www.wikidata.org/w/api.php"
WIKIPEDIA_URL = "https://en.wikipedia.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "StudentTripItineraryPlanner/1.0 "
        "(educational Streamlit project)"
    )
}

# -----------------------------
# Find destination coordinates
# -----------------------------

@st.cache_data(ttl=86400)
def get_coordinates(destination):

    # Search Wikidata for the destination
    response = requests.get(
        WIKIDATA_URL,
        params={
            "action": "wbsearchentities",
            "search": destination,
            "language": "en",
            "format": "json",
            "limit": 5
        },
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    results = response.json().get("search", [])

    if not results:
        return None

    # Check candidate entities for coordinates
    for result in results:
        entity_id = result["id"]

        entity_response = requests.get(
            WIKIDATA_URL,
            params={
                "action": "wbgetentities",
                "ids": entity_id,
                "props": "claims",
                "format": "json"
            },
            headers=HEADERS,
            timeout=20
        )

        entity_response.raise_for_status()

        entity = entity_response.json().get(
            "entities", {}
        ).get(entity_id, {})

        coordinates = entity.get(
            "claims", {}
        ).get("P625", [])

        if coordinates:
            value = coordinates[0]["mainsnak"][
                "datavalue"
            ]["value"]

            return value["latitude"], value["longitude"]

    return None


# -----------------------------
# Find nearby Wikipedia places
# -----------------------------

@st.cache_data(ttl=3600)
def get_nearby_places(lat, lon):

    response = requests.get(
        WIKIPEDIA_URL,
        params={
            "action": "query",
            "generator": "geosearch",
            "ggscoord": f"{lat}|{lon}",
            "ggsradius": 10000,
            "ggslimit": 100,
            "prop": "extracts|info",
            "exintro": 1,
            "explaintext": 1,
            "exsentences": 2,
            "inprop": "url",
            "format": "json"
        },
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    pages = response.json().get(
        "query", {}
    ).get("pages", {})

    places = []

    for page in pages.values():

        title = page.get("title", "")
        description = page.get("extract", "")
        url = page.get("fullurl", "")

        # Avoid articles without descriptions
        if not description:
            continue

        places.append({
            "name": title,
            "description": description,
            "url": url
        })

    return places


# -----------------------------
# Categorize recommendations
# -----------------------------

def categorize_place(place):

    text = (
        place["name"] + " " + place["description"]
    ).lower()

    categories = []

    if any(word in text for word in [
        "museum", "gallery", "art collection"
    ]):
        categories.append("Museums")

    if any(word in text for word in [
        "palace", "cathedral", "church",
        "monument", "landmark", "tower"
    ]):
        categories.append("Sightseeing")

    if any(word in text for word in [
        "historic", "history", "castle",
        "ancient", "heritage"
    ]):
        categories.append("Historical Sites")

    if any(word in text for word in [
        "park", "garden", "forest",
        "lake", "river"
    ]):
        categories.append("Outdoor Activities")

    return categories


# -----------------------------
# User inputs
# -----------------------------

st.header("Plan Your Trip")

destination = st.text_input(
    "Where are you traveling?",
    placeholder="Example: Munich, Germany"
)

start_date = st.date_input(
    "When does your trip start?"
)

num_days = st.number_input(
    "How many days is your trip?",
    min_value=1,
    max_value=14,
    value=3
)

activities = st.multiselect(
    "What activities are you interested in?",
    [
        "Sightseeing",
        "Museums",
        "Historical Sites",
        "Outdoor Activities"
    ]
)

# -----------------------------
# Generate itinerary
# -----------------------------

if st.button("Generate My Itinerary"):

    if not destination.strip():
        st.warning("Please enter a destination.")

    elif not activities:
        st.warning("Please select at least one activity.")

    else:
        try:

            with st.spinner(
                "Searching Wikipedia and Wikidata..."
            ):

                coordinates = get_coordinates(destination)

                if coordinates is None:
                    st.error(
                        "Destination not found. "
                        "Try entering the city name only."
                    )

                else:
                    lat, lon = coordinates

                    places = get_nearby_places(lat, lon)

                    # Filter places by selected interests
                    matching_places = []

                    for place in places:
                        place_categories = categorize_place(place)

                        if any(
                            category in activities
                            for category in place_categories
                        ):
                            matching_places.append(place)

                    st.write(f"Total matching attractions found: {len(matching_places)}")
                    if not matching_places:
                        st.warning(
                            "No matching attractions found. "
                            "Try different activity categories."
                        )

                    else:
                        end_date = start_date + timedelta(
                            days=num_days - 1
                        )

                        st.success(
                            "Your itinerary has been created!"
                        )

                        st.header(
                            f"Your Trip to {destination}"
                        )

                        st.write(
                            f"Start Date: {start_date}"
                        )

                        st.write(
                            f"End Date: {end_date}"
                        )

                        st.write(
                            f"Duration: {num_days} days"
                        )

                        st.header("Your Daily Itinerary")

                        # Display up to 3 places per day
                        for day in range(num_days):

                            current_date = (
                                start_date
                                + timedelta(days=day)
                            )

                            st.subheader(
                                f"Day {day + 1}: {current_date}"
                            )

                           
                            # Display up to 3 attractions per day
                            # Reuse recommendations if necessary

                            
                            # Get up to 3 unique attractions per day
                          
                            # Display 1 unique attraction per day
                            if day < len(matching_places):

                                place = matching_places[day]

                                st.write(f"### {place['name']}")

                                st.write(place["description"])

                                if place["url"]:
                                    st.markdown(
                                        f"[Read more on Wikipedia]({place['url']})"
                                    )

                                st.divider()

                            else:
                                st.info(
                                    "No additional attractions found "
                                    "for this day."
                                )



        except requests.RequestException as error:
            st.error(
                "Could not connect to Wikipedia or Wikidata. "
                f"Details: {error}"
            )

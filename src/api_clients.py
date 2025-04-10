import logging
import os
import random
from typing import Any, Dict, List, Optional
import base64

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_solar_schedule(lat: float, long: float) -> Dict[str, Any]:
    """
    Fetch the solar schedule (sunrise, sunset, etc.) for a given latitude and longitude.

    Args:
        lat (float): Latitude of the location.
        long (float): Longitude of the location.

    Returns:
        Dict[str, Any]: A dictionary containing solar schedule data such as sunrise and sunset times.
                        Returns an empty dictionary if an error occurs or if the API response is invalid.
    """
    SOLAR_SCHEDULE_URL = "https://api.sunrisesunset.io/json"
    params = {"lat": lat, "lng": long}
    try:
        response = requests.get(url=SOLAR_SCHEDULE_URL, params=params, timeout=10)
        response.raise_for_status()  # Ensure the response status is 2xx.
        data = response.json()
        if "results" in data:
            return data["results"]
        else:
            logging.warning("No 'results' key found in the API response.")
    except Exception as e:
        logging.error(f"Error fetching solar schedule data: {e}")
    return {}


def get_zen_quote() -> Dict[str, str]:
    """Fetch a random Zen quote.

    Returns:
        Dict[str, str]: Dictionary with keys 'quote' and 'author'.
                        Returns an empty dictionary if an error occurs.
    """
    ZEN_QUOTE_URL = "https://zenquotes.io/api/random"
    try:
        response = requests.get(url=ZEN_QUOTE_URL, timeout=10)
        response.raise_for_status()
        data = response.json()[0]
        return {
            "quote": data["q"],
            "author": data.get(
                "a", "Unknown"
            ),  # Default to "Unknown" if author key is not found
        }
    except Exception as e:
        logging.error(f"Error fetching Zen quote: {e}")
    return {}


def get_stoic_quote() -> Dict[str, str]:
    """Fetch a random Stoic quote.

    Returns:
        Dict[str, str]: Dictionary with keys 'quote' and 'author'.
                        Returns an empty dictionary if an error occurs.
    """
    STOIC_QUOTE_URL = "https://stoic.tekloon.net/stoic-quote"
    try:
        response = requests.get(url=STOIC_QUOTE_URL, timeout=10)
        response.raise_for_status()
        data = response.json()["data"]
        return {
            "quote": data["quote"],
            "author": data.get(
                "author", "Unknown"
            ),  # Default to "Unknown" if author key is not found
        }
    except Exception as e:
        logging.error(f"Error fetching Zen quote: {e}")
    return {}


def get_bible_verse() -> Dict[str, str]:
    """Fetch a random Bible verse from the Gospels.

    Returns:
        Dict[str, str]: Dictionary with keys 'reference' and 'verse'.
                        Returns an empty dictionary if an error occurs.
    """
    BIBLE_URL = "https://bible-api.com/data/web/random"
    try:
        response = requests.get(url=BIBLE_URL, timeout=10)
        response.raise_for_status()
        data = response.json().get("random_verse", {})  # Use .get() to avoid KeyError

        text = data["text"]
        # Use .get() with default values for missing keys
        book = data.get("book", "Unknown Book")
        chapter = data.get("chapter", "0")
        verse_number = data.get("verse", "0")

        reference = f"{book} {chapter}:{verse_number}"
        return {"reference": reference, "verse": text}

    except Exception as e:
        logging.error(f"Error fetching Bible verse: {e}")
    return {}


def get_useless_fact() -> str:
    """Fetch a random interesting fact.

    Returns:
        Optional[Dict[str, str]]: Dictionary with key 'fact', or None if error.
    """
    USELESS_FACT_URL = "https://uselessfacts.jsph.pl/api/v2/facts/random"
    try:
        response = requests.get(url=USELESS_FACT_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["text"]
    except Exception as e:
        logging.error(f"Error: {e}")
    return ""


def get_recipe_of_the_day() -> Dict[str, str]:
    """Fetch a random recipe.

    Returns:
        Optional[Dict[str, str]]: Dictionary with keys 'name', 'instructions', 'image_url', and 'youtube_url', or None if error.
    """
    RECIPE_URL = "https://www.themealdb.com/api/json/v1/1/random.php"
    try:
        response = requests.get(url=RECIPE_URL, timeout=10)
        response.raise_for_status()
        meal = response.json()["meals"][0]
        return {
            "name": meal["strMeal"],
            "instructions": meal["strInstructions"],
            "image_url": meal["strMealThumb"],
            "youtube_url": meal.get("strYoutube", ""),
        }
    except Exception as e:
        logging.error(f"Error: {e}")
    return {}


def get_arxiv_papers(
    query: str,
    max_results: int = 100,
    random_k: int = 3,
) -> List[Dict[str, str]]:
    """
    Fetch a list of papers from arXiv using BeautifulSoup.

    Args:
        query (str): The search query (after "all:").
        max_results (int): Number of papers to retrieve.
        random_k (int): Number of random papers to select from the retrieved list.

    Returns:
        List[Dict[str, str]]: List of dictionaries with keys 'title', 'abstract', 'published', 'pdf_link',
                              'local_path', and 's3_path'. Returns an empty list if an error occurred.
    """
    try:
        base_url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()

        # Parse the XML response with BeautifulSoup.
        soup = BeautifulSoup(response.text, features="lxml")
        entries = soup.find_all("entry")
        if not entries:
            logging.warning("No entries found in arXiv feed.")
            return []

        # Adjust random_k if necessary.
        if random_k > len(entries):
            logging.warning(
                "random_k (%d) is greater than the number of retrieved papers (%d). Returning all papers.",
                random_k,
                len(entries),
            )
            random_k = len(entries)

        selected_entries = random.sample(entries, random_k)
        papers = []

        for entry in selected_entries:
            title = entry.title.text.strip()
            abstract = entry.summary.text.strip()
            published = entry.published.text.strip()

            pdf_link_tag = entry.find("link", title="pdf")
            pdf_link = (
                pdf_link_tag["href"]
                if pdf_link_tag and pdf_link_tag.has_attr("href")
                else None
            )

            papers.append(
                {
                    "title": title,
                    "abstract": abstract,
                    "published": published,
                    "pdf_link": pdf_link,
                }
            )

        return papers

    except Exception as e:
        logging.error("Unexpected error while fetching arXiv papers: %s", e)
    return []


def get_word_of_the_day() -> list[dict]:
    """Fetch the Word of the Day from Dictionary.com.

    Returns:
        dict: A dictionary with keys 'word', 'part_of_speech', and 'definition', or None if an error occurred.
    """
    DICTIONARY_URL = "https://www.dictionary.com/e/word-of-the-day/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url=DICTIONARY_URL, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        word = soup.select_one(
            ".otd-item-headword .otd-item-headword__word h1"
        ).get_text(strip=True)
        pos = soup.select_one(
            ".otd-item-headword .otd-item-headword__pos span.italic"
        ).get_text(strip=True)
        definition = soup.select(".otd-item-headword .otd-item-headword__pos p")[
            1
        ].get_text(strip=True)

        return {"word": word, "part_of_speech": pos, "definition": definition}

    except Exception as e:
        logging.error(f"Error parsing Word of the Day page: {e}")
        return {}


def get_poem_of_the_day() -> Dict[str, str]:
    """Fetch the Poem of the Day from Poetry Foundation.

    Returns:
        Dict[str, str]: Dictionary with keys 'title', 'author', and 'poem'.
                        Returns an empty dictionary if an error occurs or if the title is missing.
    """
    POEM_URL = "https://www.poetryfoundation.org/poems/poem-of-the-day"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url=POEM_URL, headers=headers, timeout=15)
        response.raise_for_status()

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract the title (mandatory)
        # 1. Title Selector: Selects the <h4> element with class 'type-gamma'.
        title = soup.select_one("h4.type-gamma").get_text(strip=True)

        # Extract the author (optional, defaults to "Unknown")
        # 2. Author Selector: Selects the innermost <span> inside a <span> inside a <div> with class 'type-kappa'.
        author_tag = soup.select_one("div.type-kappa span span")
        author = author_tag.get_text(strip=True) if author_tag else "Unknown"

        # Extract the poem text and preserve line breaks
        # 3. Poem Text Selector: Selects the <div> containing the poem, identifiable by classes like 'rich-text' and 'md:text-xl'.
        # We use a partial class match '[class*="md:text-xl"]' for robustness, assuming this class is unique to the poem div.
        poem_div = soup.select_one('div.rich-text[class*="md:text-xl"]')
        for br in poem_div.find_all("br"):
            br.replace_with("\n")  # Replace <br> tags with newline characters
        poem = poem_div.get_text()  # Do not use strip=True to preserve newlines

        # Return the poem details
        return {"title": title, "author": author, "poem": poem}

    except Exception as e:
        logging.error(f"Error fetching Poem of the Day: {e}", exc_info=True)
        # Optional: Log a snippet of the HTML for debugging if things fail
        # logging.debug(f"HTML Snippet: {soup.prettify()[:2000]}")
        return {}


def get_horoscope(sign: str) -> Dict[str, str]:
    """Fetches the daily horoscope for a given zodiac sign.

    Args:
        sign (str): The zodiac sign (e.g., 'aries', 'leo').

    Returns:
        Dict[str, str]: Dictionary with keys 'sign', 'prediction', 'date'.
                        Returns an empty dictionary if an error occurs.
    """
    HOROSCOPE_URL = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
    params = {"sign": sign}  # Ensure sign is lowercase

    try:
        response = requests.get(url=HOROSCOPE_URL, params=params, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()["data"]
        return {
            "sign": sign,  # Use original sign case for return
            "prediction": data["horoscope_data"],
            "date": data["date"],
        }
    except Exception as e:
        logging.error(f"Error fetching horoscope for sign '{sign}': {e}")
    return {}


def get_places(
    api_key: str,
    text_query: str,
    bounding_coordinates: Dict[str, Dict[str, float]],
    place_type: Optional[str] = None,
    page_size: int = 10,
    min_rating: Optional[float] = None,
    price_levels: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Searches for places (e.g., restaurants, cafes, bars) in a specified location using the Google Places API.

    Args:
        api_key (str): Your Google Cloud API Key with Places API enabled.
        text_query (str): The search term (e.g., "vegetarian ramen").
        bounding_coordinates (Dict[str, Dict[str, float]]): Coordinates for the search area. It should include
            "low" and "high" for latitude and longitude.
        place_type (Optional[str]): The type of place to search for (e.g., "restaurant", "cafe").
            Defaults to None (no filtering).
        page_size (int): The maximum number of results to return. Defaults to 10.
            The API caps this at 20, so this will be used as the page size.
        min_rating (Optional[float]): Minimum rating to filter results. Defaults to None (no filtering).
        price_levels (Optional[List[str]]): List of price levels to filter results (e.g.,
            ["PRICE_LEVEL_INEXPENSIVE", "PRICE_LEVEL_MODERATE"]). Defaults to None (no filtering).

    Returns:
        List[Dict[str, Any]]: A list of places matching the query, with fields such as name, address, rating,
            user ratings, photo URL, and reviews. Returns an empty list if an error occurs.
    """

    # --- Constants ---
    PLACES_API_URL = "https://places.googleapis.com/v1/places:searchText"

    # --- Define Headers and Fields ---
    fields = [
        "places.displayName",
        "places.formattedAddress",
        "places.rating",
        "places.userRatingCount",
        "places.reviews",
        "places.photos",
    ]

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": ",".join(fields),
    }

    # --- Build JSON Payload ---
    payload = {
        "textQuery": text_query,
        "pageSize": page_size,
        "locationRestriction": {
            "rectangle": {
                "low": {
                    "latitude": bounding_coordinates["low"]["latitude"],
                    "longitude": bounding_coordinates["low"]["longitude"],
                },
                "high": {
                    "latitude": bounding_coordinates["high"]["latitude"],
                    "longitude": bounding_coordinates["high"]["longitude"],
                },
            }
        },
        "includedType": place_type,
        **({"priceLevels": price_levels} if price_levels else {}),
        **({"minRating": min_rating} if min_rating else {}),
    }

    # --- Make API Request & Process ---
    processed_places = []
    try:
        response = requests.post(
            PLACES_API_URL, headers=headers, json=payload, timeout=15
        )
        response.raise_for_status()
        results = response.json()

        places = results["places"]

        for place in places:
            processed_place = {
                "name": place.get("displayName", {}).get("text", "N/A"),
                "address": place.get("formattedAddress", "N/A"),
                "rating": place.get("rating"),
                "user_ratings_total": place.get("userRatingCount"),
                "price_level": place.get("priceLevel"),
                "photo_base64": None,  # Initialize photo data key
            }

            # --- Fetch and Encode Photo ---
            photos = place.get("photos", [])
            if photos:
                photo_name = photos[0].get(
                    "name"
                )  # Get resource name of the first photo
                if photo_name:
                    photo_media_url = f"https://places.googleapis.com/v1/{photo_name}/media?maxWidthPx=400&key={api_key}"
                    try:
                        logging.debug(
                            f"Fetching photo for {processed_place['name']}..."
                        )
                        photo_response = requests.get(photo_media_url, timeout=10)
                        photo_response.raise_for_status()

                        # Get image bytes and encode to Base64 string
                        image_bytes = photo_response.content
                        base64_image = base64.b64encode(image_bytes).decode("utf-8")
                        processed_place["photo_base64"] = base64_image
                        logging.debug(
                            f"Successfully encoded photo for {processed_place['name']}"
                        )

                    except requests.exceptions.RequestException as photo_err:
                        logging.warning(
                            f"Failed to download photo for {processed_place['name']} from {photo_name}: {photo_err}"
                        )
                    except Exception as enc_err:
                        logging.warning(
                            f"Failed to encode photo for {processed_place['name']}: {enc_err}"
                        )

            # --- Process Reviews ---
            reviews = []
            for review in place.get("reviews", [])[:3]:
                review_text = review.get("text", {}).get("text")
                if review_text:  # Only add if text exists
                    reviews.append(
                        {
                            "reviewer_name": review.get("authorAttribution", {}).get(
                                "displayName", "Anonymous"
                            ),
                            "text": review_text,
                            "rating": review.get("rating"),
                        }
                    )
            processed_place["reviews"] = reviews

            processed_places.append(processed_place)

        # Return results up to the originally requested page_size (or less if API returned fewer)
        return processed_places[:page_size]

    except Exception as e:
        logging.error(
            f"Error fetching places for query '{text_query}': {e}", exc_info=True
        )
        return []


def get_nearby_places(
    api_key: str,
    coordinates: tuple[float, float],
    place_types: List[str],
    search_radius: float = 1000,
    page_size: int = 10,
) -> List[Dict[str, Any]]:
    """
    Searches for nearby places using the Google Places v1 Nearby Search API.

    Args:
        api_key (str): Your Google Cloud API Key with Places API enabled.
        coordinates (tuple[float, float]): A tuple containing the latitude and longitude of the search center.
        place_types (List[str]): A list of place types to filter the search (e.g., ["restaurant", "cafe"]).
        search_radius (float, optional): The radius (in meters) around the coordinates to search. Defaults to 1000.
        page_size (int, optional): The maximum number of results to return. Defaults to 10.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each representing a place. Each dictionary contains:
            - "name" (str): The name of the place.
            - "address" (str): The formatted address of the place.
            - "rating" (float): The average rating of the place.
            - "user_ratings_total" (int): The total number of user ratings for the place.
            - "photo_url" (str): A URL to a photo of the place (if available).
    """
    NEARBY_PLACES_API_URL = "https://places.googleapis.com/v1/places:searchNearby"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.photos",  # Add more fields if needed
    }

    body = {
        "includedTypes": place_types,
        "maxResultCount": page_size,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": coordinates[0], "longitude": coordinates[1]},
                "radius": search_radius,
            }
        },
    }

    try:
        response = requests.post(
            url=NEARBY_PLACES_API_URL, headers=headers, json=body, timeout=15
        )
        response.raise_for_status()
        results = response.json()

        places = results.get("places", [])
        logging.info(
            f"Found {len(places)} places near ({coordinates[0]}, {coordinates[1]})."
        )

        processed_places: List[Dict[str, Any]] = []
        for place in places:
            processed_place = {
                "name": place.get("displayName", {}).get("text"),
                "address": place.get("formattedAddress"),
                "rating": place.get("rating"),
                "user_ratings_total": place.get("userRatingCount"),
                "photo_url": None,
            }

            # Process photo (optional: only if photos field is requested and present)
            if "photos" in place and place["photos"]:
                photo_name = place["photos"][0].get("name")
                if photo_name:
                    processed_place["photo_url"] = (
                        f"https://places.googleapis.com/v1/{photo_name}/media?maxWidthPx=400&key={api_key}"
                    )

            processed_places.append(processed_place)

        return processed_places

    except Exception as e:
        logging.exception(f"Unexpected error during Nearby Search v1: {e}")
        return []


def get_nearby_places_legacy(
    api_key: str,
    coordinates: tuple[float, float],
    keyword: Optional[str] = None,
    type: Optional[str] = None,
    search_radius: float = 1000,
) -> List[Dict[str, Any]]:
    """
    Searches for nearby places based on a coordinate using
    the Google Places API Nearby Search endpoint. It applies filters such as place types
    and returns up to `num_results` places with processed review and photo URL fields.
    """
    # --- Constants ---
    NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    # --- Build URL Parameters ---
    params = {
        "location": f"{coordinates[0]},{coordinates[1]}",  # latitude, longitude
        "radius": search_radius,
        "keyword": keyword,
        "type": type,
        "key": api_key,
    }

    # --- Make API Request & Process the Response ---
    try:
        response = requests.get(NEARBY_SEARCH_URL, params=params, timeout=15)
        response.raise_for_status()
        results = response.json()

        places = results.get("results", [])
        logging.info(
            f"Found {len(places)} places near ({coordinates[0]}, {coordinates[1]})."
        )

        processed_places: List[Dict[str, Any]] = []
        for place in places:
            # Process basic information
            processed_place = {
                "name": place.get("name"),
                "address": place.get("vicinity"),
                "rating": place.get("rating"),
                "user_ratings_total": place.get("user_ratings_total"),
            }

            # Process photo (if available)
            photo_url = None
            photos = place.get("photos", [])
            if photos:
                photo_reference = photos[0].get("photo_reference")
                if photo_reference:
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={api_key}"
            processed_place["photo_url"] = photo_url

            # Process up to 3 reviews (if available)
            processed_reviews = []
            for review in place.get("reviews", [])[:3]:
                processed_reviews.append(
                    {
                        "reviewer_name": review.get("author_name", "Anonymous"),
                        "text": review.get("text", ""),
                        "rating": review.get("rating"),
                    }
                )
            processed_place["reviews"] = processed_reviews

            processed_places.append(processed_place)

        return processed_places

    except requests.RequestException as e:
        logging.error(f"Error during Nearby Search: {e}", exc_info=True)
        return []
    except Exception as e:
        logging.exception(f"Unexpected error during Nearby Search: {e}")
        return []


def main() -> None:
    """Main function to call all API functions and print the results."""
    # Call the API functions
    sun = get_solar_schedule(1.3521, 103.8198)  # Singapore coordinates
    zen = get_zen_quote()
    stoic = get_stoic_quote()
    verse = get_bible_verse()
    word = get_word_of_the_day()
    fact = get_useless_fact()
    recipe = get_recipe_of_the_day()
    papers = get_arxiv_papers(
        query="object detection",
        random_k=3,
    )
    poem = get_poem_of_the_day()
    horoscope = get_horoscope("Scorpio")  # Example zodiac sign

    # Print the results
    print(sun)
    print(zen)
    print(stoic)
    print(verse)
    print(word)
    print(fact)
    print(recipe)
    print(papers)
    print(poem)
    print(horoscope)

    # Load Google Maps API key
    load_dotenv()  # Load variables from .env file
    google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")  # Get the key

    geolocation_coordinates = {
        "center": {"latitude": 1.357107, "longitude": 103.8194992},
        "low": {"latitude": 1.1285402, "longitude": 103.5666667},
        "high": {"latitude": 1.5143183, "longitude": 104.5716696},
    }

    text_query = "fried chicken"
    places = get_places(
        api_key=google_maps_api_key,
        text_query=text_query,
        bounding_coordinates=geolocation_coordinates,
        place_type="cafe",
        min_rating=4.0,
    )
    for i, place in enumerate(places):
        print(f"{i + 1}. Name: {place.get('name', 'N/A')}")
        print(f"Address: {place.get('address', 'N/A')}")
        print(
            f"Rating: {place.get('rating', 'N/A')} ({place.get('user_ratings_total', '0')} ratings)"
        )

        reviews = place.get("reviews", [])
        print(f"Total Reviews: {len(reviews)}")
        for review in reviews:
            reviewer = review.get("reviewer_name", "Anonymous")
            rating = review.get("rating", "N/A")
            text = review.get("text", "").strip()
            short_text = text[:80] + ("..." if len(text) > 80 else "")
            print(f'- {reviewer} ({rating}★): "{short_text}"')

        print(f"Photo URL: {place.get('photo_url', 'N/A')}")
    print()

    # --- Randomly select a coordinate within the bounding rectangle ---
    low_lat = geolocation_coordinates["low"]["latitude"]
    high_lat = geolocation_coordinates["high"]["latitude"]
    low_lng = geolocation_coordinates["low"]["longitude"]
    high_lng = geolocation_coordinates["high"]["longitude"]

    random_coordinates = (
        random.uniform(low_lat, high_lat),
        random.uniform(low_lng, high_lng),
    )

    # Call the function using a list of place types.
    places = get_nearby_places(
        api_key=google_maps_api_key,
        coordinates=random_coordinates,
        place_types=["restaurant", "tourist_attraction"],
        search_radius=1000,
        page_size=5,
    )
    for i, place in enumerate(places):
        print(f"{i + 1}. Name: {place.get('name', 'N/A')}")
        print(f"Address: {place.get('address', 'N/A')}")
        print(
            f"Rating: {place.get('rating', 'N/A')} ({place.get('user_ratings_total', '0')} ratings)"
        )

        reviews = place.get("reviews", [])
        print(f"Total Reviews: {len(reviews)}")
        for review in reviews:
            reviewer = review.get("reviewer_name", "Anonymous")
            rating = review.get("rating", "N/A")
            text = review.get("text", "").strip()
            short_text = text[:80] + ("..." if len(text) > 80 else "")
            print(f'- {reviewer} ({rating}★): "{short_text}"')

        print(f"Photo URL: {place.get('photo_url', 'N/A')}")
    print()


if __name__ == "__main__":
    main()

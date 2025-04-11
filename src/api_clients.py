"""
This module provides functions to retrieve various pieces of content from
online APIs and web pages, such as the solar schedule, quotes, Bible verses,
useless facts, recipes, arXiv papers, Word of the Day, Poem of the Day, horoscopes,
and places data via Google Places APIs. It also contains a main() function to
demonstrate and print the outputs from these functions.
"""

import base64
import logging
import os
import random
from typing import Any, Dict, List, Optional
import warnings

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Suppress warnings related to BeautifulSoup parsing
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def get_solar_schedule(lat: float, long: float) -> Dict[str, Any]:
    """
    Fetch the solar schedule (sunrise, sunset, etc.) for a given latitude and longitude.

    Args:
        lat (float): Latitude of the location.
        long (float): Longitude of the location.

    Returns:
        Dict[str, Any]: A dictionary containing solar schedule data such as sunrise and sunset times.
                        Returns an empty dictionary if an error occurs.
    """
    SOLAR_SCHEDULE_URL = "https://api.sunrisesunset.io/json"
    params = {"lat": lat, "lng": long}
    try:
        response = requests.get(url=SOLAR_SCHEDULE_URL, params=params, timeout=10)
        response.raise_for_status()  # Ensure response status is 2xx.
        data = response.json()
        if "results" in data:
            return data["results"]
        else:
            logging.warning("No 'results' key found in the API response.")
    except Exception as e:
        logging.error(f"Error fetching solar schedule data: {e}")
    return {}


def get_zen_quote() -> Dict[str, str]:
    """
    Fetch a random Zen quote.

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
            "author": data.get("a", "Unknown"),
        }
    except Exception as e:
        logging.error(f"Error fetching Zen quote: {e}")
    return {}


def get_stoic_quote() -> Dict[str, str]:
    """
    Fetch a random Stoic quote.

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
            "author": data.get("author", "Unknown"),
        }
    except Exception as e:
        logging.error(f"Error fetching Stoic quote: {e}")
    return {}


def get_bible_verse() -> Dict[str, str]:
    """
    Fetch a random Bible verse from the Gospels.

    Returns:
        Dict[str, str]: Dictionary with keys 'reference' and 'verse'.
                        Returns an empty dictionary if an error occurs.
    """
    BIBLE_URL = "https://bible-api.com/data/web/random"
    try:
        response = requests.get(url=BIBLE_URL, timeout=10)
        response.raise_for_status()
        data = response.json().get("random_verse", {})
        text = data["text"]
        book = data.get("book", "Unknown Book")
        chapter = data.get("chapter", "0")
        verse_number = data.get("verse", "0")
        reference = f"{book} {chapter}:{verse_number}"
        return {"reference": reference, "verse": text}
    except Exception as e:
        logging.error(f"Error fetching Bible verse: {e}")
    return {}


def get_useless_fact() -> str:
    """
    Fetch a random interesting fact.

    Returns:
        str: A fact as a string. Returns an empty string if an error occurs.
    """
    USELESS_FACT_URL = "https://uselessfacts.jsph.pl/api/v2/facts/random"
    try:
        response = requests.get(url=USELESS_FACT_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["text"]
    except Exception as e:
        logging.error(f"Error fetching useless fact: {e}")
    return ""


def get_recipe_of_the_day() -> Dict[str, str]:
    """
    Fetch a random recipe.

    Returns:
        Dict[str, str]: Dictionary with keys 'name', 'instructions', 'image_url', and 'youtube_url'.
                        Returns an empty dictionary if an error occurs.
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
        logging.error(f"Error fetching recipe: {e}")
    return {}


def get_arxiv_papers(
    query: str, max_results: int = 100, random_k: int = 3
) -> List[Dict[str, str]]:
    """
    Fetch a list of papers from arXiv using BeautifulSoup.

    Args:
        query (str): The search query (after "all:").
        max_results (int): Number of papers to retrieve.
        random_k (int): Number of random papers to select from the retrieved list.

    Returns:
        List[Dict[str, str]]: List of dictionaries with keys 'title', 'abstract', 'published',
                              and 'pdf_link'. Returns an empty list if an error occurred.
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

        soup = BeautifulSoup(response.text, features="lxml")
        entries = soup.find_all("entry")
        if not entries:
            logging.warning("No entries found in arXiv feed.")
            return []

        # Adjust random_k if more than available entries
        if random_k > len(entries):
            logging.warning(
                "random_k (%d) is greater than retrieved papers (%d). Returning all papers.",
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


def get_word_of_the_day() -> Dict[str, str]:
    """
    Fetch the Word of the Day from Dictionary.com.

    Returns:
        Dict[str, str]: A dictionary with keys 'word', 'part_of_speech', and 'definition'.
                        Returns an empty dictionary if an error occurs.
    """
    DICTIONARY_URL = "https://www.dictionary.com/e/word-of-the-day/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    try:
        response = requests.get(url=DICTIONARY_URL, headers=headers, timeout=10)
        response.raise_for_status()

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
    """
    Fetch the Poem of the Day from Poetry Foundation.

    Returns:
        Dict[str, str]: A dictionary with keys 'title', 'author', and 'poem'.
                        Returns an empty dictionary if an error occurs.
    """
    POEM_URL = "https://www.poetryfoundation.org/poems/poem-of-the-day"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    }
    try:
        response = requests.get(url=POEM_URL, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract title from the designated header element.
        title = soup.select_one("h4.type-gamma").get_text(strip=True)

        # Extract author if present; default to "Unknown"
        author_tag = soup.select_one("div.type-kappa span span")
        author = author_tag.get_text(strip=True) if author_tag else "Unknown"

        # Extract poem text, preserving line breaks by replacing <br> tags with newline characters.
        poem_div = soup.select_one('div.rich-text[class*="md:text-xl"]')
        for br in poem_div.find_all("br"):
            br.replace_with("\n")
        poem = poem_div.get_text()

        return {"title": title, "author": author, "poem": poem}

    except Exception as e:
        logging.error(f"Error fetching Poem of the Day: {e}", exc_info=True)
        return {}


def get_horoscope(sign: str) -> Dict[str, str]:
    """
    Fetch the daily horoscope for a given zodiac sign.

    Args:
        sign (str): The zodiac sign (e.g., 'aries', 'leo').

    Returns:
        Dict[str, str]: Dictionary with keys 'sign', 'prediction', 'date'.
                        Returns an empty dictionary if an error occurs.
    """
    HOROSCOPE_URL = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
    params = {"sign": sign}
    try:
        response = requests.get(url=HOROSCOPE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()["data"]
        return {
            "sign": sign,
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
    Searches for places (e.g., restaurants, cafes) in a specified location using the Google Places API.

    Args:
        api_key (str): Google Cloud API key with Places API enabled.
        text_query (str): The search term (e.g., "vegetarian ramen").
        bounding_coordinates (Dict[str, Dict[str, float]]): Coordinates for the search area with "low" and "high" keys.
        place_type (Optional[str]): Type of place to search (e.g., "restaurant", "cafe").
        page_size (int): Maximum number of results.
        min_rating (Optional[float]): Minimum rating for filtering results.
        price_levels (Optional[List[str]]): List of price level filters.

    Returns:
        List[Dict[str, Any]]: A list of processed places including details like name, address, rating, and photo (Base64 encoded).
                              Returns an empty list if an error occurs.
    """
    PLACES_API_URL = "https://places.googleapis.com/v1/places:searchText"

    # Fields to request
    fields = [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.rating",
        "places.userRatingCount",
        "places.reviews",
        "places.photos",
        "places.googleMapsLinks",
    ]
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": ",".join(fields),
    }

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
                "id": place.get("id"),
                "name": place.get("displayName", {}).get("text", "N/A"),
                "address": place.get("formattedAddress", "N/A"),
                "rating": place.get("rating"),
                "user_ratings_total": place.get("userRatingCount"),
                "price_level": place.get("priceLevel"),
                "photo_base64": None,  # Initialize photo key
                "google_map_link": f"https://www.google.com/maps/search/?api=1&query={place.get('formattedAddress', 'address')}&query_place_id={place.get('id')}",
            }

            # Fetch and encode photo if available.
            photos = place.get("photos", [])
            if photos:
                photo_name = photos[0].get("name")
                if photo_name:
                    photo_media_url = f"https://places.googleapis.com/v1/{photo_name}/media?maxWidthPx=400&key={api_key}"
                    try:
                        logging.debug(
                            f"Fetching photo for {processed_place['name']}..."
                        )
                        photo_response = requests.get(photo_media_url, timeout=10)
                        photo_response.raise_for_status()
                        image_bytes = photo_response.content
                        processed_place["photo_base64"] = base64.b64encode(
                            image_bytes
                        ).decode("utf-8")
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

            # Process reviews and include up to three.
            reviews = []
            for review in place.get("reviews", [])[:3]:
                review_text = review.get("text", {}).get("text")
                if review_text:
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
        api_key (str): Google Cloud API key with Places API enabled.
        coordinates (tuple[float, float]): Latitude and longitude as a tuple.
        place_types (List[str]): List of place types (e.g., ["restaurant", "cafe"]).
        search_radius (float, optional): Radius in meters around the coordinates. Defaults to 1000.
        page_size (int, optional): Maximum number of results. Defaults to 10.

    Returns:
        List[Dict[str, Any]]: A list of processed places with details like name, address, rating, user ratings, and photo URL.
    """
    NEARBY_PLACES_API_URL = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.photos",
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

        processed_places = []
        for place in places:
            processed_place = {
                "name": place.get("displayName", {}).get("text"),
                "address": place.get("formattedAddress"),
                "rating": place.get("rating"),
                "user_ratings_total": place.get("userRatingCount"),
                "photo_url": None,
            }

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
    Searches for nearby places using the legacy Google Places API Nearby Search endpoint.

    Args:
        api_key (str): Google Cloud API key.
        coordinates (tuple[float, float]): Latitude and longitude.
        keyword (Optional[str]): Keyword to filter search results.
        type (Optional[str]): Specific type of place.
        search_radius (float, optional): Radius in meters for the search. Defaults to 1000.

    Returns:
        List[Dict[str, Any]]: A list of processed places with details like name, address, rating, and photo URL.
                              Returns an empty list if an error occurs.
    """
    NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{coordinates[0]},{coordinates[1]}",
        "radius": search_radius,
        "keyword": keyword,
        "type": type,
        "key": api_key,
    }
    try:
        response = requests.get(NEARBY_SEARCH_URL, params=params, timeout=15)
        response.raise_for_status()
        results = response.json()
        places = results.get("results", [])
        logging.info(
            f"Found {len(places)} places near ({coordinates[0]}, {coordinates[1]})."
        )

        processed_places = []
        for place in places:
            processed_place = {
                "name": place.get("name"),
                "address": place.get("vicinity"),
                "rating": place.get("rating"),
                "user_ratings_total": place.get("user_ratings_total"),
            }
            photo_url = None
            photos = place.get("photos", [])
            if photos:
                photo_reference = photos[0].get("photo_reference")
                if photo_reference:
                    photo_url = (
                        f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference="
                        f"{photo_reference}&key={api_key}"
                    )
            processed_place["photo_url"] = photo_url

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
    """
    Main function to call all API functions and print the results.
    Demonstrates the retrieval of various data items.
    """
    # Retrieve different pieces of content
    solar_schedule = get_solar_schedule(1.3521, 103.8198)  # Singapore coordinates
    zen_quote = get_zen_quote()
    stoic_quote = get_stoic_quote()
    bible_verse = get_bible_verse()
    word_of_the_day = get_word_of_the_day()
    useless_fact = get_useless_fact()
    recipe = get_recipe_of_the_day()
    arxiv_papers = get_arxiv_papers(query="object detection", random_k=3)
    poem = get_poem_of_the_day()
    horoscope = get_horoscope("Scorpio")  # Example zodiac sign

    # Print the results of each API call
    print(solar_schedule)
    print(zen_quote)
    print(stoic_quote)
    print(bible_verse)
    print(word_of_the_day)
    print(useless_fact)
    print(recipe)
    print(arxiv_papers)
    print(poem)
    print(horoscope)

    # Load Google Maps API key from .env file
    load_dotenv()
    google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    # Set up bounding coordinates for Singapore as default location
    bounding_coords = {
        "center": {"latitude": 1.357107, "longitude": 103.8194992},
        "low": {"latitude": 1.1285402, "longitude": 103.5666667},
        "high": {"latitude": 1.5143183, "longitude": 104.5716696},
    }

    # Test get_places: using a text query and filtering options
    text_query = "fried chicken"
    places = get_places(
        api_key=google_maps_api_key,
        text_query=text_query,
        bounding_coordinates=bounding_coords,
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

    # Randomly select a coordinate within the bounding rectangle.
    low_lat = bounding_coords["low"]["latitude"]
    high_lat = bounding_coords["high"]["latitude"]
    low_lng = bounding_coords["low"]["longitude"]
    high_lng = bounding_coords["high"]["longitude"]
    random_coordinates = (
        random.uniform(low_lat, high_lat),
        random.uniform(low_lng, high_lng),
    )

    # Test get_nearby_places using a list of place types.
    nearby_places = get_nearby_places(
        api_key=google_maps_api_key,
        coordinates=random_coordinates,
        place_types=["restaurant", "tourist_attraction"],
        search_radius=1000,
        page_size=5,
    )
    for i, place in enumerate(nearby_places):
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

"""
This module provides functions to retrieve various pieces of content from
online APIs and web pages, such as the solar schedule, quotes, Bible verses,
useless facts, recipes, arXiv papers, Word of the Day, Poem of the Day, horoscopes.
"""

import logging
import random
from typing import Any, Dict, List
import warnings

import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

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


if __name__ == "__main__":
    main()

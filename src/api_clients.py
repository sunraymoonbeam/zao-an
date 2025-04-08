import logging
import os
import random
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup



logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_solar_schedule(lat: float, long: float) -> Dict[str, Any]:
    url = "https://api.sunrisesunset.io/json"
    params = {"lat": lat, "lng": long}
    try:
        response = requests.get(url=url, params=params, timeout=10)
        response.raise_for_status()  # This already ensures that only a 200 (or other 2xx) status will continue.
        data = response.json()
        if "results" in data:
            return data["results"]
        else:
            logging.warning("No 'results' key found in the API response.")
    except Exception as e:  # Catching all exceptions in one block.
        logging.error(f"Error fetching solar schedule data: {e}")
    return {}


def get_zen_quote() -> Dict[str, str]:
    """Fetch a random Zen quote.

    Returns:
        Dict[str, str]: Dictionary with keys 'quote' and 'author'.
                        Returns an empty dictionary if an error occurs.
    """
    url = "https://zenquotes.io/api/random"
    try:
        response = requests.get(url=url, timeout=10)
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
    url = "https://stoic.tekloon.net/stoic-quote"
    try:
        response = requests.get(url=url, timeout=10)
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
    url = "https://bible-api.com/data/web/random"
    try:
        response = requests.get(url, timeout=10)
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


def get_interesting_fact() -> str:
    """Fetch a random interesting fact.

    Returns:
        Optional[Dict[str, str]]: Dictionary with key 'fact', or None if error.
    """
    url = "https://uselessfacts.jsph.pl/api/v2/facts/random"
    try:
        response = requests.get(url, timeout=10)
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
    url = "https://www.themealdb.com/api/json/v1/1/random.php"
    try:
        response = requests.get(url, timeout=10)
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
    url = "https://www.dictionary.com/e/word-of-the-day/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url=url, headers=headers, timeout=10)
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
    url = "https://www.poetryfoundation.org/poems/poem-of-the-day"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
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


def main() -> None:
    """Main function to call all API functions and print the results."""
    # Call the API functions
    sun = get_solar_schedule(1.3521, 103.8198)  # Singapore coordinates
    zen = get_zen_quote()
    stoic = get_stoic_quote()
    verse = get_bible_verse()
    word = get_word_of_the_day()
    fact = get_interesting_fact()
    recipe = get_recipe_of_the_day()
    papers = get_arxiv_papers(
        query="object detection",
        random_k=3,
        download=True,
        storage="local",
        local_storage_path="./data/papers",
    )
    poem = get_poem_of_the_day()

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


if __name__ == "__main__":
    main()

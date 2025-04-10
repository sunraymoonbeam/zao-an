import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import hydra
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape
from omegaconf import DictConfig, OmegaConf
from tqdm import tqdm

from src.api_clients import (
    get_arxiv_papers,
    get_bible_verse,
    get_horoscope,
    get_nearby_places,
    get_places,
    get_poem_of_the_day,
    get_recipe_of_the_day,
    get_solar_schedule,
    get_stoic_quote,
    get_useless_fact,
    get_word_of_the_day,
    get_zen_quote,
)
from src.gmail_service import GmailService
from src.utils import (
    download_pdf_local,
    download_pdf_s3,
    get_display_name,
    get_geolocation_details,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@hydra.main(config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """
    Orchestrates the retrieval of various API data, downloads necessary PDFs,
    renders an email using a Jinja2 template, and sends the composed email via Gmail.

    Args:
        cfg (DictConfig): Hydra configuration object including email, location, and API settings.
    """
    # Initialize the Gmail service
    logging.info("Initializing Gmail service...")
    gmail_service = GmailService(
        credentials_path=cfg.credentials_path, token_path=cfg.token_path
    )

    # Get geolocation details based on the provided region and country codes.
    logging.info(
        "Retrieving geolocation details for region '%s' with country code '%s'",
        cfg.api.location,
        cfg.api.country_code,
    )
    geolocation_coordinates = get_geolocation_details(
        query=cfg.api.location, country_codes=[cfg.api.country_code]
    )
    if not geolocation_coordinates:
        logging.warning(
            "Failed to retrieve geolocation details. Defaulting to Singapore coordinates."
        )
        geolocation_coordinates = {
            "center": {"latitude": 1.357107, "longitude": 103.8194992},
            "low": {"latitude": 1.1285402, "longitude": 103.5666667},
            "high": {"latitude": 1.5143183, "longitude": 104.5716696},
        }

    # Get the data from various APIs
    logging.info("Retrieving data from various APIs...")
    data: Dict[str, Any] = {
        "datetime": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
        "solar_schedule": get_solar_schedule(
            lat=geolocation_coordinates["center"]["latitude"],
            long=geolocation_coordinates["center"]["longitude"],
        ),
        "zen_quote": get_zen_quote(),
        "stoic_quote": get_stoic_quote(),
        "bible_verse": get_bible_verse(),
        "interesting_fact": get_useless_fact(),
        "recipe": get_recipe_of_the_day(),
        "arxiv_query": cfg.arxiv.query,
        "arxiv_papers": get_arxiv_papers(
            query=cfg.arxiv.query,
            max_results=cfg.arxiv.max_results,
            random_k=cfg.arxiv.random_k,
        ),
        "wod": get_word_of_the_day(),
        "poem": get_poem_of_the_day(),
        "horoscope": get_horoscope(sign=cfg.api.horoscope_sign),
        "cat_gif": "https://cataas.com/cat/gif",  # Direct URL for the cat GIF
    }

    # Load Google Maps API key
    load_dotenv()  # Load variables from .env file
    google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")  # Get the key

    # Fetching restaurants using Google Places API that might serve the recipe of the day
    logging.info(
        "Fetching nearby restaurants that might serve the recipe of the day..."
    )
    text_query = data["recipe"]["name"]
    restaurants = get_places(
        api_key=google_maps_api_key,
        text_query=text_query,
        bounding_coordinates=geolocation_coordinates,
        place_type=cfg.api.text_search.place_type,
        page_size=cfg.api.text_search.page_size,
        min_rating=cfg.api.text_search.min_rating,
        price_levels=OmegaConf.to_container(
            cfg.api.text_search.price_levels, resolve=True
        ),  # <-- convert ListConfig to list,
    )
    if len(restaurants) == 0:
        # TODO: implement mimesis to get random dish name (requires python3.10 and above - use docker)
        text_query = "chicken rice"  # chicken rice for now
        logging.warning(
            f"No restaurants relevant to {data['recipe']['name']} found. Defaulting to {text_query}.."
        )
        restaurants = get_places(
            api_key=google_maps_api_key,
            text_query=text_query,
            bounding_coordinates=geolocation_coordinates,
            place_type=cfg.api.text_search.place_type,
            page_size=cfg.api.text_search.page_size,
            min_rating=cfg.api.text_search.min_rating,
            price_levels=OmegaConf.to_container(
                cfg.api.text_search.price_levels, resolve=True
            ),  # convert ListConfig to list,,
        )
    data["restaurants"] = restaurants
    data["text_query"] = text_query  # store the text query used for restaurants

    # Download PDFs if needed
    if cfg.arxiv.download_papers:
        logging.info("Downloading PDFs for arXiv papers...")
        for paper in tqdm(data["arxiv_papers"], desc="Downloading PDFs"):
            pdf_link = paper.get("pdf_link")
            if pdf_link:
                local_path = None
                s3_path = None

                dest_filename = (
                    "".join(
                        c.lower() if c.isalnum() or c in " _-" else "_"
                        for c in paper["title"]
                    ).replace(" ", "_")
                    + ".pdf"
                )
                output_dir = os.path.join(
                    cfg.arxiv.storage_dir, cfg.arxiv.query.lower().replace(" ", "_")
                )

                if cfg.arxiv.storage_type == "s3":
                    s3_path = download_pdf_s3(
                        pdf_url=pdf_link,
                        s3_dir=output_dir,
                        dest_filename=f"{dest_filename}.pdf",
                        s3_config=cfg.s3_config,
                    )
                else:
                    os.makedirs(
                        output_dir, exist_ok=True
                    )  # Ensure the output directory exists.
                    dest_filepath = os.path.join(output_dir, dest_filename)
                    local_path = download_pdf_local(
                        pdf_url=pdf_link,
                        dest_filepath=dest_filepath,
                    )
                # Update the paper dictionary with paths
                paper["local_path"] = local_path
                paper["s3_path"] = s3_path

    # Locate the templates directory relative to this file and verify its existence.
    template_dir = Path(__file__).parent / "templates"
    if not template_dir.is_dir():
        raise FileNotFoundError(
            f"Template directory not found: {template_dir}. Please ensure the directory exists."
        )

    # Set up the Jinja2 environment with autoescaping for security on HTML/XML templates.
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # Determine the email format. Default to HTML if the specified format is invalid.
    email_format = cfg.email.email_format.lower()
    if email_format not in ("html", "text"):
        logging.warning(
            f"Invalid email format '{email_format}' specified. Defaulting to HTML."
        )
        email_format = "html"

    # Select the appropriate template based on the email format.
    template_name = "newsletter.html" if email_format == "html" else "newsletter.txt"
    template = env.get_template(template_name)

    logging.info("Starting emailing process...")

    # Prepare attachments: filter out papers that have a local PDF path available.
    attachments = [
        paper["local_path"]
        for paper in data.get("arxiv_papers", [])
        if paper.get("local_path")
    ]

    # Iterate over each recipient to personalize and send the email.
    for recipient in cfg.email.recipients:
        recipient_name = get_display_name(recipient)
        subject = f"Good Morning, {recipient_name}!"

        # Update the rendering context with personalized data.
        email_context = data.copy()
        email_context["recipient_name"] = recipient_name

        # Render the email body using the appropriate template.
        email_body = template.render(email_context)

        # Send the email via the provided gmail service.
        gmail_service.send_email(
            sender=cfg.email.sender,
            recipient=recipient,
            subject=subject,
            body=email_body,
            format_type=email_format,
            attachments=attachments,
        )


if __name__ == "__main__":
    main()

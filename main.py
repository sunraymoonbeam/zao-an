"""
This script orchestrates the following tasks:
    - Retrieves data from various APIs (e.g., arXiv, Bible verse, quotes, etc.)
    - Downloads necessary PDFs from arXiv papers
    - Renders an email using a Jinja2 template
    - Sends the composed email via the Gmail API

The configuration is managed via Hydra with an external YAML configuration file.
"""

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
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


from src.api_clients import (
    get_arxiv_papers,
    get_bible_verse,
    get_horoscope,
    get_poem_of_the_day,
    get_recipe_of_the_day,
    get_solar_schedule,
    get_stoic_quote,
    get_useless_fact,
    get_word_of_the_day,
    get_zen_quote,
)
from src.api_google_places import get_places
from src.gmail_service import GmailService
from src.utils import (
    download_pdf_local,
    download_pdf_s3,
    get_display_name,
    get_geolocation_details,
    setup_logging,
)


@hydra.main(config_path="conf", config_name="config")
def main(cfg: DictConfig) -> None:
    """
    Main function to execute the following steps:
        1. Initialize Gmail service.
        2. Retrieve geolocation details using API settings.
        3. Gather data from various APIs.
        4. Download PDFs from arXiv if required.
        5. Render and send personalized emails to recipients.

    Args:
        cfg (DictConfig): Hydra configuration object containing settings for email,
                          API, arXiv, and other modules.
    """
    logger = logging.getLogger(__name__)
    logger.info("Setting up logging configuration.")

    # Get absolute path to the directory of main.py
    project_root = Path(__file__).parent
    setup_logging(
        logging_config_path=os.path.join(
            project_root,
            "conf",
            "logging.yaml",
        ),
    )

    # Initialize the Gmail service with API credentials.
    logging.info("Initializing Gmail service...")

    # Define paths relative to main.py
    credentials_path, token_path = (
        project_root / cfg.credentials_path,
        Path(__file__).parent / cfg.token_path,
    )
    gmail_service = GmailService(
        credentials_path=credentials_path, token_path=token_path
    )

    # Retrieve geolocation details for the configured location.
    logging.info(
        "Retrieving geolocation details for region '%s' with country code '%s'.",
        cfg.api.location,
        cfg.api.country_code,
    )
    geo_details = get_geolocation_details(
        query=cfg.api.location, country_codes=[cfg.api.country_code]
    )
    if not geo_details:
        logging.warning(
            "Failed to retrieve geolocation details. Defaulting to Singapore coordinates."
        )
        geo_details = {
            "center": {"latitude": 1.357107, "longitude": 103.8194992},
            "low": {"latitude": 1.1285402, "longitude": 103.5666667},
            "high": {"latitude": 1.5143183, "longitude": 104.5716696},
        }

    # Compose data dictionary by retrieving data from various APIs.
    logging.info("Retrieving data from various APIs...")
    data: Dict[str, Any] = {
        "datetime": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
        "solar_schedule": get_solar_schedule(
            lat=geo_details["center"]["latitude"],
            long=geo_details["center"]["longitude"],
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
        "cat_gif": "https://cataas.com/cat/gif",  # Direct URL for a cat GIF
    }

    # Load environment variables (e.g., Google Maps API key)
    load_dotenv()
    google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    # Fetch places (e.g., restaurants) relevant to the recipe of the day
    logging.info(
        f"Fetching nearby places relevant to the recipe of the day: {data['recipe']['name']}..."
    )
    text_query = data["recipe"]["name"]
    places = get_places(
        api_key=google_maps_api_key,
        text_query=text_query,
        bounding_coordinates=geo_details,
        place_type=cfg.api.text_search.place_type,
        page_size=cfg.api.text_search.page_size,
        min_rating=cfg.api.text_search.min_rating,
        price_levels=OmegaConf.to_container(
            cfg.api.text_search.price_levels, resolve=True
        ),
    )
    # If no places are found, default to a fallback query (e.g., "chicken rice").
    if not places:
        # TODO: implement mimesis to get random dish name (requires python3.10 and above - use docker)
        text_query = "chicken rice"
        logging.warning(
            f"No places relevant to '{data['recipe']['name']}' found. Defaulting to finding places for '{text_query}'."
        )
        places = get_places(
            api_key=google_maps_api_key,
            text_query=text_query,
            bounding_coordinates=geo_details,
            place_type=cfg.api.text_search.place_type,
            page_size=cfg.api.text_search.page_size,
            min_rating=cfg.api.text_search.min_rating,
            price_levels=OmegaConf.to_container(
                cfg.api.text_search.price_levels, resolve=True
            ),
        )
    data["places"] = places  # store the fetched places in the data dictionary
    data["text_query"] = text_query  # store the actual query used

    # Download PDFs from arXiv papers if the configuration is set accordingly.
    if cfg.arxiv.download_papers:
        logging.info("Downloading PDFs for arXiv papers...")
        for paper in tqdm(data["arxiv_papers"], desc="Downloading PDFs"):
            pdf_link = paper.get("pdf_link")
            if pdf_link:
                local_pdf_path = None
                s3_pdf_path = None

                # Create a safe filename based on the paper title.
                dest_filename = (
                    "".join(
                        c.lower() if c.isalnum() or c in " _-" else "_"
                        for c in paper["title"]
                    ).replace(" ", "_")
                    + ".pdf"
                )

                if cfg.arxiv.storage_type == "s3":
                    output_directory = os.path.join(
                        cfg.arxiv.storage_dir, cfg.arxiv.query.lower().replace(" ", "_")
                    )
                    s3_pdf_path = download_pdf_s3(
                        pdf_url=pdf_link,
                        s3_dir=output_directory,
                        dest_filename=f"{dest_filename}.pdf",
                        s3_config=cfg.s3_config,
                    )
                else:
                    output_directory = os.path.join(
                        project_root,
                        cfg.arxiv.storage_dir,
                        cfg.arxiv.query.lower().replace(" ", "_"),
                    )
                    os.makedirs(output_directory, exist_ok=True)
                    dest_filepath = os.path.join(output_directory, dest_filename)
                    local_pdf_path = download_pdf_local(
                        pdf_url=pdf_link,
                        dest_filepath=dest_filepath,
                    )
                # Update the paper dictionary with paths to the PDF files.
                paper["local_path"] = local_pdf_path
                paper["s3_path"] = s3_pdf_path

    # Locate the templates directory relative to this file.
    template_dir = Path(__file__).parent / "templates"
    if not template_dir.is_dir():
        raise FileNotFoundError(
            f"Template directory not found: {template_dir}. Please ensure the directory exists."
        )

    # Set up the Jinja2 environment with autoescaping enabled for security.
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # Ensure the email format is valid; default to "html" if not.
    email_format = cfg.email.format.lower()
    if email_format not in ("html", "plain"):
        logging.warning(
            f"Invalid email format '{email_format}' specified. Defaulting to plain."
        )
        email_format = "plain"

    # Select the correct template based on the email format.
    template_name = "newsletter.html" if email_format == "html" else "newsletter.txt"
    template = env.get_template(template_name)

    logging.info("Starting the email sending process...")

    # Prepare attachments: include only papers with a local PDF path.
    attachments = [
        paper["local_path"]
        for paper in data.get("arxiv_papers", [])
        if paper.get("local_path")
    ]

    progress_bar = Progress(
        SpinnerColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        BarColumn(complete_style="light_goldenrod1", finished_style="light_goldenrod1"),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
    )

    # Main Loop: send a personalized emai to each recipient
    recipient_list = cfg.email.recipients
    with progress_bar as p:
        for recipient in p.track(
            recipient_list,
            description="Sending emails...",
        ):
            recipient_name = get_display_name(recipient)
            subject = f"Good Morning, {recipient_name}!"

            # Update the rendering context with the recipient's name and other data.
            email_context = data.copy()
            email_context["recipient_name"] = recipient_name

            # Render the email content from the Jinja2 template.
            email_body = template.render(email_context)

            # Send the email using the Gmail service.
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

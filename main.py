import logging
import os
from datetime import datetime
from typing import Any, Dict

import hydra
from jinja2 import Environment, FileSystemLoader
from omegaconf import DictConfig
from tqdm import tqdm

# Import your API clients and Gmail service modules from src
from src.api_clients import (
    get_arxiv_papers,
    get_bible_verse,
    get_interesting_fact,
    get_poem_of_the_day,
    get_recipe_of_the_day,
    get_stoic_quote,
    get_solar_schedule,
    get_word_of_the_day,
    get_zen_quote,
)
from src.gmail_service import GmailService
from src.utils import download_pdf_local, download_pdf_s3

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
    # Initialize the Gmail service using our GmailService class
    logging.info("Initializing Gmail service...")
    gmail = GmailService(
        credentials_path=cfg.credentials_path, token_path=cfg.token_path
    )

    # Retrieve data from API clients
    logging.info("Retrieving data from API clients...")
    data: Dict[str, Any] = {
        "datetime": datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
        "solar_schedule": get_solar_schedule(
            lat=cfg.location.latitude, long=cfg.location.longitude
        )
        or {},
        "zen_quote": get_zen_quote(),
        "stoic_quote": get_stoic_quote(),
        "bible_verse": get_bible_verse(),
        "interesting_fact": get_interesting_fact(),
        "recipe": get_recipe_of_the_day(),
        "arxiv_query": cfg.arxiv.query,
        "arxiv_papers": get_arxiv_papers(
            query=cfg.arxiv.query,
            max_results=cfg.arxiv.max_results,
            random_k=cfg.arxiv.random_k,
        ),
        "wod": get_word_of_the_day(),
        "poem": get_poem_of_the_day(),
        "cat_gif": "https://cataas.com/cat/gif",  # Direct URL for the cat GIF
    }

    # Download PDFs if needed
    if cfg.arxiv.download_papers:
        logging.info("Downloading PDFs for arXiv papers...")
        for paper in tqdm(data["arxiv_papers"], desc="Downloading PDFs"):
            pdf_link = paper.get("pdf_link")
            if pdf_link:
                local_path = None
                s3_path = None

                # Sanitize title for filename: lowercase, underscores, and add .pdf extension.
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
                    local_path = download_pdf_local(
                        pdf_url=pdf_link,
                        output_dir=output_dir,
                        dest_filename=dest_filename,
                    )
                # Update the paper dictionary with paths
                paper["local_path"] = local_path
                paper["s3_path"] = s3_path

    # Prepare the email template using Jinja2
    template_dir = os.path.join(os.path.dirname(__file__), "src", "email_templates")
    env = Environment(loader=FileSystemLoader(template_dir))

    email_format = cfg.email.email_format.lower()
    if email_format not in ["html", "text"]:
        logging.warning(
            f"Invalid email format '{email_format}' specified. Defaulting to HTML."
        )
        email_format = "html"

    # Load the appropriate template based on the format
    template_name = "digest.html" if email_format == "html" else "digest.txt"
    template = env.get_template(template_name)

    # Render the template with data
    email_body = template.render(data)

    # Compose the email subject with prefix and current date
    subject = f"{cfg.email.subject_prefix} - {datetime.today().strftime('%Y-%m-%d')}"

    # Prepare attachments: filtering only papers with a local PDF available.
    attachments = [
        paper["local_path"] for paper in data["arxiv_papers"] if paper.get("local_path")
    ]

    # Send the email to each recipient
    for recipient in cfg.email.recipients:
        logging.info(f"Sending email to {recipient}...")
        result = gmail.send_email(
            sender=cfg.email.sender,
            recipient=recipient,
            subject=subject,
            body=email_body,
            format_type=email_format,
            attachments=attachments,
        )
        if result:
            logging.info(f"Email sent successfully to {recipient}.")
        else:
            logging.error(f"Failed to send email to {recipient}.")


if __name__ == "__main__":
    main()

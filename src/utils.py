"""
Utilities Module

This module provides utility functions for:
    - Extracting display names from email addresses.
    - Geolocation queries using Nominatim (OpenStreetMap).
    - Downloading PDFs locally or uploading to AWS S3.
"""

import logging
import os
from email.utils import parseaddr
from typing import Dict, Optional

import boto3
import requests
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
import yaml

# Configure logging
logger = logging.getLogger(__name__)


def setup_logging(
    logging_config_path="conf/logging.yaml",
    default_level=logging.INFO,
):
    """Set up configuration for logging utilities."""

    # Get absolute path to project root from the logging config file
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Ensure logs directory exists
    logs_dir = os.path.join(project_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    try:
        with open(logging_config_path, encoding="utf-8") as file:
            log_config = yaml.safe_load(file)

        # Inject absolute paths into handlers (overwrite relative)
        for handler_name in [
            "debug_file_handler",
            "info_file_handler",
            "error_file_handler",
        ]:
            if handler_name in log_config.get("handlers", {}):
                filename = log_config["handlers"][handler_name]["filename"]
                log_config["handlers"][handler_name]["filename"] = os.path.join(
                    logs_dir, filename
                )

        logging.config.dictConfig(log_config)

    except Exception as error:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=default_level,
        )
        logging.getLogger().warning(error)
        logging.getLogger().warning(
            "Logging config file not found or invalid. Basic config is being used."
        )


def get_display_name(email_address: str) -> str:
    """
    Extracts the display name from an email address.

    If the provided email string includes a display name, it is returned.
    Otherwise, the function infers a display name from the email's local part.

    Args:
        email_address (str): The full email address, which may contain a display name.

    Returns:
        str: The extracted or inferred display name.
    """
    name, address = parseaddr(email_address)
    if name:
        # Return the explicitly provided display name.
        return name.strip()

    # Fallback: use the local part of the address (before the @ symbol).
    local_part = address.split("@")[0]
    # Replace common separators and convert to title case.
    return local_part.replace(".", " ").replace("_", " ").title()


def get_geolocation_details(
    query: str,
    country_codes: Optional[str] = ["SG"],
) -> Optional[Dict[str, Dict[str, float]]]:
    """
    Retrieves geolocation details such as the center and bounding box for a location.

    Uses Nominatim (OpenStreetMap) for geocoding. The returned dictionary contains:
        - "center": Latitude and longitude of the location.
        - "low": Southern and western bounds.
        - "high": Northern and eastern bounds.

    Args:
        query (str): The location query (e.g., "Singapore").
        country_codes (Optional[str], optional): Country code(s) to restrict the search.
            Defaults to ["SG"].

    Returns:
        Optional[Dict[str, Dict[str, float]]]: A dictionary with 'center', 'low', and 'high' coordinates,
        or None if the lookup fails.
    """
    geolocator = Nominatim(user_agent="my_geocoder")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    try:
        location = geocode(
            query, exactly_one=True, addressdetails=True, country_codes=country_codes
        )
        if location and "boundingbox" in location.raw:
            bounds = location.raw[
                "boundingbox"
            ]  # Format: [south_lat, north_lat, west_lng, east_lng]
            return {
                "center": {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                },
                "low": {
                    "latitude": float(bounds[0]),  # South
                    "longitude": float(bounds[2]),  # West
                },
                "high": {
                    "latitude": float(bounds[1]),  # North
                    "longitude": float(bounds[3]),  # East
                },
            }
        else:
            logging.warning("Could not find bounding box for '%s'.", query)
    except Exception as e:
        logging.error("Error retrieving geolocation details for '%s': %s", query, e)

    return None


def download_pdf_local(pdf_url: str, dest_filepath: str) -> Optional[str]:
    """
    Downloads a PDF from a given URL and saves it locally.

    Args:
        pdf_url (str): URL from which to download the PDF.
        dest_filepath (str): Full path where the PDF should be saved.

    Returns:
        Optional[str]: The full path to the downloaded PDF if successful, else None.
    """
    try:
        response = requests.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()
        with open(dest_filepath, "wb") as file_out:
            for chunk in response.iter_content(chunk_size=8192):
                file_out.write(chunk)
        return dest_filepath
    except Exception as e:
        logging.error("Error downloading PDF from %s: %s", pdf_url, e)
    return None


def download_pdf_s3(
    pdf_url: str, s3_folder: str, dest_filename: str, s3_config: dict
) -> Optional[str]:
    """
    Downloads a PDF from a given URL and uploads it to an AWS S3 bucket.

    Args:
        pdf_url (str): URL from which to download the PDF.
        s3_folder (str): Folder (prefix) in the S3 bucket where the PDF will be stored.
        dest_filename (str): Filename to assign in the S3 bucket.
        s3_config (dict): S3 configuration parameters. Expected keys:
            - "bucket" (str): S3 bucket name.
            - "region" (str): AWS region.
            - "access_key_id" (str): AWS access key ID.
            - "secret_access_key" (str): AWS secret access key.

    Returns:
        Optional[str]: The S3 object key (i.e. path in the bucket) if successful, else None.
    """
    try:
        # Create S3 client.
        s3_client = boto3.client(
            "s3",
            region_name=s3_config.get("region"),
            aws_access_key_id=s3_config.get("access_key_id"),
            aws_secret_access_key=s3_config.get("secret_access_key"),
        )
        response = requests.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()

        # Ensure the S3 folder has no leading/trailing slashes.
        s3_folder = s3_folder.strip("/")
        s3_key = f"{s3_folder}/{dest_filename}"

        # Upload the file directly from response stream.
        s3_client.upload_fileobj(response.raw, s3_config["bucket"], s3_key)
        logging.info("Uploaded PDF to S3 with key: %s", s3_key)
        return s3_key
    except Exception as e:
        logging.error("Error downloading or uploading PDF from %s: %s", pdf_url, e)
    return None


def get_random_dish_name() -> str:
    """
    Generate a random dish name using mimesis.

    Returns:
        str: A random dish name (e.g., "pasta", "sushi", "burger").
             Falls back to "chicken rice" if mimesis fails.
    """
    try:
        from mimesis import Food

        food = Food()
        dish = food.dish()
        logging.debug(f"Generated random dish name: {dish}")
        return dish
    except Exception as e:
        logging.warning(
            f"Failed to generate random dish name with mimesis: {e}. Falling back to 'chicken rice'."
        )
        return "chicken rice"

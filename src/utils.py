import logging
from email.utils import parseaddr
from typing import Dict, Optional

import boto3
import requests
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim


def get_display_name(email_string: str) -> str:
    """Extracts the display name from an email address.

    If the email string includes a display name, return it.
    Otherwise, try to infer a name from the email's local part.
    """
    name, address = parseaddr(email_string)
    if name:
        # Return the explicitly provided display name.
        return name.strip()

    # No display name provided, use the local part as a fallback.
    local_part = address.split("@")[0]
    # Replace common separators with spaces and title-case the result.
    return local_part.replace(".", " ").replace("_", " ").title()


def get_geolocation_details(
    query: str,
    country_codes: Optional[str] = ["SG"],
) -> Optional[Dict[str, Dict[str, float]]]:
    """
    Retrieves the geographic center and bounding box of a country using OpenStreetMap (Nominatim).

    Args:
        country_name (str): The name of the country (e.g., "Singapore").

    Returns:
        Optional[Dict]: A dictionary with 'center', 'low', and 'high' lat/lng coordinates,
                        or None if lookup fails.
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
            ]  # [south_lat, north_lat, west_lng, east_lng]

            return {
                "center": {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                },
                "low": {
                    "latitude": float(bounds[0]),  # south
                    "longitude": float(bounds[2]),  # west
                },
                "high": {
                    "latitude": float(bounds[1]),  # north
                    "longitude": float(bounds[3]),  # east
                },
            }
        else:
            logging.warning(f"Could not find bounding box for '{query}'.")

    except Exception as e:
        logging.error("Error retrieving geolocation details for '%s': %s", query, e)


def download_pdf_local(pdf_url: str, dest_filepath: str) -> Optional[str]:
    """
    Download a PDF from the given URL and save it locally.

    Args:
        pdf_url (str): URL to download the PDF.
        dest_filepath (str): Full path where the PDF should be saved.

    Returns:
        Optional[str]: The full path to the downloaded PDF if successful, else None.
    """
    try:
        # Download the PDF and save it to the specified location.
        response = requests.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()
        with open(dest_filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return dest_filepath
    except Exception as e:
        logging.error("Error downloading PDF locally from %s: %s", pdf_url, e)


def download_pdf_s3(
    pdf_url: str, s3_dir: str, dest_filename: str, s3_config: dict
) -> Optional[str]:
    """
    Download a PDF from the given URL and upload it to S3.

    Args:
        pdf_url (str): URL to download the PDF.
        s3_folder (str): Folder (prefix) in the S3 bucket where the PDF should be stored.
        dest_filename (str): Filename to be used for the PDF in S3.
        s3_config (dict): S3 configuration parameters. Expected keys:
            - bucket (str): S3 bucket name.
            - region (str): AWS region.
            - access_key_id (str): AWS access key ID.
            - secret_access_key (str): AWS secret access key.

    Returns:
        Optional[str]: The S3 object key (path in the bucket) if upload is successful, else None.
    """
    try:
        # Create an S3 client using provided configuration.
        s3_client = boto3.client(
            "s3",
            region_name=s3_config.get("region"),
            aws_access_key_id=s3_config.get("access_key_id"),
            aws_secret_access_key=s3_config.get("secret_access_key"),
        )
        response = requests.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()

        # Build the S3 object key.
        # Ensure s3_folder does not have leading/trailing slashes.
        s3_dir = s3_dir.strip("/")
        s3_key = f"{s3_dir}/{dest_filename}"

        # Use upload_fileobj to stream the file directly to S3.
        s3_client.upload_fileobj(response.raw, s3_config["bucket"], s3_key)
        logging.info("Uploaded PDF to S3 with key: %s", s3_key)
        return s3_key
    except Exception as e:
        logging.error(
            "Error downloading or uploading PDF to S3 from %s: %s", pdf_url, e
        )

import os
import logging
import requests
import boto3
from typing import Optional


def download_pdf_local(
    pdf_url: str, output_dir: str, dest_filename: str
) -> Optional[str]:
    """
    Download a PDF from the given URL and save it locally.

    Args:
        pdf_url (str): URL to download the PDF.
        output_dir (str): Local directory where the PDF should be stored.
        dest_filename (str): Filename for the saved PDF (without the full path).

    Returns:
        Optional[str]: The full path to the downloaded PDF if successful, else None.
    """
    try:
        # Ensure the output directory exists.
        os.makedirs(output_dir, exist_ok=True)

        # Build the full path for the destination file.
        full_path = os.path.join(output_dir, dest_filename)

        # Download the PDF and save it to the specified location.
        response = requests.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()
        with open(full_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return full_path
    except Exception as e:
        logging.error("Error downloading PDF locally from %s: %s", pdf_url, e)
        return None


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

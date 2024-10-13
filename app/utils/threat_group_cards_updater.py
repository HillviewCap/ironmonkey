import os
import requests
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

def fetch_json_from_url(url):
    """Fetch JSON data from the provided URL."""
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'YourAppName/1.0'})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching data from {url}: {e}")
        return None

def read_local_json_file(filepath):
    """Read JSON data from a local file."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading local JSON file {filepath}: {e}")
        return None

def has_data_changed(existing_data, new_data):
    """Check if the existing data has changed compared to the new data."""
    existing_hash = hashlib.md5(json.dumps(existing_data, sort_keys=True).encode('utf-8')).hexdigest()
    new_hash = hashlib.md5(json.dumps(new_data, sort_keys=True).encode('utf-8')).hexdigest()
    return existing_hash != new_hash

def update_threat_group_cards():
    """Check for updates to the Threat Group Cards JSON files and update them if changes are detected."""
    urls = {
        'all_tools': 'https://apt.etda.or.th/cgi-bin/getcard.cgi?t=all&o=j',
        'all_groups': 'https://apt.etda.or.th/cgi-bin/getcard.cgi?g=all&o=j'
    }
    static_json_path = os.path.join('app', 'static', 'json')

    # Ensure the directory exists
    os.makedirs(static_json_path, exist_ok=True)

    for filename, url in urls.items():
        local_filepath = os.path.join(static_json_path, f"{filename}.json")
        new_data = fetch_json_from_url(url)
        if new_data is None:
            logger.error(f"Failed to fetch data from {url}")
            continue

        existing_data = read_local_json_file(local_filepath)
        if existing_data is None:
            # Local file doesn't exist or couldn't be read; save the new data
            try:
                with open(local_filepath, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=4)
                logger.info(f"Downloaded new data and saved to {local_filepath}")
            except Exception as e:
                logger.error(f"Error writing to file {local_filepath}: {e}")
            continue

        if has_data_changed(existing_data, new_data):
            # Data has changed; update the local file
            try:
                with open(local_filepath, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=4)
                logger.info(f"Detected changes in data from {url}. Updated local file {local_filepath}")
            except Exception as e:
                logger.error(f"Error writing to file {local_filepath}: {e}")
        else:
            logger.info(f"No changes detected for {url}. Local file {local_filepath} is up to date.")

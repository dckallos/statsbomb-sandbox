import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

# Fix pathing issues depending on how the script is executed
if '__file__' in globals():
    script_dir = Path(__file__).resolve().parent
    ROOT = script_dir.parent
else:
    ROOT = Path(os.getcwd())
    script_dir = ROOT / "research"

CONFIG = json.loads((script_dir / "source_config.json").read_text(encoding="utf-8"))

REPOSITORY = CONFIG["repository"]
SOURCE_REF = CONFIG["source_ref"]
COMPETITION_ID = CONFIG["competition_id"]
SEASON_ID = CONFIG["season_id"]

BASE_URL = f"https://raw.githubusercontent.com/{REPOSITORY}/{SOURCE_REF}/data"
DATA_DIR = ROOT / "data" / "raw" / "statsbomb" / SOURCE_REF
FILE_TYPES = ("events", "lineups", "three-sixty")
USER_AGENT = "statsbomb-euro-2024-portfolio"


def fetch(relative_path):
    """
    Download and save a JSON file from StatsBomb.
    """
    request = Request(
        f"{BASE_URL}/{relative_path}",
        headers={"User-Agent": USER_AGENT},
    )
    with urlopen(request, timeout=90) as response:
        payload = response.read()

    output_path = DATA_DIR / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)

    return json.loads(payload)


def main():
    fetch("competitions.json")
    catalog_path = f"matches/{COMPETITION_ID}/{SEASON_ID}.json"
    matches = fetch(catalog_path)

    # Extract all match IDs and download their specific files
    match_ids = [match["match_id"] for match in matches]
    for match_id in match_ids:
        for file_type in FILE_TYPES:
            path = f"{file_type}/{match_id}.json"
            print(f"Fetching {path}...")
            fetch(path)

    print(f"Snapshot downloaded to: {DATA_DIR}")


if __name__ == "__main__":
    main()
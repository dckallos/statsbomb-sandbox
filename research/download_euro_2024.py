import json
from pathlib import Path
from urllib.request import Request, urlopen

# TODO: Conform to py console, bash/zsh, and IDE
CONFIG = json.loads(Path("source_config.json").read_text(encoding="utf-8"))

REPOSITORY = CONFIG["repository"]
SOURCE_REF = CONFIG["source_ref"]
COMPETITION_ID = CONFIG["competition_id"]
SEASON_ID = CONFIG["season_id"]

BASE_URL = f"https://raw.githubusercontent.com/{REPOSITORY}/{SOURCE_REF}/data"
DATA_DIR = Path("data") / "raw" / "statsbomb" / SOURCE_REF
USER_AGENT = "statsbomb-euro-2024-portfolio"
print(BASE_URL)

def fetch(relative_path):
    """
    Download and save a JSON file from StatsBomb.
    """
    print(f"Downloading {relative_path}...")
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
    # Grab the top-level files first
    fetch("competitions.json")
    catalog_path = f"matches/{COMPETITION_ID}/{SEASON_ID}.json"
    fetch(catalog_path)

    print(f"Done! Files saved to {DATA_DIR}")


if __name__ == "__main__":
    main()
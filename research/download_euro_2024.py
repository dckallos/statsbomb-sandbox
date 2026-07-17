"""
Download the complete StatsBomb Euro 2024 snapshot used by this project.
TODO: Add docs support ...
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from hashlib import sha256
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

if '__file__' in globals():
    # If running normally (Green Play Button), use the script's actual file path
    script_dir = Path(__file__).resolve().parent
    ROOT = script_dir.parent
else:
    # If running interactively (Console Selction), use the working directory
    ROOT = Path(os.getcwd())
    script_dir = ROOT / "research"

# Load the config directly from the script's directory
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
    Download, validat, and save one JSON array.
    """
    request = Request(
        f"{BASE_URL}/{relative_path}",
        headers={"User-Agent": USER_AGENT},
    )
    with urlopen(request, timeout=90) as response:
        payload = response.read()

    records = json.loads(payload)
    if not isinstance(records, list):
        raise ValueError(f"{relative_path} is not a bueno json arry")
    # print(json.dumps(records, indent=2))

    output_path = DATA_DIR / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(payload)

    return {
        "path": relative_path,
        "bytes": len(payload),
        "records": len(records),
        # Excessive? still best-practice
        "sha256": sha256(payload).hexdigest(),
    }, records


def main():
    catalog_path = f"matches/{COMPETITION_ID}/{SEASON_ID}.json"
    catalog_file, matches = fetch(catalog_path)
    competition_file, _ = fetch("competitions.json")

    match_ids = [match["match_id"] for match in matches]
    paths = [
        f"{file_type}/{match_id}.json"
        for file_type in FILE_TYPES
        for match_id in match_ids
    ]

    files = [competition_file, catalog_file]
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(fetch, path) for path in paths]
        for completed, future in enumerate(as_completed(futures), start=1):
            file_record, _ = future.result()
            files.append(file_record)
            print(f"Downloaded {file_record['path']}")

    files.sort(key=lambda file: file["path"])
    manifest = {
        "repository": REPOSITORY,
        "source_ref": SOURCE_REF,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "competition_id": COMPETITION_ID,
        "season_id": SEASON_ID,
        "match_ids": match_ids,
        "file_types": list(FILE_TYPES),
        "files": files,
    }
    # print(json.dumps(manifest, indent=2))
    (DATA_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Snapshot: {DATA_DIR}")


if __name__ == "__main__":
    main()

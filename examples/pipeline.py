"""Stream a bounded number of subscription-backed Lists pages to a JSONL file."""

import json
from pathlib import Path

from builtwith_official import BuiltWith


def export_technology_sites(technology: str, output: Path, max_pages: int = 5) -> None:
    """Write full pages without dropping unknown fields. Requires Lists access."""
    with BuiltWith() as client, output.open("w", encoding="utf-8") as stream:
        for page in client.lists_pages(technology, max_pages=max_pages):
            stream.write(json.dumps(page.data) + "\n")

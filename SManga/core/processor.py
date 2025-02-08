import json
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from .models import Chapter, MangaDetails, ProcessedEntry, ScrapedData


class MangaDataProcessor:
    def __init__(self, source_name: str = "?") -> None:
        self.source_name = source_name
        self.data_directory = Path.home() / ".spider_data"
        self.processed_data_path = self.data_directory / "processed_data.json"
        self.data_directory.mkdir(parents=True, exist_ok=True)

    def _load_json_file(self, path: Path, default: Any = []) -> List[Dict[str, Any]]:
        """Load data from a file, returning a default value if the file does not exist or contains invalid data."""
        if not path.is_file():
            return default

        try:
            with open(path, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, ValueError, IOError) as e:
            print(f"Failed to load data from {path}: {e}")
            return default

    def _save_json_file(self, file_path: Path, data: Any) -> None:
        """Save data to a JSON file with proper error handling."""
        try:
            with file_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except (IOError, OSError) as error:
            print(f"Error saving JSON to {file_path}: {error}")

    def _read_scraped_data(self, file_path: Path) -> ScrapedData:
        """Read the latest scraped data from the file."""
        data = self._load_json_file(file_path, {})
        return cast(ScrapedData, data)  # Cast the loaded data to ScrapedData

    def _create_processed_entry(
        self, last_chapter: Chapter, scraped_details: MangaDetails
    ) -> ProcessedEntry:
        """Create a new processed data entry."""
        return {
            "site": scraped_details.get("source", self.source_name),
            "manganame": scraped_details.get("manganame", "Unknown"),
            "lastchapter": last_chapter.get("document_location", "Unknown"),
            "json_file": self.file_name.name,
        }

    def _update_or_add_entry(
        self, existing_data: List[ProcessedEntry], new_entry: ProcessedEntry
    ) -> List[ProcessedEntry]:
        """Update an existing entry or append a new one."""
        for index, entry in enumerate(existing_data):
            if (
                entry.get("site") == self.source_name
                and entry.get("manganame") == new_entry["manganame"]
            ):
                existing_data[index] = new_entry
                return existing_data  # Return early if updated
        existing_data.append(new_entry)
        return existing_data

    def process_scraped_data(
        self, scraped_file_path: Path, scraped_data: Optional[ScrapedData] = None
    ) -> None:
        """Process the scraped data and update or append it to the data file."""
        self.file_name = scraped_file_path

        existing_data = cast(
            List[ProcessedEntry], self._load_json_file(self.processed_data_path)
        )
        scraped_data = scraped_data or self._read_scraped_data(scraped_file_path)

        chapters = scraped_data.get("chapters", [])
        if not chapters:
            return

        new_entry = self._create_processed_entry(
            chapters[-1], scraped_data.get("details", {})
        )

        if new_entry.get("manganame") and new_entry.get("site"):
            updated_data = self._update_or_add_entry(existing_data, new_entry)
            self._save_json_file(
                self.processed_data_path, cast(List[Dict[str, Any]], updated_data)
            )

    def load_processed_data(self) -> Optional[List[ProcessedEntry]]:
        """Load and return the processed data from the file."""
        data = self._load_json_file(self.processed_data_path)
        return cast(List[ProcessedEntry], data) if data else None

import json
import os
from pathlib import Path
from typing import List, Optional, Dict

class SpiderDataProcessor:
    def __init__(self, spider_name: str = "?"):
        self.spider_name = spider_name
        self.data_directory = Path.home() / ".spider_data"
        self.processed_data_path = self.data_directory / "processed_data.json"
        self.data_directory.mkdir(
            parents=True, exist_ok=True
        )  # Ensure the directory exists

    def _load_data(self, path: Path, empty=[]) -> List[Dict]:
        """Load data from a file, returning an empty list if the file does not exist or contains invalid data."""
        if not path.is_file():
            return empty

        try:
            with open(path, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, ValueError):
            return empty 
        return empty

    def _save_data(self, path: Path, data: List[Dict]) -> None:
        """Save data to a JSON file."""
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except (IOError, OSError) as e:
            print(f"Failed to save data to JSON file {path}: {e}")

    def _read_scraped_data(self, file_path: Path) -> List[Dict]:
        """Read the latest scraped data from the file."""
        return self._load_data(file_path, {})

    def _create_new_entry(self, last_chapter: Dict, scraped_data: Dict) -> Dict:
        """Create a new entry dictionary from the last scraped entry."""
        return {
            "site": scraped_data.get("source", self.spider_name),
            "manganame": scraped_data.get("manganame"),
            "lastchapter": last_chapter.get("document_location"),
            "json_file": self.file_name.name,
        }

    def _update_or_append_entry(
        self, existing_data: List[Dict], new_entry: Dict
    ) -> List[Dict]:
        """Update an existing entry or append a new one to the data list."""
        for index, entry in enumerate(existing_data):
            if (
                entry.get("site") == self.spider_name
                and entry.get("manganame") == new_entry["manganame"]
            ):
                existing_data[index] = new_entry
                return existing_data  # Return early if updated
        existing_data.append(new_entry)
        return existing_data

    def process_data(self, scraped_file_path: Path) -> None:
        """Process the scraped data and update or append it to the data file."""
        self.file_name = scraped_file_path
        existing_data = self._load_data(self.processed_data_path)
        scraped_data = self._read_scraped_data(scraped_file_path)

        chapters = scraped_data.get("chapters")
        if chapters:
            last_chapter = chapters[-1]
            new_entry = self._create_new_entry(last_chapter, scraped_data.get("details", {}))
            if new_entry.get("manganame") and new_entry.get("site"):
                updated_data = self._update_or_append_entry(existing_data, new_entry)
                self._save_data(self.processed_data_path, updated_data)

    def load_processed_data(self) -> Optional[List[Dict]]:
        """Load and return the processed data from the file."""
        data = self._load_data(self.processed_data_path)
        return data if data else None
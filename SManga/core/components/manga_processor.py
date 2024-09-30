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

    def _load_data(self, path: Path) -> List[Dict]:
        """Load data from a file, returning an empty list if the file does not exist or contains invalid data."""
        if not path.is_file():
            return []
        try:
            with open(path, "r") as file:
                data = json.load(file)
                    # and all(isinstance(item, dict) for item in data):
                if isinstance(data, list):
                    return data
        except (json.JSONDecodeError, ValueError):
            return []  # Return empty list on error
        return []

    def _save_data(self, path: Path, data: List[Dict]) -> None:
        """Save data to a JSON file."""
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except (IOError, OSError) as e:
            print(f"Failed to save data to JSON file {path}: {e}")

    def _read_scraped_data(self, file_path: Path) -> List[Dict]:
        """Read the latest scraped data from the file."""
        return self._load_data(file_path)

    def _create_new_entry(self, last_entry: Dict) -> Dict:
        """Create a new entry dictionary from the last scraped entry."""
        return {
            "site": self.spider_name,
            "manganame": last_entry.get("manganame"),
            "lastchapter": last_entry.get("document_location"),
            "json_file": os.path.basename(self.file_name),
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

    def _fix_json_string(self, json_string: str) -> List[Dict]:
        """
        Fix a malformed JSON string by adjusting formatting issues.

        Args:
            json_string (str): The input malformed JSON string.
        """
        formatted_data = json_string.replace("[]", "").strip()
        formatted_data = "[" + formatted_data + "]"

        try:
            formatted_data = formatted_data.replace(
                "][", ","
            )  # Fix the list concatenation issue
            return json.loads(formatted_data)
        except json.JSONDecodeError:
            return []

    def _is_valid_json(self, json_string: str) -> bool:
        """Check if a JSON string is valid."""
        try:
            json.loads(json_string)
            return True
        except json.JSONDecodeError:
            return False

    def fix_json(self, path) -> None:
        """Fix JSON file if it is not valid."""
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as file:
                file_content = file.read()

            if not self._is_valid_json(file_content):
                data = self._fix_json_string(file_content)
                if data:
                    self._save_data(path, data)

    def process_data(self, scraped_file_path: str) -> None:
        """Process the scraped data and update or append it to the data file."""
        self.file_name = scraped_file_path
        existing_data = self._load_data(self.processed_data_path)
        scraped_data = self._read_scraped_data(Path(scraped_file_path))

        if scraped_data:
            last_entry = scraped_data[-1]
            new_entry = self._create_new_entry(last_entry)
            updated_data = self._update_or_append_entry(existing_data, new_entry)
            self._save_data(self.processed_data_path, updated_data)

    def load_processed_data(self) -> Optional[List[Dict]]:
        """Load and return the processed data from the file."""
        data = self._load_data(self.processed_data_path)
        return data if data else None  # Return None if empty

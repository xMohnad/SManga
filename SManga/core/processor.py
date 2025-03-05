import json
from pathlib import Path
from typing import Dict, List

from .models import LastChapter


class BaseManager:
    """
    Base class to manage JSON data storage.

    Attributes:
        data_directory (Path): The directory where JSON files are stored.
        json_file (Path): The path to the specific JSON file.
    """

    def __init__(self, json_filename: str):
        """
        Initializes the BaseManager and ensures the data directory exists.

        Args:
            json_filename (str): The name of the JSON file.
        """
        self.data_directory = Path.home() / ".smanga"
        self.json_file = self.data_directory / json_filename
        self.data_directory.mkdir(parents=True, exist_ok=True)
        self.data = self._load_data()

    def get_all_entries(self) -> List[Dict]:
        """
        Retrieves all entries from the JSON file.

        Returns:
            List[Dict]: A list of all entries.
        """
        return self.data

    def add_or_update_entry(self, last_chapter: LastChapter) -> None:
        """
        Adds or updates an entry in the JSON file.

        Args:
            last_chapter (LastChapter): The entry to add or update.
        """
        for index, entry in enumerate(self.data):
            if last_chapter == entry:
                self.data[index] = last_chapter.asdict
                break
        else:
            self.data.append(last_chapter.asdict)
        self._save_data()

    def update_entry(self, old_manga: LastChapter, updated_manga: LastChapter) -> None:
        """
        Updates an entry in the JSON file based on the old and updated manga.

        Args:
            old_manga (LastChapter): The manga entry before the update.
            updated_manga (LastChapter): The manga entry after the update.
        """
        for index, entry in enumerate(self.data):
            if old_manga == entry:
                self.data[index] = updated_manga.asdict
                break
        else:
            self.data.append(updated_manga.asdict)
        self._save_data()

    def _load_data(self) -> List[Dict]:
        """
        Loads the data from the JSON file.

        Returns:
            List[Dict]: A list of entries from the JSON file. Returns an empty list if the file doesn't exist.
        """
        if self.json_file.exists():
            with open(self.json_file, "r", encoding="utf-8") as file:
                return json.load(file)
        return []

    def _save_data(self) -> None:
        """
        Saves the current data to the JSON file.
        """
        with open(self.json_file, "w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=4)


class LastChapterManager(BaseManager):
    """Manages the addition, updating, and retrieval of last chapter data."""

    def __init__(self, trash_manager=None):
        super().__init__(json_filename="last_chapters.json")
        self.trash_manager = trash_manager or TrashManager(self)

    def delete_entry(self, last_chapter: LastChapter) -> None:
        """
        Deletes an entry from the JSON file and moves it to the trash.

        Args:
            last_chapter (LastChapter): The entry to delete.
        """
        self.data = [entry for entry in self.data if last_chapter != entry]
        self._save_data()
        self.trash_manager.add_to_trash(last_chapter)


class TrashManager(BaseManager):
    """Manages the trash for deleted last chapter entries."""

    def __init__(self, last_chapter_manager=None):
        super().__init__(json_filename="trash.json")
        self.last_chapter_manager = last_chapter_manager or LastChapterManager(self)

    def add_to_trash(self, last_chapter: LastChapter) -> None:
        """
        Adds an entry to the trash.

        Args:
            last_chapter (LastChapter): The entry to add to the trash.
        """
        self.add_or_update_entry(last_chapter)

    def restore_entry(self, last_chapter: LastChapter) -> None:
        """
        Restores an entry from the trash back to the main list.

        Args:
            last_chapter (LastChapter): The entry to restore.
        """
        self.data = [entry for entry in self.data if last_chapter != entry]
        self._save_data()
        self.last_chapter_manager.add_or_update_entry(last_chapter)

    def delete_permanently(self, last_chapter: LastChapter) -> None:
        """
        Deletes an entry permanently from the trash.

        Args:
            last_chapter (LastChapter): The entry to delete permanently.
        """
        self.data = [entry for entry in self.data if last_chapter != entry]
        self._save_data()

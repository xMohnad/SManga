# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from itemadapter.adapter import ItemAdapter
from scrapy import signals


class CustomJsonFeed:
    def __init__(
        self,
        file_name: Optional[str],
        dest_path: Optional[Path],
        overwrite: bool,
        json_enabled: bool,
    ) -> None:
        if isinstance(dest_path, str):
            dest_path = Path(dest_path)

        self.file_name = file_name
        self.dest_path = dest_path
        self.overwrite = overwrite
        self.json_enabled = json_enabled
        self.data = {
            "details": {},
            "chapters": [],
        }
        self.load = False

    @classmethod
    def from_crawler(cls, crawler: Any) -> "CustomJsonFeed":
        JSON_FEEDS = crawler.settings.get("JSON_FEEDS")
        if JSON_FEEDS:
            file_name = JSON_FEEDS.get("file_name")
            dest_path = Path(JSON_FEEDS.get("dest_path"))
            overwrite = JSON_FEEDS.get("overwrite", False)
            pipeline = cls(file_name, dest_path, overwrite, True)
            crawler.signals.connect(
                pipeline.spider_closed, signal=signals.spider_closed
            )
            return pipeline
        return cls(None, None, False, False)

    def open_spider(self, _: Any) -> None:
        data = self.load_data()
        if data:
            self.data["details"] = data.get("details", {})
            self.data["chapters"].extend(data.get("chapters", []))

    def load_data(self) -> Optional[Dict[str, Any]]:
        if not self.overwrite and self.file_name and self.dest_path:
            file_path = self.dest_path / self.file_name
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf8") as file:
                        data = json.load(file)
                        self.load = True
                        return data
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error loading JSON file: {e}")
        return None

    def process_item(self, item: Any, _: Any) -> Any:
        if self.json_enabled:
            item_dict = ItemAdapter(item).asdict()
            if "details" in item_dict:
                self.data["details"] = item_dict["details"]
                if not self.file_name:
                    self.file_name = self.generate_file_name(item_dict["details"])
                    print(self.file_name)
            if "chapters" in item_dict:
                self.data["chapters"].append(item_dict["chapters"])
        return item

    def generate_file_name(self, details: Dict[str, Any]) -> str:
        manganame = details.get("manganame", "unknown")
        sanitized_name = re.sub(r'[<>:"/\\|?*]', "_", manganame.replace(" ", "-"))
        return f"{sanitized_name.lower()}.json"

    def close_spider(self, _: Any) -> None:
        if self.file_name and self.dest_path:
            if not self.overwrite and not self.load:
                data = self.load_data()
                if data:
                    self.data["chapters"].extend(data.get("chapters", []))
                    if not self.data.get("details"):
                        self.data["details"] = data.get("details", {})

            self.data["chapters"] = self.clean_and_sort_chapters(self.data["chapters"])
            file_path = self.dest_path / self.file_name
            self.save_data_to_file(file_path)

    def save_data_to_file(self, file_path) -> None:
        try:
            with open(file_path, "w", encoding="utf8") as file:
                json.dump(self.data, file, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Error saving JSON file: {e}")

    def clean_and_sort_chapters(
        self, chapters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # if not isinstance(chapters, list):
        #     raise ValueError("Expected data to be a list of chapters.")

        unique_chapters = {
            chapter["title"]: chapter
            for chapter in chapters
            if isinstance(chapter, dict) and "title" in chapter
        }.values()

        def extract_chapter_number(chapter: Dict[str, Any]) -> Union[int, float]:
            title = chapter["title"]
            match = re.search(r"\d+", title)
            return int(match.group(0)) if match else float("inf")

        return sorted(unique_chapters, key=extract_chapter_number)

    def spider_closed(self, spider: Any) -> None:
        if self.file_name is None:
            spider.logger.error("File name is None")
            return

        if self.dest_path is None:
            spider.logger.error("Destination path is None")
            return

        spider.smanga.final_file_path = self.dest_path / self.file_name
        # spider.smanga.custom_json_feed = self

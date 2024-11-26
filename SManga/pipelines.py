# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy import signals 
import json, re
from typing import List, Dict


class CustomJsonFeed:
    def __init__(self, file_name, dest_path, overwrite, json):
        self.file_name = file_name
        self.dest_path = dest_path
        self.overwrite = overwrite
        self.json = json
        self.data = {"details": {}, "chapters": []}
        self.load = False 

    @classmethod
    def from_crawler(cls, crawler):
        JSON_FEEDS = crawler.settings.get("JSON_FEEDS")
        if JSON_FEEDS:
            file_name = JSON_FEEDS.get("file_name")
            dest_path = JSON_FEEDS.get("dest_path")
            overwrite = JSON_FEEDS.get("overwrite")
            pipeline = cls(file_name, dest_path, overwrite, True)
            crawler.signals.connect(pipeline.spider_closed, signal=signals.spider_closed)
            return pipeline
        return cls(None, None, None, False)

    def open_spider(self, spider):
        data = self.load_data()
        if data:
            self.data["details"] = data.get("details", {})
            self.data["chapters"].extend(data.get("chapters", []))

    def load_data(self):
        if not self.overwrite:
            if self.file_name and (self.dest_path / self.file_name).exists():
                with open(self.dest_path / self.file_name, "r", encoding="utf8") as file:
                    try:
                        return json.load(file)
                        self.load = True 
                    except json.JSONDecodeError:
                        pass

    def process_item(self, item, spider):
        if self.json:
            item_dict = ItemAdapter(item).asdict()
            if "details" in item_dict:
                self.data["details"] = item_dict["details"]
                if not self.file_name:
                    self.file_name = re.sub(
                        r'[<>:"/\\|?*]',
                        "_",
                        (
                            item_dict.get("details").get("manganame").replace(" ", "-")
                            + ".json"
                        ),
                    ).lower()
                    print(self.file_name)
            if "chapters" in item_dict:
                self.data["chapters"].append(item_dict.get("chapters"))
        return item

    def close_spider(self, spider):
        if self.file_name:
            if not self.overwrite and not self.load:
                data = self.load_data()
                if data:
                    self.data["chapters"].extend(data.get("chapters", []))
                    if not self.data.get("details", False):
                        self.data["details"] = data.get("details", {})

            self.data["chapters"] = self.clean_and_sort_chapters(self.data.get("chapters"))
            with open(self.dest_path / self.file_name, "w", encoding="utf8") as file:
                json.dump(self.data, file, ensure_ascii=False, indent=4)

    def clean_and_sort_chapters(self, data: List[Dict]) -> List[Dict]:
        if not isinstance(data, list):
            raise ValueError("Expected data to be a list of chapters.")

        unique_chapters = {chapter["title"]: chapter for chapter in [chapter for chapter in data if isinstance(chapter, dict) and "title" in chapter]}.values()
        def extract_chapter_number(chapter):
            title = chapter["title"]
            match = re.search(r'\d+', title)  
            return int(match.group(0)) if match else float('inf') 
        return sorted(unique_chapters, key=extract_chapter_number)
     
    def spider_closed(self, spider):
        if self.file_name is None:
            spider.logger.error("File name is None")
            return
    
        if self.dest_path is None:
            spider.logger.error("Destination path is None")
            return
    
        spider.smanga.final_file_path = self.dest_path / self.file_name
        # spider.smanga.custom_json_feed = self

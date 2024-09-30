from typing import Optional
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.spiderloader import SpiderLoader

from SManga.core.components import SpiderDataProcessor

SUPPORTED_FORMATS = ["json", "jsonlines", "jl", "csv", "xml", "pickle", "marshal"]

class SManga:
    def __init__(
        self,
        url: Optional[str] = None,
        file_name: str = "chapters.json",
        overwrite: bool = False,
    ) -> None:
        """
        Initializes the SManga class with the given parameters.
        """
        self.url = url
        self.file_name = file_name
        self.file_format = self._validate_file_format(file_name)
        self.overwrite = overwrite

        self.local_settings = self._prepare_local_settings(
            file_name, self.file_format, overwrite
        )

        self.settings = get_project_settings()
        self.spider_loader = SpiderLoader.from_settings(self.settings)
        self.list_spiders = self.spider_loader.list()

        self.processor = None
        self.spider_name = None

    def _validate_file_format(self, file_name: str) -> str:
        """Validates the file format based on the extension."""
        file_format = file_name.rsplit(".", 1)[-1].lower()
        if file_format not in SUPPORTED_FORMATS:
            raise TypeError(
                f"Unsupported file format: {file_format}. Please use one of the supported formats: {', '.join(SUPPORTED_FORMATS)}."
            )
        return file_format

    def _prepare_local_settings(
        self, file_name: str, file_format: str, overwrite: bool
    ) -> dict:
        """Prepares local settings for the crawling process."""
        return {
            "FEEDS": {
                file_name: {
                    "format": file_format,
                    "overwrite": overwrite,
                }
            }
        }

    def is_valid_url(self, base_url: str) -> bool:
        """Checks if the provided URL starts with the given base URL."""
        return self.url.startswith(base_url)

    def print_spiders(self) -> None:
        """Prints the names of all available spiders."""
        print("Available spiders: ")
        for spider_name in self.list_spiders:
            print(f"  - {spider_name}")

    def find_spider_by_base_url(self) -> Optional[str]:
        """Finds a spider that matches the base URL of the provided URL."""
        for spider_name in self.list_spiders:
            spider_cls = self.spider_loader.load(spider_name)
            if hasattr(spider_cls, "base_url") and self.is_valid_url(
                spider_cls.base_url
            ):
                return spider_name
        return None

    def process_spider_data(self) -> None:
        """Processes the scraped data."""
        if self.processor:
            self.processor.process_data(self.file_name)

    def fix_spider_data(self) -> None:
        """Fixes the JSON data if needed."""
        if self.processor:
            self.processor.fix_json(self.file_name)

    def load_processed_data(self):
        """Loads the processed data."""
        if self.processor:
            return self.processor.load_processed_data()

    def start(self, spider_name: Optional[str] = None) -> None:
        """
        Starts the crawling process using the appropriate spider.
        """
        if not self.url:
            raise ValueError("Error: Missing argument 'URL'.")

        spider_name = spider_name or self.find_spider_by_base_url()
        if not spider_name:
            raise ValueError("The site is not yet supported.")
        if spider_name not in self.list_spiders:
            raise ValueError(f"Spider with name '{spider_name}' not found.")

        self.processor = SpiderDataProcessor(spider_name)
        self.spider_name = spider_name
        process_settings = {**self.settings, **self.local_settings}

        process = CrawlerProcess(process_settings)
        process.crawl(spider_name, url=self.url)
        process.start()


# Example of usage
# smanga = SManga(url="https://3asq.org/manga/jujutsu-kaisen/256/")
# smanga.start()
# smanga.process_spider_data()

from pathlib import Path
from typing import Optional
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.spiderloader import SpiderLoader
from scrapy.settings import Settings
from rich import print 

from SManga.core.components import SpiderDataProcessor

SUPPORTED_FORMATS = ["json", "jsonlines", "jl", "csv", "xml", "pickle", "marshal"]

class SManga:
    def __init__(
        self,
        url: Optional[str] = None,
        user_agent: Optional[str] = None,
        file_name: Optional[str | Path] = None,
        overwrite: bool = False,
    ) -> None:
        """Initializes the SManga class with the given parameters."""
        self.url = url
        self.file_name = file_name
        self.overwrite = overwrite
        self.file_format = self._validate_file_format(file_name)

        self.process_settings = self._prepare_settings(
            file_name, self.file_format, overwrite, user_agent
        )

        self.spider_loader = SpiderLoader.from_settings(self.process_settings)
        self.list_spiders = self.spider_loader.list()
        
        self.processor = None
        self.spider_name = None
        
    def _validate_file_format(self, file_name: Path) -> str:
        """Validates the file format based on the extension."""
        file_format = str(file_name).rsplit(".", 1)[-1].lower()

        if file_format not in SUPPORTED_FORMATS:
            raise TypeError(
                f"Unsupported file format: {file_format}. Please use one of the supported formats: {', '.join(SUPPORTED_FORMATS)}."
            )
        return file_format

    def _prepare_settings(
        self, file_name: str, file_format: str, overwrite: bool, user_agent: str
    ) -> dict:
        """Prepares settings for the crawling process."""
        return Settings({
            **get_project_settings(),
            "FEEDS": {
                file_name: {
                    "format": file_format,
                    "overwrite": overwrite,
                }
            },
            **({"USER_AGENT": user_agent} if user_agent else {})
        })

    def is_valid_url(self, base_url: str) -> bool:
        """Checks if the provided URL starts with the given base URL."""
        return self.url.startswith(base_url)

    def print_spiders(self) -> None:
        """Prints the names of all available spiders."""
        print("[magenta]Available spiders: ")
        for spider_name in self.list_spiders:
            spider_cls = self.spider_loader.load(spider_name)
            print(f" -[cyan] {spider_name.capitalize():<15}[/] [green]{spider_cls.language.capitalize():<5} [/]{spider_cls.base_url}")

    def find_spider_by_base_url(self) -> Optional[str]:
        """Finds a spider that matches the base URL of the provided URL."""
        for spider_name in self.list_spiders:
            spider_cls = self.spider_loader.load(spider_name)
            if self.is_valid_url(spider_cls.base_url):
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
        """Starts the crawling process using the appropriate spider."""
        if not self.url:
            raise ValueError("Error: Missing argument 'URL'.")

        spider_name = spider_name or self.find_spider_by_base_url()
        if not spider_name:
            raise ValueError("The site is not yet supported.")
        if spider_name not in self.list_spiders:
            raise ValueError(f"Spider with name '{spider_name}' not found.")

        self.processor = SpiderDataProcessor(spider_name)
        self.spider_name = spider_name

        process = CrawlerProcess(self.process_settings)
        process.crawl(spider_name, url=self.url)
        process.start()


# Example of usage
# smanga = SManga(url="https://3asq.org/manga/jujutsu-kaisen/256/")
# smanga.start()
# smanga.process_spider_data()
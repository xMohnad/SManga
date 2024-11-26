from pathlib import Path
from typing import Optional
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.spiderloader import SpiderLoader
from scrapy.settings import Settings
from rich import print

from SManga.core.components import SpiderDataProcessor

# Constants
SUPPORTED_FORMATS = ["json", "jsonlines", "jl", "xml", "pickle", "marshal"]


class SManga:
    def __init__(
        self,
        url: Optional[str] = None,
        dest_path: Optional[Path] = None,
        file_name: Optional[Path] = None,
        overwrite: bool = False,
        user_agent: Optional[str] = None,
    ) -> None:
        """Initializes the SManga class with the given parameters."""
        self.url = url
        self.dest_path = dest_path
        self.file_name = file_name
        self.overwrite = overwrite
        self.file_format = self._validate_file_format(file_name)

        # Prepare process settings and spider loader
        self.process_settings = self._prepare_settings(
            file_name, self.file_format, overwrite, user_agent, dest_path
        )
        self.spider_loader = SpiderLoader.from_settings(self.process_settings)
        self.list_spiders = self.spider_loader.list()
        self.processor = None
        self.spider_name = None

    # Validation Methods
    def _validate_file_format(self, file_name: Optional[Path]) -> str:
        """Validates the file format based on the extension."""
        file_format = (
            str(file_name).rsplit(".", 1)[-1].lower() if file_name else "json"
        )
        if file_format not in SUPPORTED_FORMATS:
            raise TypeError(
                f"Unsupported file format: {file_format}. "
                f"Please use one of the supported formats: {', '.join(SUPPORTED_FORMATS)}."
            )
        return file_format

    def _is_valid_url(self, base_url: str) -> bool:
        """Checks if the provided URL starts with the given base URL."""
        return self.url.startswith(base_url)

    def _validate_spider(self, spider_name: Optional[str]) -> str:
        """Validates the spider name and URL."""
        if not self.url:
            raise ValueError("Error: Missing argument 'URL'.")
    
        spider_name = spider_name or self.find_spider_by_base_url()
        if not spider_name:
            raise ValueError("The site is not yet supported.")
    
        if spider_name not in self.list_spiders:
            raise ValueError(f"Spider with name '{spider_name}' not found.")
    
        return spider_name

    # Settings Preparation
    def _prepare_settings(
        self,
        file_name: Optional[str],
        file_format: str,
        overwrite: bool,
        user_agent: Optional[str],
        dest_path: Optional[Path],
    ) -> dict:
        """Prepares settings for the crawling process."""
        if file_name:
            self.final_file_path = dest_path / file_name
            FEEDS = {
                self.final_file_path: {
                    "format": file_format,
                    "overwrite": overwrite,
                }
            }
        JSON_FEEDS = {
            "overwrite": overwrite,
            "file_name": file_name,
            "dest_path": dest_path,
        }

        settings = {
            **get_project_settings(),
            **(
                {"JSON_FEEDS": JSON_FEEDS}
                if file_format == "json"
                else {"FEEDS": FEEDS}
            ),
        }
        if user_agent:
            settings["USER_AGENT"] = user_agent

        return Settings(settings)

    # Spider Operations
    def print_spiders(self) -> None:
        """Prints the names of all available spiders."""
        print("[magenta]Available spiders: ")
        for spider_name in self.list_spiders:
            spider_cls = self.spider_loader.load(spider_name)
            print(
                f" - [cyan]{spider_name.capitalize():<15}[/] "
                f"[green]{spider_cls.language.capitalize():<5}[/] "
                f"{spider_cls.base_url}"
            )

    def find_spider_by_base_url(self) -> Optional[str]:
        """Finds a spider that matches the base URL of the provided URL."""
        for spider_name in self.list_spiders:
            spider_cls = self.spider_loader.load(spider_name)
            if self._is_valid_url(spider_cls.base_url):
                return spider_name
        return None

    def start(self, spider_name: Optional[str] = None) -> None:
        """Starts the crawling process using the appropriate spider."""
        spider_name = self._validate_spider(spider_name)
        
        # Initialize the processor and start the crawling process
        self.processor = SpiderDataProcessor(spider_name)
        self.spider_name = spider_name
        process = CrawlerProcess(self.process_settings)
    
        process.crawl(spider_name, url=self.url, smanga=self)
        process.start()

    # Data Processing
    def process_spider_data(self) -> None:
        """Processes the scraped data."""
        if self.processor and hasattr(self, "final_file_path"):
            self.processor.process_data(self.final_file_path)

    def load_processed_data(self):
        """Loads the processed data."""
        if self.processor:
            return self.processor.load_processed_data()


# Example usage:
# smanga = SManga(url="https://3asq.org/manga/jujutsu-kaisen/256/")
# smanga.start()
# smanga.process_spider_data()

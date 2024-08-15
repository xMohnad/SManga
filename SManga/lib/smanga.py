from typing import List, Optional
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.spiderloader import SpiderLoader


class SManga:
    def __init__(
        self, url: str, file_name: str = "chapters.json", overwrite: bool = False
    ) -> None:
        """
        Initializes the SManga class with the given parameters.

        :param url: URL of the manga to scrape.
        :param file_name: The name of the file where the scraped data will be saved.
        :param overwrite: Whether to overwrite the file if it already exists.
        """
        self.settings = get_project_settings()
        self.spider_loader = SpiderLoader.from_settings(self.settings)
        self.url = url
        self.file_name = file_name

        supported_formats = [
            "json",
            "jsonlines",
            "jl",
            "csv",
            "xml",
            "pickle",
            "marshal",
        ]

        file_format = file_name.rsplit(".")[-1].lower()
        if file_format not in supported_formats:
            raise TypeError(
                f"Unsupported file format: {file_format}. Please use one of the supported formats: {', '.join(supported_formats)}."
            )

        self.local_settings = {
            "FEEDS": {
                file_name: {
                    "format": file_format,
                    "overwrite": overwrite,
                },
            },
        }

    def is_valid_url(self, base_url: str) -> bool:
        """Checks if the provided URL starts with the given base URL."""
        return self.url.startswith(base_url)

    def list_spiders(self) -> List[str]:
        return self.spider_loader.list()

    def print_spiders(self) -> None:
        """Prints the names of all available spiders."""
        print("Available spiders:")
        for spider_name in self.list_spiders():
            print(f"- {spider_name}")

    def find_spider_by_base_url(self) -> Optional[str]:
        """Finds a spider that matches the base URL of the provided URL."""
        for spider_name in self.list_spiders():
            spider_cls = self.spider_loader.load(spider_name)

            if hasattr(spider_cls, "base_url"):
                if self.is_valid_url(spider_cls.base_url):
                    return spider_name
            else:
                raise NotImplementedError("base_url not defined in spider.")

        return None

    def start(self, spider_name: Optional[str] = None) -> None:
        """
        Starts the crawling process using the appropriate spider.

        :param spider_name: The name of the spider to use. If not provided, the spider is found based on the base URL.
        :raises ValueError: If no suitable spider is found or if the spider name provided does not exist.
        """
        if spider_name:
            if spider_name not in self.list_spiders():
                raise ValueError(f"Spider with name '{spider_name}' not found.")
        else:
            spider_name = self.find_spider_by_base_url()
            if not spider_name:
                raise ValueError("The site is not yet supported")

        process_settings = {**self.settings, **self.local_settings}
        process = CrawlerProcess(process_settings)
        process.crawl(spider_name, url=self.url)
        process.start()


# مثال على كيفية استخدام الفئة
# smanga = SManga(url="https://3asq.org/manga/jujutsu-kaisen/256/")
# smanga.start(spider_name="example_spider")

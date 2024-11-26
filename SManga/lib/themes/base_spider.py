import scrapy
from scrapy.http import Response
from scrapy.selector import Selector
from typing import List, Optional, Generator

from SManga.items import ChapterItem, MangaDetails, SMangaItem

class BaseSpider(scrapy.Spider):
    """
    BaseSpider is the foundation for manga scraping spiders.
    It contains the main logic for scraping manga details and chapters,
    and provides abstract methods for child classes to implement specific behaviors.

    Attributes:
        name (str): The name of the spider (must be set in child classes).
        base_url (str): The base URL of the manga site (set in child classes).
        language (str): The language the manga site (set in child classes).
    """

    name: str = ""
    base_url: str = ""
    language: str = ""

    scraped_details: bool = True
    """
    A flag to indicate if details have been scraped
    (set to False after initial scraping).
    """

    def start_requests(self) -> Generator[scrapy.Request, None, None]:
        """
        Starts the scraping process by making an initial request to the spider's URL.
        This can be overridden to handle multiple starting points if necessary.
        """
        yield scrapy.Request(self.url, dont_filter=True)

    def parse(self, response: Response) -> Generator[scrapy.Request, None, None]:
        """
        Handles the parsing logic for scraping the manga. If the manga details
        are not yet scraped, it extracts them first. Otherwise, it scrapes the chapter data.

        Args:
            response (Response): The response object containing the page content.

        Yields:
            Request: The next request for the following page.
        """
        if self.scraped_details:
            self.scraped_details = False
            home_url = self.extract_home_url(response)
            if home_url:
                yield self.retry_scraping_with_home_url(response, home_url)
                return

        yield self.create_smanga_item(response)

        next_page = self.extract_next_page_url(response)
        if next_page and next_page.startswith("http"):
            yield response.follow(url=next_page.strip(), callback=self.parse)

    def retry_scraping_with_home_url(
        self, response: Response, home_url: str
    ) -> scrapy.Request:
        """
        Generates a retry request using the home URL to scrape manga details.

        Args:
            response (Response): The response object for the initial request.
            home_url (str): The URL of the manga home page.

        Returns:
            Request: A Scrapy request to retry scraping with the home URL.
        """
        return scrapy.Request(
            url=home_url,
            callback=self.get_details_and_retry,
            meta={"retry": response.url},
            dont_filter=True,
        )

    def create_smanga_item(self, response: Response) -> SMangaItem:
        """
        Creates a SMangaItem object from the scraped.

        Args:
            response (Response): The response object containing the chapter's page content.

        Returns:
            SMangaItem: The populated SMangaItem object with chapter item and details item.
        """
        item = SMangaItem()
        details_item = response.meta.get("details_item")
        if details_item:
            item["details"] = details_item
        item["chapters"] = self.create_chapter_item(response)
        return item

    def create_chapter_item(self, response: Response) -> ChapterItem:
        """
        Creates a ChapterItem object from the scraped data of the current chapter.

        Args:
            response (Response): The response object containing the chapter's page content.

        Returns:
            ChapterItem: The populated ChapterItem object with chapter data.
        """
        item = ChapterItem()
        item["title"] = self.extract_title(response)
        item["images"] = self.parse_chapter_image(response)
        item["document_location"] = response.url
        return item

    def get_details_and_retry(
        self, response: Response
    ) -> Generator[scrapy.Request, None, None]:
        """
        Extracts the manga details (name and cover) from the home page and retries scraping
        the original page.

        Args:
            response (Response): The response object for the home page.

        Yields:
            Request: The retry request for the original page.
        """
        item = MangaDetails()

        item["source"] = self.name
        item["manganame"] = self.extract_manga_name(response)
        item["cover"] = self.extract_cover(response)
        item["description"] = self.extract_description(response)
        item["genre"] = self.extract_genre(response)
        item["author"] = self.extract_author(response)
        item["artist"] = self.extract_artist(response)

        retry_url = response.meta.get("retry")
        if retry_url:
            yield response.follow(
                url=retry_url,
                callback=self.parse,
                meta={"details_item": item},
                dont_filter=True,
            )

    ## Abstract Methods to be Implemented by Child Classes

    # details data

    def extract_manga_name(self, response: Response) -> Optional[str]:
        """
        Abstract method for extracting the manga's name from the home page.
        Must be implemented by the child class.

        Returns:
            Optional[str]: The name of the manga.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    def extract_cover(self, response: Response) -> Optional[str]:
        """
        Abstract method for extracting the manga's cover image from the home page.
        Must be implemented by the child class.

        Returns:
            Optional[str]: The URL of the manga's cover image.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    def extract_description(self, response: Response) -> Optional[str]:
        """
        Abstract method for extracting the manga's description from the home page.
        Must be implemented by the child class.

        Returns:
            Optional[str]: The description of the manga's.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    def extract_genre(self, response: Response) -> List[str]:
        """
        Abstract method for extracting the manga's genre from the home page.
        Must be implemented by the child class.

        Returns:
            List[str] The genre of the manga's.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    def extract_author(self, response: Response) -> str:
        """
        Abstract method for extracting the manga's author from the home page.
        Must be implemented by the child class.

        Returns:
            str: The name of the manga's author.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    def extract_artist(self, response: Response) -> str:
        """
        Abstract method for extracting the manga's artist from the home page.
        Must be implemented by the child class.

        Returns:
            str: The name of the manga's artist.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    # URLs

    def extract_home_url(self, response: Response) -> Optional[str]:
        """
        Abstract method for extracting the manga's home page URL.
        Must be implemented by the child class.

        Returns:
            str: The URL of the manga's home page.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    def extract_next_page_url(self, response: Response) -> Optional[str]:
        """
        Abstract method for extracting the next chapter's URL from the current page.
        Must be implemented by the child class.

        Returns:
            Optional[str]: The URL of the next chapter page.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    # chapter data

    def parse_chapter_image(self, response: Response) -> List[str]:
        """
        Abstract method for extracting images from the chapter page.
        Must be implemented by the child class.

        Returns:
            List[str]: A list of image URLs from the chapter.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    def extract_title(self, response: Response) -> str:
        """
        Abstract method for extracting the chapter's title from the page.
        Must be implemented by the child class.

        Returns:
            str: The chapter title.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    # Utility method for extracting image URLs from HTML elements
    def image_from_element(self, element: Selector) -> str:
        """Extracts the image URL from an HTML element using multiple possible attributes."""
        for attr in ["data-lazy-src", "data-src", "srcset", "data-cfsrc", "src"]:
            if element.attrib.get(attr):
                if attr == "srcset":
                    return element.attrib["srcset"].split(" ")[0]
                return element.attrib.get(attr)
        return ""

    # def text_from_element(self, element):

    def clean_text(self, text: Selector, include_all: bool=False, separator: str | None = "\n"):
        """Cleans the provided text."""
        # Check if text is None or contains invalid values
        if not text or all(item.strip() in ["-", "N/A", "n/a"] for item in text.getall()):
            return None
        
        # Return concatenated string if include_all is True
        if include_all:
            if separator:
                return separator.join(item.strip() for item in text.xpath('string()').getall()).strip()
            return [item.strip() for item in text.xpath('string()').getall()]

        # Return single cleaned string
        return text.xpath('string()').get().strip()

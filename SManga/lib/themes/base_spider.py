import scrapy
from SManga.items import ChapterItem
from scrapy.http import Response
from scrapy.selector import Selector
from typing import List, Optional, Generator

class BaseSpider(scrapy.Spider):
    """
    BaseSpider is the foundation for manga scraping spiders. 
    It contains the main logic for scraping manga details and chapters, 
    and provides abstract methods for child classes to implement specific behaviors.

    Attributes:
        name (str): The name of the spider (must be set in child classes).
        base_url (str): The base URL of the manga site (set in child classes).
    """
    name: str = ""
    base_url: str = ""
    language: str = ""

    manganame: Optional[str] = None
    """
    The name of the manga (to be extracted).
    """
    cover: Optional[str] = None
    """
    The cover image URL of the manga (to be extracted).
    """
    
    extract_details_from_current_page: bool = True
    """
    Whether to extract details from the first scraped page (chapter page).

    if details not exist in chapter page set it to False.
    """

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
            home_url = self.handle_initial_scraping(response)
            if home_url:
                yield self.retry_scraping_with_home_url(response, home_url)
                return

        yield self.create_chapter_item(response)

        next_page = self.extract_next_page_url(response)
        if next_page and next_page.startswith("http"):
            yield response.follow(url=next_page.strip(), callback=self.parse)

    def handle_initial_scraping(self, response: Response) -> Optional[str]:
        """
        Handles the initial scraping of manga details (name and cover).
        If these details are not found on the current page, it triggers
        a retry using the home page URL.

        Args:
            response (Response): The response object for the current page.

        Returns:
            Optional[str]: The home URL if the details need to be retried from the homepage.
        """
        self.scraped_details = False
        if self.extract_details_from_current_page:
            self.extract_manga_details(response)

        if not self.manganame or not self.cover:
            return self.extract_home_url(response)
        return None

    def retry_scraping_with_home_url(self, response: Response, home_url: str) -> scrapy.Request:
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

    def create_chapter_item(self, response: Response) -> ChapterItem:
        """
        Creates a ChapterItem object from the scraped data of the current chapter.

        Args:
            response (Response): The response object containing the chapter's page content.

        Returns:
            ChapterItem: The populated ChapterItem object with chapter details.
        """
        item = ChapterItem()
        item["manganame"] = f"{self.manganame} ({self.name})"
        item["cover"] = self.cover
        item["title"] = self.extract_title(response)
        item["images"] = self.parse_chapter_image(response)
        item["document_location"] = response.url
        return item

    def get_details_and_retry(self, response: Response) -> Generator[scrapy.Request, None, None]:
        """
        Extracts the manga details (name and cover) from the home page and retries scraping 
        the original page.

        Args:
            response (Response): The response object for the home page.

        Yields:
            Request: The retry request for the original page.
        """
        self.manganame = self.extract_manga_name_from_home(response)
        self.cover = self.extract_cover_from_home(response)
        retry_url = response.meta.get("retry")
        if retry_url:
            yield response.follow(url=retry_url, callback=self.parse, dont_filter=True)
    
    # Abstract Methods to be Implemented by Child Classes

    def extract_manga_details(self, response: Response) -> None:
        """
        Abstract method for extracting manga details (name, cover) from the current page.
        Must be implemented by the child class.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    def extract_manga_name_from_home(self, response: Response) -> Optional[str]:
        """
        Abstract method for extracting the manga's name from the home page.
        Must be implemented by the child class.

        Returns:
            Optional[str]: The name of the manga.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    def extract_cover_from_home(self, response: Response) -> Optional[str]:
        """
        Abstract method for extracting the manga's cover image from the home page.
        Must be implemented by the child class.

        Returns:
            Optional[str]: The URL of the manga's cover image.
        """
        raise NotImplementedError("This method should be overridden in the child class")

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
        """
        Extracts the image URL from an HTML element using multiple possible attributes.

        Args:
            element (Selector): The HTML element containing the image.

        Returns:
            str: The extracted image URL.
        """
        for attr in ["data-lazy-src", "data-src", "srcset", "data-cfsrc", "src"]:
            if element.attrib.get(attr):
                if attr == "srcset":
                    return element.attrib["srcset"].split(" ")[0]
                return element.attrib.get(attr)
        return ""

from typing import Generator, List, Optional, Union

import scrapy
from scrapy.http.response import Response
from scrapy.selector.unified import Selector, SelectorList

from SManga.items import ChapterItem, MangaDetails, SMangaItem


class BaseSpider(scrapy.Spider):
    """
    BaseSpider is the foundation for manga scraping spiders.
    It contains the main logic for scraping manga details and chapters,
    and provides abstract methods for child classes to implement specific behaviors.

    Attributes:
        name (str): The name of the spider (must be set in child classes).
        base_url (str): The base URL of the manga site (set in child classes).
        language (str): The language of the manga site (set in child classes).
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
        yield scrapy.Request(self.url, dont_filter=True)  # pyright: ignore

    def parse(
        self, response: Response
    ) -> Generator[scrapy.Request | SMangaItem, None, None]:
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
        Creates a SMangaItem object from the scraped data.

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

    # Details Data

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
            Optional[str]: The description of the manga.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    def extract_genre(self, response: Response) -> List[str]:
        """
        Abstract method for extracting the manga's genre from the home page.
        Must be implemented by the child class.

        Returns:
            List[str]: The genres of the manga.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    def extract_author(self, response: Response) -> Optional[str]:
        """
        Abstract method for extracting the manga's author from the home page.
        Must be implemented by the child class.

        Returns:
            Optional[str]: The name of the manga's author.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    def extract_artist(self, response: Response) -> Optional[str]:
        """
        Abstract method for extracting the manga's artist from the home page.
        Must be implemented by the child class.

        Returns:
            Optional[str]: The name of the manga's artist.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    # URLs

    def extract_home_url(self, response: Response) -> Optional[str]:
        """
        Abstract method for extracting the manga's home page URL.
        Must be implemented by the child class.

        Returns:
            Optional[str]: The URL of the manga's home page.
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

    # Chapter Data

    def parse_chapter_image(self, response: Response) -> List[str]:
        """
        Abstract method for extracting images from the chapter page.
        Must be implemented by the child class.

        Returns:
            List[str]: A list of image URLs from the chapter.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    def extract_title(self, response: Response) -> Optional[str]:
        """
        Abstract method for extracting the chapter's title from the page.
        Must be implemented by the child class.

        Returns:
            Optional[str]: The chapter title.
        """
        raise NotImplementedError("This method should be overridden in the child class")

    # Utility Methods

    def image_from_element(
        self, element: Optional[Union[Selector, SelectorList]]
    ) -> Optional[str]:
        """
        Extracts the image URL from an HTML element using multiple possible attributes.

        Args:
            element (Optional[Union[Selector, SelectorList]]): The Scrapy Selector object representing the HTML element.

        Returns:
            Optional[str]: The extracted image URL, or None if no valid URL is found.
        """
        if not element:
            return None

        # Ordered list of attributes to check for the image URL
        attributes = ["data-lazy-src", "data-src", "srcset", "data-cfsrc", "src"]

        for attr in attributes:
            value = element.attrib.get(attr)
            if value:
                # Handle 'srcset' attribute separately (e.g., "image.jpg 2x")
                if attr == "srcset":
                    return value.split(" ")[0]  # Return the first URL in the srcset
                return value

        return None

    def clean_text(
        self,
        text: Optional[Union[Selector, List[Selector]]],
        include_all: bool = False,
        separator: Optional[str] = "\n",
    ) -> Optional[Union[str, List[str]]]:
        """
        Cleans the provided text.

        Args:
            text (Optional[Union[Selector, list[Selector]]]): The Scrapy Selector or list of Selectors.
            include_all (bool): Return all text items if True.
            separator (Optional[str]): Separator for joining text items.

        Returns:
            Optional[Union[str, List[str]]]: Cleaned text or list of texts.
        """
        if text is None:
            return None

        # Normalize to a list for consistent processing
        if isinstance(text, Selector):
            text = [text]  # Wrap a single Selector in a list

        # Check if all elements are empty or contain invalid values
        if all((item.get() or "").strip() in ["-", "N/A", "n/a"] for item in text):
            return None

        if include_all:
            if separator:
                return separator.join(
                    (item.xpath("string()").get() or "").strip() for item in text
                ).strip()
            return [
                (item.xpath("string()").get() or "").strip()
                for item in text
                if item.xpath("string()").get() is not None
            ]

        cleaned_text = text[0].xpath("string()").get()
        return cleaned_text.strip() if cleaned_text else None

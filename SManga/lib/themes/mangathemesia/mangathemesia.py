import base64
import json
from typing import Any, Dict, Generator, List, Optional

from scrapy import Request
from scrapy.http.response import Response

from SManga.items import MangaDetails
from SManga.lib.themes import BaseSpider


class MangaThemesiaSpider(BaseSpider):
    """
    MangaThemesiaSpider is a spider for scraping manga data from MangaThemesia sites.
    It extends the BaseSpider class and implements specific logic for MangaThemesia sites.
    """

    name: str = "MangaThemesiaSpider"
    base_url: str = ""
    language: str = ""

    title_selector: str = "div.headpost > h1::text"
    home_page_selector: str = "div.headpost > div > a::attr(href)"

    script_xpath: str = "//script[contains(text(),'ts_reader')]//text()"
    script_base64_xpath: str = '//script[starts-with(@src, "data:text/javascript;base64,dHNfcmVhZGVyLnJ1bih7")]'

    def extract_title(self, response: Response) -> str:
        """
        Extracts the chapter title from the response.

        Args:
            response (Response): The response object containing the page content.

        Returns:
            str: The cleaned chapter title, or "UnknownChapter" if no title is found.
        """
        title = response.css(self.title_selector).get()
        return title.split("–")[-1].strip() if title else "UnknownChapter"

    def extract_home_url(self, response: Response) -> Optional[str]:
        """
        Extracts the manga's home page URL from the response.

        Args:
            response (Response): The response object containing the page content.

        Returns:
            Optional[str]: The URL of the manga's home page, or None if not found.
        """
        return response.css(self.home_page_selector).get()

    def extract_next_page_url(self, response: Response) -> Optional[str]:
        """
        Extracts the URL of the next chapter page from the response.

        Args:
            response (Response): The response object containing the page content.

        Returns:
            Optional[str]: The URL of the next chapter page, or None if not found.
        """
        script_content = self.get_script_content(response)
        if not script_content:
            return None
        ts_reader = self.parse_script_content(script_content)
        return ts_reader.get("nextUrl")

    def parse_chapter_image(self, response: Response) -> List[str]:
        """
        Extracts the list of image URLs for the current chapter.

        Args:
            response (Response): The response object containing the page content.

        Returns:
            List[str]: A list of image URLs for the chapter.
        """
        script_content = self.get_script_content(response)
        if not script_content:
            return []
        ts_reader = self.parse_script_content(script_content)
        return self.get_chapter(ts_reader)

    def get_chapter(self, ts_reader: Dict[str, Any]) -> List[str]:
        """
        Extracts the list of image URLs from the ts_reader data.

        Args:
            ts_reader (Dict[str, Any]): The parsed ts_reader data.

        Returns:
            List[str]: A list of image URLs for the chapter.
        """
        return ts_reader.get("sources", [{}])[0].get("images", [])

    # Manga Details Selectors
    series_details_selector: str = (
        "div.bigcontent, div.animefull, div.main-info, div.postbody"
    )
    series_cover_selector: str = ".infomanga > div[itemprop=image] img, .thumb img"
    series_manga_name_selector: str = (
        "h1.entry-title, .ts-breadcrumb li:last-child span, h1[itemprop=headline]"
    )
    series_author_selector: str = (
        ".infotable tr:contains(Author) td:last-child, "
        ".tsinfo .imptdt:contains(Author) i, "
        ".fmed b:contains(Author)+span, "
        "span:contains(Author)"
    )
    series_artist_selector: str = (
        ".infotable tr:contains(Artist) td:last-child, "
        ".tsinfo .imptdt:contains(Artist) i, "
        ".fmed b:contains(Artist)+span, "
        "span:contains(Artist)"
    )
    series_description_selector: str = ".desc, .entry-content[itemprop=description]"
    series_alt_name_selector: str = (
        ".alternative, .wd-full:contains(alt) span, .alter, .seriestualt, "
        ".infotable tr:contains(Alternative) td:last-child"
    )
    series_genre_selector: str = (
        "div.gnr a, .mgen a, .seriestugenre a, span:contains(genre)"
    )
    series_type_selector: str = (
        ".infotable tr:contains(type) td:last-child, "
        ".tsinfo .imptdt:contains(type) i, "
        ".tsinfo .imptdt:contains(type) a, "
        ".fmed b:contains(type)+span, "
        "span:contains(type) a, "
        "a[href*=type\\=]"
    )

    alt_name_prefix: str = "Alternative Names: "

    def get_details_and_retry(
        self, response: Response
    ) -> Generator[Request, None, None]:
        """
        Extracts manga details and retries scraping the original page.

        Args:
            response (Response): The response object.

        Yields:
            Request: Retry request for the original page.
        """
        details = response.css(self.series_details_selector)
        item = MangaDetails()
        item["source"] = self.name

        # pyright: ignore
        if details:
            # Extract manga name
            item["manganame"] = self.clean_text(
                details.css(self.series_manga_name_selector)  # pyright: ignore
            )

            # Extract cover image
            item["cover"] = self.image_from_element(
                response.css(self.series_cover_selector)
            )

            # Extract description and alt names
            description = self.clean_text(
                details.css(self.series_description_selector),  # pyright: ignore
                include_all=True,
            )
            alt_name = self.clean_text(
                details.css(self.series_alt_name_selector),  # pyright: ignore
                include_all=True,
            )
            if alt_name:
                description = (
                    f"{description}\n\n{self.alt_name_prefix}{alt_name}".strip()
                )

            # Extract genres and series type
            genres = self.clean_text(
                details.css(self.series_genre_selector),  # pyright: ignore
                include_all=True,
                separator=None,
            )
            series_type = self.clean_text(details.css(self.series_type_selector))  # pyright: ignore

            # Handle series_type type safely
            if series_type and isinstance(genres, list):
                if isinstance(series_type, str):
                    genres.append(series_type)
                else:
                    genres.extend(series_type)

            # Capitalize genres and handle None case
            item["genre"] = (
                [genre.capitalize() for genre in genres if genre]
                if isinstance(genres, list)
                else []
            )

            # Extract author and artist
            item["author"] = self.clean_text(details.css(self.series_author_selector))  # pyright: ignore
            item["artist"] = self.clean_text(details.css(self.series_artist_selector))  # pyright: ignore

        # Retry the original URL with the scraped details
        retry_url = response.meta.get("retry")
        if retry_url:
            yield response.follow(
                url=retry_url,
                callback=self.parse,
                meta={"details_item": item},
                dont_filter=True,
            )

    def get_script_content(self, response: Response) -> Optional[str]:
        """
        Extracts the script content from the response.

        Args:
            response (Response): The response object containing the page content.

        Returns:
            Optional[str]: The script content, or None if not found.
        """
        return (
            response.xpath(self.script_xpath).get()
            or response.xpath(self.script_base64_xpath).get()
        )

    def parse_script_content(self, script_content: str) -> Dict[str, Any]:
        """
        Parses the script content to extract ts_reader data.

        Args:
            script_content (str): The script content containing ts_reader data.

        Returns:
            Dict[str, Any]: The parsed ts_reader data.

        Raises:
            ValueError: If the script content cannot be parsed.
        """
        if not script_content:
            return {}

        try:
            if "base64," in script_content:
                script_content = self.base64_to_str(script_content)
            json_string = script_content.split("ts_reader.run(", 1)[1].split(");", 1)[0]
            return json.loads(json_string)
        except (IndexError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to parse script content: {e}")

    def base64_to_str(self, script: str) -> str:
        """
        Decodes base64-encoded script content to a string.

        Args:
            script (str): The base64-encoded script content.

        Returns:
            str: The decoded script content.

        Raises:
            ValueError: If the script content cannot be decoded.
        """
        try:
            base64_data = script.split("base64,")[1].split('"></script>')[0]
            return base64.b64decode(base64_data).decode("utf-8")
        except (IndexError, UnicodeDecodeError) as e:
            raise ValueError(f"Failed to decode base64 script content: {e}")

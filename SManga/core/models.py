from typing import List, Optional, TypedDict


class Chapter(TypedDict):
    title: str
    document_location: str
    images: List[str]


class MangaDetails(TypedDict):
    source: str
    manganame: str
    description: str
    cover: str
    genre: List[str]
    author: Optional[str]
    artist: Optional[str]


class ScrapedData(TypedDict):
    details: MangaDetails
    chapters: List[Chapter]


class ProcessedEntry(TypedDict):
    site: str
    manganame: str
    lastchapter: str
    json_file: str

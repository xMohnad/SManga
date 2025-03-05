from dataclasses import asdict, dataclass, fields
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


@dataclass
class LastChapter:
    site: str
    name: str
    last_chapter: str
    file_name: str

    @property
    def asdict(self):
        def filter_fields(field_list):
            return {
                f.name: getattr(self, f.name)
                for f in field_list
                if not f.metadata.get("exclude", False)
            }

        return asdict(self, dict_factory=lambda _: filter_fields(fields(self)))

    def __eq__(self, other):
        if isinstance(other, dict):
            return self.site == other.get("site") and self.name == other.get("name")
        elif isinstance(other, LastChapter):
            return self.site == other.site and self.name == other.name
        return False

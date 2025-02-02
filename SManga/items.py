# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MangaDetails(scrapy.Item):
    source = scrapy.Field()
    manganame = scrapy.Field()
    cover = scrapy.Field()
    description = scrapy.Field()
    genre = scrapy.Field()
    author = scrapy.Field()
    artist = scrapy.Field()


class ChapterItem(scrapy.Item):
    title = scrapy.Field()
    images = scrapy.Field()
    document_location = scrapy.Field()


class SMangaItem(scrapy.Item):
    details = scrapy.Field()
    chapters = scrapy.Field()

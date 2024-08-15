# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ChapterItem(scrapy.Item):
    manganame = scrapy.Field()
    title = scrapy.Field()
    images = scrapy.Field()
    cover = scrapy.Field()
    document_location = scrapy.Field()

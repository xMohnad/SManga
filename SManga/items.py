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





{
    "details": {
        "source": "TeamX",
        "manganame": "Villain Is Here",
        "cover": "https://teamoney.site/images/manga/20781135161542011176.jpg",
        "description": "انتقل غو تشانغ يي الى عالم آخر...",
        "genre": [
            "أكشن",
            "إثارة",
            "إيسيكاي",
            "بطل غير إعتيادي",
            "خيال",
            "دموي",
            "نظام",
            "صقل",
            "قوة خارقة",
            "فنون قتال",
            "غموض"
        ],
        "author": "Unknown",
        "artist": "غير معروف"
    },
    "chapters": [
        {
            "title": "الفصل 185 - انهيار القصر !!",
            "images": [
                "https://teamoney.site/uploads/manga_c81e7/185/image1.jpg",
                "https://teamoney.site/uploads/manga_c81e7/185/image2.jpg",
                "...etc"
            ],
            "document_location": "https://teamoney.site/series/villain-is-here/185"
        },
        {
                "title": "الفصل 186 - الخادمة الجديدة !!",
                "images": [
                    "https://teamoney.site/uploads/manga_c81e7/186/image1.jpg",
                    "https://teamoney.site/uploads/manga_c81e7/186/image2.jpg",
                    "...etc"
                ],
                "document_location": "https://teamoney.site/series/villain-is-here/186"
        }
    ]
}

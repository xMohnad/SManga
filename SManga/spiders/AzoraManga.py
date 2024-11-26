from SManga.lib.themes.madara import Madara
from scrapy.http import Response
from typing import Optional


class AzoramangaSpider(Madara):
    name = "Azora"
    base_url = "https://azoramoon.com/"
    language = "Ara"
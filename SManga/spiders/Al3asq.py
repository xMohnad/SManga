from scrapy.http import Response
from SManga.lib.themes.madara import Madara


class Al3asqSpider(Madara):
    name = "Al3asq"
    allowed_domains = ["3asq.org"]
    base_url = "https://3asq.org/"
    extract_info_from_script = True

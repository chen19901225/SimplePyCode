# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from cnbeta.items import CnbetaItem
from scrapy.selector.unified import Selector


class CnbetaSpider(CrawlSpider):
    name = "Cnbeta"
    allowed_domains = ["cnbeta.com"]
    start_urls = (
        'http://www.cnbeta.com/',
    )
    rules=(Rule(SgmlLinkExtractor(allow='/articles/.*\.htm'),callback='parse_page',follow=True),)

    def parse_page(self,response):
        item=CnbetaItem()
        sel=Selector(response)
        item["title"]=sel.xpath('//title/text()').extract()
        item['url']=response.url
        return item




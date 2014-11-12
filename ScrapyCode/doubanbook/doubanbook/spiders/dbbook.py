# -*- coding: utf-8 -*-
from cssselect import Selector
import scrapy
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import Rule


class DbbookSpider(scrapy.Spider):
    name = "dbbook"
    allowed_domains = ["douban.com"]
    start_urls = (
        'http://book.douban.com/',
    )

    rules=[Rule(SgmlLinkExtractor(allow=("/subject/\d+/?$")),callback='parse_2'),
           Rule(SgmlLinkExtractor(allow=("/tag/[^/]+/?$")),follow=True),
           Rule(SgmlLinkExtractor(allow=("/tag/$")),follow=True)
           ]

    def parse_2(self, response):
        items = []
        sel = Selector(response)
        sites = sel.css('#wrapper')
        for site in sites:
            item = DoubanSubjectItem()
            item['title'] = site.css('h1 span::text').extract()
            item['link'] = response.url
            item['content_intro'] = site.css('#link-report .intro p::text').extract()
            items.append(item)
            print repr(item).decode("unicode-escape") + '\n'
        # info('parsed ' + str(response))
        return items


    def parse(self, response):
        pass

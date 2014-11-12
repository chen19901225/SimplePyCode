import scrapy
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule

__author__ = 'cqh'

class MySpider(CrawlSpider):
    name='example_com'
    allowed_domains=['example.com']
    start_urls=['http://www.example.com']

    rules=(
        Rule(SgmlLinkExtractor(allow=('category\.php'),deny=('subsection\.php'))),
    )

    def parse_item(self,response):
        self.log("Hi,This is an Item page!%s"%response.url)
        item=scrapy.Item()
        item['id']=response.xpath('//td[@id="item_id"]/text()').re(r"ID:(\d+)")
        item['name']=response.xpath('//td[@id="item_name/text()"]').extract()
        item["description"]=response.xpath('//td[@id="item_description"]/text()').extract()

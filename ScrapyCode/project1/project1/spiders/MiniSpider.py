from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule

from project1.project1.items import TorrentItem


__author__ = 'Administrator'

class MininovaSpider(CrawlSpider):
    name="mininova"
    allowed_doadmins=['mininova.org']
    start_urls=['http://www.mininova.org/today']
    rules=[Rule(SgmlLinkExtractor(allow=[r'/tor/\d+']),'parse_torrent')]

    def parse_torrent(self,response):
        torrent=TorrentItem()
        torrent['url']=response.url
        torrent['name']=response.xpath('//h1/text()').extract()
        torrent['descriptio']=response.xpath("//div[@id='description']").extract()
        torrent['size']=response.xpath("//div[@id='info-left']/p[2]/text()[2]").extract()

# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Field

class DoubanbookItem(scrapy.Item):
    title=Field()
    link=Field()
    desc=Field()
    num=Field()


class DoubanSubjectItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title=Field()
    link=Field()
    rate=Field()
    votes=Field()
    content_intro=Field()
    author_intro=Field()
    tags=Field()


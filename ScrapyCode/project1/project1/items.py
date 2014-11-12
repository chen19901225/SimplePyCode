# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html


from scrapy.item import Item, Field

class Project1Item(Item):
    # define the fields for your item here like:
    # name = Field()
    pass


class TorrentItem(Item):
    url=Field()
    name=Field()
    description=Field()
    size=Field()

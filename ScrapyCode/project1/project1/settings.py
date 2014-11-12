# Scrapy settings for project1 project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

BOT_NAME = 'project1'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['project1.spiders']
NEWSPIDER_MODULE = 'project1.spiders'
USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)


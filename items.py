# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field


class TwitterItem(scrapy.Item):
    
    ID = Field()       # tweet id
    text = Field()     # text tweet
    date = Field() # date publication
    username = Field() # username de l'auteur du tweet

    
    # define the fields for your item here like:
    # name = scrapy.Field()
    

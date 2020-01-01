# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#from scrapy.exception import DropItem


import re


class TwitterPipeline(object):

    def process_item(self,item,spider):
        
        tweet=item['text']

        tweet=re.sub("<[^>]*>","",tweet)  #supprimes les balises html
        
        #suprimes les tweets qui indiques une mention ou retweets 
        if not re.search("added,|Retweeted",tweet):
            item['text']=tweet
            
            return item

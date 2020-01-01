# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import Selector
import re
import logging
import json
from twitter.items import TwitterItem

from datetime import datetime


#from items import TwitterItem

from urllib.parse import quote  # Python 3

#from items import TwitterItem


class TwitterScraperSpider(scrapy.Spider):
    
    def __init__(self, *args, **kwargs):

        logger = logging.getLogger('scrapy.middleware')
        logger.setLevel(logging.WARNING)

        #self.query = ''
        #self.lang=lang
        self.query='' #initialise la requete de recherche twitter
        
        
        #parse word or hashtag
        if 'word' not in kwargs:
            self.logger.info('Word Or Hashtag attribute not provided')
            self.word=''
        else :
            self.query=kwargs['word']+' ' #ajoute le mot ou le hashtag dans la requete

        #À proximité de ce lieu
        if 'place' not in kwargs:
            self.logger.info('Place attribute not provided')
            self.place=None
        else :
            #distance en mille (1 mi =1,60 km)
            if 'distance' not in kwargs:
                self.distance='15mi' #distance par defaut
            else:
                self.distance=kwargs['distance']+'mi'
            #ajoute le lieux et la distance dans la requete
            self.query=self.query+'near:"'+kwargs['place']+'" within:'+self.distance+' ' 
        #parse date
        if 'date' not in kwargs:
            self.logger.info('Date attribute not provided, scraping since today ')
            self.date =None
        else:
            self.date = datetime.strptime(kwargs['date'],'%Y-%m-%d')
            self.logger.info('Date attribute provided, twitter_scraper will crawling since {}'.format(kwargs['date']))

            #ajoute le lieux et la distance dans la requete
            self.query=self.query+' since:'+str(self.date)+' '

        #parse lang, if not provided (but is supported) it will be guessed in parse_home
        if 'lang' not in kwargs:

            self.logger.info('Language attribute not provided, fbcrawl will try to guess it from the fb interface')
            self.logger.info('To specify, add the lang parameter: scrapy fb -a lang="LANGUAGE"')
            self.logger.info('Currently choices for "LANGUAGE" are: "en", "es", "fr", "it", "ar","pt"')
            self.lang = 'fr'

        elif kwargs['lang'] in ['en','es','fr','it','ar','pt']:

            self.lang=kwargs['lang']
            self.logger.info('Language attribute recognized, using "{}" '.format(self.lang))

        else:
            self.logger.info('Lang "{}" not currently supported'.format(self.lang))                             
            self.logger.info('Currently supported languages are: "en", "es", "fr", "it", "ar"')
            raise AttributeError('Language provided not currently supported')
        
        #URL qui va effectuer la requete,on lui passe la position minimal
        self.url="https://twitter.com/i/search/timeline?f=tweets&vertical=default&q=%s&l=%s&src=typd&include_available_features=1&include_entities=1&reset_error_state=false&max_position=%s"
        
        
        #URL qui va simuler un scrolling vers le bas,on lui passe la position minimal
        self.url_scrolling="https://twitter.com/i/search/timeline?f=tweets&vertical=default&q=%s&l=%s&src=typd&composed_count=0&include_available_features=1&include_entities=1&include_new_items_bar=true&interval=30000&latent_count=0&min_position=%s"
    

    name = 'twitter_scraper'
    custom_settings = {
        
        'LOG_LEVEL': logging.WARNING,

        'FEED_FORMAT':'csv', # format d'exportation
        'FEED_URI': 'tweets.csv', # fichier d'exportation
        'FEED_EXPORT_ENCODING': 'utf-8', #encodage
        'COOKIES_ENABLED ': False, # Disable cookies (enabled by default)
    
        'ROBOTSTXT_OBEY': False ,# Obey robots.txt rules  
        }
    
    #allowed_domains = ['wwww.twitter.com/search']
    #start_urls = ["https://twitter.com/i/search/timeline?f=tweets&vertical=default&q="+self.query+"&l="self.lang+"&src=typd&composed_count=0&include_available_features=1&include_entities=1&include_new_items_bar=true&interval=30000&latent_count=1&min_position="]    

    def start_requests(self):

        
        url =self.url % (quote(self.query),self.lang,'')
        yield scrapy.Request(url, callback=self.parse_page)

    
    
    def parse_page(self, response):
        
        # inspect_response(response, self)
        # handle current page
        data = json.loads(response.text,encoding="utf8")

        html=data['items_html']  #recupere le code html des tweets scraper
        page = Selector(text=html) #convertisse le html en xpath

        paragraphes=page.css(".tweet p").getall()  #recupere les paragraphes des tweets

        texts=[re.sub("<[^>]*>","",tweet) for tweet in paragraphes]  #supprimes les balises html

        #suprimes les phrases qui indiques une mention ou retweets 
        texts=[ tweet for tweet in texts if not re.search('added,|Retweeted',tweet)]

        ids=page.xpath('.//@data-tweet-id').getall() #recupere les ids des tweets

        usernames=page.xpath('.//span[@class="username u-dir u-textTruncate"]/b/text()').getall()

         #recupere le timestampe de la date du tweet
        dates=page.xpath('.//div[@class="stream-item-header"]/small[@class="time"]/a/span/@data-time').getall()
        #formate la date
        dates=[datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d %H:%M:%S')for date in dates ] 


        for ID,text,date,username in zip(ids,texts,dates,usernames):

           yield {"ID":ID,"text":text,"date":date,"username":username}

       
        #Pour recuper la page suivante on passe à l'url du scrolling la requete et la position minimal
        min_position=data['min_position'] #recupere la position minimal de la page
        
        #affecter 'min_position' au parametre 'min_position' pour simuler un scrolling
        url = self.url_scrolling % (quote(self.query),self.lang, min_position)

        yield scrapy.Request(url, callback=self.parse_scrolling)

        
    
    def parse_tweet_item(self,items):
         for item in items :
             text=item.css(".tweet p").get()
             # If there is not text, we ignore the tweet
             if text is not None :
                 tweet=TwitterItem() #instancie un nouvelle item 
                 tweet['text']=tweet  #recupere le text du tweet

                 #recupere le timestampe de la date du tweet
                 date=int(item.xpath('.//div[@class="stream-item-header"]/small[@class="time"]/a/span/@data-time').get())
                 date=datetime.fromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S') #formate la date

                 tweet['date']=date 

                 tweet['ID']=item.xpath('.//@data-tweet-id').get() #recupere l'id du tweet

                 tweet['username']=item.xpath('.//span[@class="username u-dir u-textTruncate"]/b/text()').get()

                 yield tweet


    def parse_scrolling(self, response):

        data = json.loads(response.text,encoding="utf8")


        #affecter 'max_position' au parametre 'min_position' de la requete pour aller a la page suivante

        max_position=data['max_position'] #recupere la position maximal du scroll

        url = self.url % (quote(self.query),self.lang,max_position)

        
        yield scrapy.Request(url, callback=self.parse_page)





    

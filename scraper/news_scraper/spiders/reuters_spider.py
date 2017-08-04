# -*- coding: utf-8 -*-
import re
from datetime import datetime
import logging
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from news_scraper.items import ReutersItem

def process_for_multi_pages(value):
    if '?sp=true' in value:
        return value
    else:
        return value.split('?pageNumber=')[0] + '?sp=true'
    
class ReutersSpider(CrawlSpider):
    name = 'reuters'
    allowed_domains = ['internal.jp.reuters.com', 'jp.reuters.com']
    start_urls = ['http://internal.jp.reuters.com']
    start_urls += ['http://internal.jp.reuters.com/search/news?sortBy=&dateRange=&blob=%d'%x for x in range(1990, 2017)]
    
    rules = [Rule(LinkExtractor(deny=['http://(internal.)?jp.reuters.com/(%s).*$'
                                      % '|'.join(['video', 'info', 'tools', 'article', 'investing'])])),
             Rule(LinkExtractor(allow=['http://(internal.)?jp.reuters.com/(%s)/$'
                                       % '|'.join(['investing', 'investing/news'])])),
             Rule(LinkExtractor(allow=['http://(internal.)?jp.reuters.com/article.*'],
                                deny=['^.*\?pageNumber=([2-9]|[1-9][0-9]).*$', '^.*\?sp=true.+$'],
                                process_value=process_for_multi_pages),
                  callback='parse_articles',
                  follow=True)]

    
    def parse_articles(self, response):
        url = response.url
        item = ReutersItem()
        item['URL'] = url
        m = re.search('(idJP[^\?]*)', url)
        if m:
            item['ID'] = 'JP' + m.group(0)
        else:
            item['ID'] = ''
            self.logger.error('Cannot parse ID from url: <%s>', url)

        item['category'] = response.xpath('//*[@class="article-section"]/text()').extract()[0]
        item['title'] = response.xpath('//h1[@class="article-headline"]/text()').extract()[0].replace('\u3000', ' ')
        item['content'] = ''.join([x.replace('\u3000', ' ') for x in response.xpath('//*[@id="articleText"]//p/text()').extract()])
        item['publication_datetime'] = response.xpath('//*[@class="article-header"]//*[@class="timestamp"]/text()').extract()[0]
        item['scraping_datetime'] = datetime.now().strftime('%Y年 %m月 %d日 %H:%M JST')

        self.logger.info('scraped from <%s> published in %s' % (item['URL'], item['publication_datetime']))

        return item

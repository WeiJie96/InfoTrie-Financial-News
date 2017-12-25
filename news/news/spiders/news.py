import scrapy
import re
'''
Settings for command line input

scrapy crawl News -o investnews.csv -s USER_AGENT="Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36" -s FEED_FORMAT="csv"
'''

class FinNewsScraper(scrapy.Spider):
    name = "News"
    start_urls = [
        "https://www.investing.com/news/"
    ]

    custom_settings = {
        "FEED_EXPORT_FIELDS":["DateTime","Source","Category","Title","Content"]
    }

    
    def parse(self, response):

        #Follow article links
        for article_link in response.css('div#latestNews article.articleItem a.img::attr(href)'):
            article_link = "https://www.investing.com" + article_link.extract()
            yield response.follow(article_link, self.parse_article_page)
            

    def parse_article_page(self, response):

        article_dict = {}

        DateTime = response.css('div.contentSectionDetails span::text').extract_first()
        #Retrieve date within brackets
        match = re.search(r"\((.*?)\)",DateTime)
        if match:
        	article_dict["DateTime"] = match.group(1)
        else:
        	article_dict["DateTime"] = DateTime

        article_dict["Source"] = response.xpath('//meta[@property="article:author"]/@content').extract()
        #Some articles e.g.	https://www.investing.com/news/economy-news/economic-calendar-top-things-to-watch-this-week-1027471 may not have article:author property, so look for source in title instead
        if article_dict["Source"] == []:
            title = response.css('title::text').extract_first()
            search = re.search(r"By (.*)",title)
            if search:
                article_dict["Source"] = search.group(1)

        article_dict["Category"] = response.css('div.contentSectionDetails a::text').extract() 
               
        article_dict["Title"] = response.css('div.floatingH1::text').extract()

        #Retrieve content from p/li tags
        content_list = response.css('div.arial_14.clear.WYSIWYG.newsPage p').extract()
        content_list2 = response.css('div.arial_14.clear.WYSIWYG.newsPage li').extract()
        content_raw = ""
        for para in content_list:
        	content_raw += para
        for line in content_list2:
        	content_raw += line
        #Replace closing/opening/br tags with new line
        content_raw = re.sub(r"</p><p>","\n",content_raw)
        content_raw = re.sub(r"</li><li>","\n",content_raw)
        content_raw = re.sub(r"<br>","\n",content_raw)
        content_raw = re.sub(r"<br/>","\n",content_raw)
        content_raw = re.sub(r"<br />","\n",content_raw)        
        content_raw = re.sub(r"</a>"," ",content_raw)

        #Remove all other tags
        content_raw = re.sub(r"<.*?>","",content_raw)

        #Remove extra new lines
        lst = [line for line in content_raw.split('\n') if line.strip()]
        article_dict["Content"] = '\n'.join(lst)

        yield article_dict

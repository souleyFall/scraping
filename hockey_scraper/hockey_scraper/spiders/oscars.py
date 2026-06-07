import scrapy
import json
from hockey_scraper.items import OscarFilmItem


class OscarsSpider(scrapy.Spider):
    name = 'oscars'
    allowed_domains = ['scrapethissite.com']
    start_urls = ['https://www.scrapethissite.com/pages/ajax-javascript/']
    
    def parse(self, response):
        # Extract available years from the page
        years = response.css('a.year-link::attr(id)').getall()
        
        for year in years:
            # Make AJAX request for each year
            ajax_url = f'https://www.scrapethissite.com/pages/ajax-javascript/?ajax=true&year={year}'
            
            yield scrapy.Request(
                url=ajax_url,
                callback=self.parse_ajax,
                meta={'year': year}
            )
    
    def parse_ajax(self, response):
        # Parse JSON response
        data = json.loads(response.text)
        year = response.meta['year']
        
        if isinstance(data, list):
            for film_data in data:
                item = OscarFilmItem()
                item['title'] = film_data.get('title', '').strip()
                item['year'] = int(film_data.get('year', year))
                item['awards'] = int(film_data.get('awards', 0))
                item['nominations'] = int(film_data.get('nominations', 0))
                item['best_picture'] = bool(film_data.get('best_picture', False))
                yield item

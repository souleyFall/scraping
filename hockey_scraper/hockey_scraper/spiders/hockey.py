import scrapy
from hockey_scraper.items import HockeyTeamItem


class HockeySpider(scrapy.Spider):
    name = 'hockey'
    allowed_domains = ['scrapethissite.com']
    
    def __init__(self, team_name=None, year=None, *args, **kwargs):
        super(HockeySpider, self).__init__(*args, **kwargs)
        self.team_name = team_name
        self.year = year
        
        # Build start URL with query parameters if provided
        self.start_urls = ['https://www.scrapethissite.com/pages/forms/']
        if team_name:
            self.start_urls = [f'https://www.scrapethissite.com/pages/forms/?q={team_name}']
    
    def parse(self, response):
        # Extract team data from current page
        rows = response.css('table.table tr')
        
        for row in rows[1:]:  # Skip header row
            team_name = row.css('td:nth-child(1)::text').get()
            year = row.css('td:nth-child(2)::text').get()
            wins = row.css('td:nth-child(3)::text').get()
            losses = row.css('td:nth-child(4)::text').get()
            ot_losses = row.css('td:nth-child(5)::text').get()
            win_pct = row.css('td:nth-child(6)::text').get()
            goals_for = row.css('td:nth-child(7)::text').get()
            goals_against = row.css('td:nth-child(8)::text').get()
            
            if team_name:  # Only process if we have data
                # Filter by year if specified
                if self.year:
                    parsed_year = None
                    if year and year.strip():
                        try:
                            parsed_year = int(year.strip())
                        except ValueError:
                            pass
                    if parsed_year != int(self.year):
                        continue
                
                item = HockeyTeamItem()
                item['team_name'] = team_name.strip() if team_name else None
                
                # Helper function to safely convert to int
                def safe_int(value):
                    if value and value.strip():
                        try:
                            return int(value.strip())
                        except ValueError:
                            return None
                    return None
                
                # Helper function to safely convert to float
                def safe_float(value):
                    if value and value.strip():
                        try:
                            return float(value.strip())
                        except ValueError:
                            return None
                    return None
                
                item['year'] = safe_int(year)
                item['wins'] = safe_int(wins)
                item['losses'] = safe_int(losses)
                item['ot_losses'] = safe_int(ot_losses)
                item['win_pct'] = safe_float(win_pct)
                item['goals_for'] = safe_int(goals_for)
                item['goals_against'] = safe_int(goals_against)
                yield item
        
        # Handle pagination
        next_page = response.css('ul.pagination li:last-child a::attr(href)').get()
        if next_page and 'page_num' in next_page:
            yield response.follow(next_page, callback=self.parse)

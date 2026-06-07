# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class HockeyScraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class HockeyTeamItem(scrapy.Item):
    team_name = scrapy.Field()
    team_name_normalized = scrapy.Field()
    year = scrapy.Field()
    wins = scrapy.Field()
    losses = scrapy.Field()
    ot_losses = scrapy.Field()
    win_pct = scrapy.Field()
    performance_category = scrapy.Field()
    goals_for = scrapy.Field()
    goals_against = scrapy.Field()


class OscarFilmItem(scrapy.Item):
    title = scrapy.Field()
    year = scrapy.Field()
    awards = scrapy.Field()
    nominations = scrapy.Field()
    best_picture = scrapy.Field()

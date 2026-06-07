# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import sqlite3
import os
from itemadapter import ItemAdapter


class HockeyScraperPipeline:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    @classmethod
    def from_crawler(cls, crawler):
        db_path = crawler.settings.get('DB_PATH', 'hockey_teams.db')
        return cls(db_path)
    
    def open_spider(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def close_spider(self):
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        # Create hockey teams table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS hockey_teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL,
                team_name_normalized TEXT,
                year INTEGER NOT NULL,
                wins INTEGER,
                losses INTEGER,
                ot_losses INTEGER,
                win_pct REAL,
                performance_category TEXT,
                goals_for INTEGER,
                goals_against INTEGER,
                UNIQUE(team_name, year)
            )
        ''')
        
        # Create oscar films table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS oscar_films (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                year INTEGER NOT NULL,
                awards INTEGER,
                nominations INTEGER,
                best_picture BOOLEAN,
                UNIQUE(title, year)
            )
        ''')
        
        self.conn.commit()
    
    def process_item(self, item):
        adapter = ItemAdapter(item)
        
        # Check if it's a hockey team or oscar film
        if 'team_name' in adapter:
            # Hockey team item
            self.cursor.execute('''
                INSERT OR REPLACE INTO hockey_teams 
                (team_name, team_name_normalized, year, wins, losses, ot_losses, win_pct, performance_category, goals_for, goals_against)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                adapter.get('team_name'),
                adapter.get('team_name_normalized'),
                adapter.get('year'),
                adapter.get('wins'),
                adapter.get('losses'),
                adapter.get('ot_losses'),
                adapter.get('win_pct'),
                adapter.get('performance_category'),
                adapter.get('goals_for'),
                adapter.get('goals_against')
            ))
        elif 'title' in adapter:
            # Oscar film item
            self.cursor.execute('''
                INSERT OR REPLACE INTO oscar_films 
                (title, year, awards, nominations, best_picture)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                adapter.get('title'),
                adapter.get('year'),
                adapter.get('awards'),
                adapter.get('nominations'),
                adapter.get('best_picture')
            ))
        
        self.conn.commit()
        return item

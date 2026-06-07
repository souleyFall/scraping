import os
import re
import google.generativeai as genai
from itemadapter import ItemAdapter


class LLMEnrichmentPipeline:
    VALID_CATEGORIES = {"Elite", "Good", "Average", "Poor", "Unknown"}
    
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-flash-latest')
    
    @classmethod
    def from_crawler(cls, crawler):
        api_key = crawler.settings.get('GEMINI_API_KEY', os.getenv('GEMINI_API_KEY'))
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set in settings or environment variable")
        return cls(api_key)
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Only enrich hockey team items
        if 'team_name' not in adapter:
            return item
        
        team_name = adapter.get('team_name')
        win_pct = adapter.get('win_pct')
        
        # Normalize team name using LLM with validation
        normalized_name = self.normalize_team_name(team_name, spider)
        adapter['team_name_normalized'] = normalized_name
        
        # Categorize performance using LLM with validation
        performance_category = self.categorize_performance(win_pct, spider)
        adapter['performance_category'] = performance_category
        
        return item
    
    def normalize_team_name(self, team_name, spider):
        """Use LLM to normalize team name (remove extra spaces, standardize format)"""
        if not team_name:
            return team_name
        
        prompt = f"""Normalize this hockey team name by removing extra spaces and standardizing the format.
Return ONLY the normalized name, nothing else.

Team name: "{team_name}"
Normalized name:"""
        
        try:
            response = self.model.generate_content(prompt, generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=50,
            ))
            normalized = response.text.strip()
            
            # Validation: ensure output is not empty and contains valid characters
            if not normalized or not re.match(r'^[A-Za-z0-9\s\-\.]+$', normalized):
                spider.logger.warning(f"LLM normalization validation failed for {team_name}: invalid output '{normalized}'")
                return team_name
            
            # Validation: ensure output is reasonable length
            if len(normalized) > 100 or len(normalized) < 2:
                spider.logger.warning(f"LLM normalization validation failed for {team_name}: invalid length '{len(normalized)}'")
                return team_name
            
            return normalized
        except Exception as e:
            spider.logger.warning(f"LLM normalization failed for {team_name}: {e}")
            return team_name
    
    def categorize_performance(self, win_pct, spider):
        """Use LLM to categorize team performance based on win percentage with validation"""
        if win_pct is None:
            return "Unknown"
        
        prompt = f"""Categorize this hockey team's performance based on win percentage.
Categories: Elite (>=0.600), Good (0.500-0.599), Average (0.400-0.499), Poor (<0.400)
Return ONLY the category name, nothing else.

Win percentage: {win_pct}
Category:"""
        
        try:
            response = self.model.generate_content(prompt, generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=20,
            ))
            category = response.text.strip()
            
            # Validation: ensure category is in allowed set
            if category not in self.VALID_CATEGORIES:
                spider.logger.warning(f"LLM categorization validation failed for win_pct {win_pct}: invalid category '{category}'")
                # Fallback to simple logic
                return self._fallback_categorization(win_pct)
            
            return category
        except Exception as e:
            spider.logger.warning(f"LLM categorization failed for win_pct {win_pct}: {e}")
            # Fallback to simple logic
            return self._fallback_categorization(win_pct)
    
    def _fallback_categorization(self, win_pct):
        """Simple logic-based categorization as fallback"""
        if win_pct >= 0.600:
            return "Elite"
        elif win_pct >= 0.500:
            return "Good"
        elif win_pct >= 0.400:
            return "Average"
        else:
            return "Poor"

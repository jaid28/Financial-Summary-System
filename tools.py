import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
from crewai_tools import tool
from litellm import completion
from config import config

logger = logging.getLogger(__name__)

@tool
def search_financial_news(query: str, hours_back: int = 1) -> List[Dict[str, Any]]:
    """Search for recent financial news using Serper API"""
    try:
        url = "https://google.serper.dev/search"
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Enhanced query for financial news
        enhanced_query = f"{query} after:{start_time.strftime('%Y-%m-%d')} financial markets trading stocks"
        
        payload = {
            "q": enhanced_query,
            "num": config.MAX_NEWS_ITEMS,
            "type": "news"
        }
        
        headers = {
            "X-API-KEY": config.SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        results = response.json()
        news_items = []
        
        for item in results.get("news", []):
            news_items.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
                "date": item.get("date", ""),
                "source": item.get("source", "")
            })
        
        logger.info(f"Found {len(news_items)} news items")
        return news_items
        
    except Exception as e:
        logger.error(f"Error searching financial news: {e}")
        return []

@tool
def get_groq_analysis(news_text: str) -> str:
    """Get additional analysis from Groq API"""
    try:
        response = completion(
            model=config.LITELLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial analyst. Provide a concise analysis of the given financial news."
                },
                {
                    "role": "user", 
                    "content": f"Analyze these financial news items and provide key insights: {news_text}"
                }
            ],
            api_key=config.GROQ_API_KEY
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error getting Groq analysis: {e}")
        return "Analysis unavailable"

@tool
def find_financial_charts(search_query: str) -> List[str]:
    """Find relevant financial charts and images"""
    try:
        url = "https://google.serper.dev/images"
        
        payload = {
            "q": f"{search_query} financial chart graph market trading",
            "num": 10
        }
        
        headers = {
            "X-API-KEY": config.SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        results = response.json()
        image_urls = []
        
        for item in results.get("images", []):
            if any(keyword in item.get("title", "").lower() for keyword in ["chart", "graph", "market", "stock", "trading"]):
                image_urls.append(item.get("imageUrl", ""))
        
        return image_urls[:2]  # Return top 2 relevant images
        
    except Exception as e:
        logger.error(f"Error finding charts: {e}")
        return []

@tool
def send_telegram_message(message: str, image_paths: List[str] = None) -> bool:
    """Send message to Telegram channel"""
    try:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        
        payload = {
            "chat_id": config.TELEGRAM_CHANNEL_ID,
            "text": message,
            "parse_mode": config.TELEGRAM_PARSE_MODE
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        # Send images if provided
        if image_paths:
            for image_path in image_paths:
                try:
                    with open(image_path, 'rb') as image_file:
                        files = {'photo': image_file}
                        data = {'chat_id': config.TELEGRAM_CHANNEL_ID}
                        requests.post(
                            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendPhoto",
                            files=files,
                            data=data
                        )
                except Exception as img_error:
                    logger.error(f"Error sending image {image_path}: {img_error}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False

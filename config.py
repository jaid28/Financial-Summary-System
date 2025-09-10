import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for the Financial Summary System"""
    
    # API Keys
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
    
    # LLM Configuration
    LITELLM_MODEL = os.getenv("LITELLM_MODEL", "groq/llama3-8b-8192")
    
    # System Configuration
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Search Configuration
    SEARCH_HOURS_BACK = int(os.getenv("SEARCH_HOURS_BACK", "1"))
    MAX_NEWS_ITEMS = int(os.getenv("MAX_NEWS_ITEMS", "20"))
    
    # Summary Configuration
    MAX_SUMMARY_WORDS = int(os.getenv("MAX_SUMMARY_WORDS", "500"))
    TARGET_LANGUAGES = os.getenv("TARGET_LANGUAGES", "Arabic,Hindi,Hebrew").split(",")
    
    # Telegram Configuration
    TELEGRAM_PARSE_MODE = os.getenv("TELEGRAM_PARSE_MODE", "HTML")
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            "SERPER_API_KEY",
            "GROQ_API_KEY", 
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHANNEL_ID"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
        
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration (hiding sensitive data)"""
        print("=== Financial Summary System Configuration ===")
        print(f"LLM Model: {cls.LITELLM_MODEL}")
        print(f"Output Directory: {cls.OUTPUT_DIR}")
        print(f"Search Hours Back: {cls.SEARCH_HOURS_BACK}")
        print(f"Max News Items: {cls.MAX_NEWS_ITEMS}")
        print(f"Max Summary Words: {cls.MAX_SUMMARY_WORDS}")
        print(f"Target Languages: {', '.join(cls.TARGET_LANGUAGES)}")
        print(f"Serper API Key: {'✓ Set' if cls.SERPER_API_KEY else '✗ Missing'}")
        print(f"Groq API Key: {'✓ Set' if cls.GROQ_API_KEY else '✗ Missing'}")
        print(f"Telegram Bot Token: {'✓ Set' if cls.TELEGRAM_BOT_TOKEN else '✗ Missing'}")
        print(f"Telegram Channel ID: {'✓ Set' if cls.TELEGRAM_CHANNEL_ID else '✗ Missing'}")
        print("===============================================")

# Create a global config instance
config = Config()

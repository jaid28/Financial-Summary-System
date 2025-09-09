import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio
import requests
from dataclasses import dataclass
from pathlib import Path

# CrewAI imports
from crewai import Agent, Task, Crew, Flow
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool, tool
from litellm import completion
from pydantic import BaseModel, Field

# Additional imports for PDF generation and image handling
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import requests
from PIL import Image
import io

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('financial_summary.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
@dataclass
class Config:
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY") 
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHANNEL_ID: str = os.getenv("TELEGRAM_CHANNEL_ID")
    LITELLM_MODEL: str = "groq/llama3-8b-8192"  # Free tier model
    OUTPUT_DIR: str = "output"

config = Config()

# Pydantic models for structured data
class NewsItem(BaseModel):
    title: str = Field(description="News article title")
    summary: str = Field(description="Brief summary of the article")
    url: str = Field(description="Article URL")
    timestamp: str = Field(description="Publication timestamp")
    relevance_score: float = Field(description="Relevance score 0-1")

class MarketSummary(BaseModel):
    summary_text: str = Field(description="Market summary text")
    key_points: List[str] = Field(description="Key market points")
    charts_urls: List[str] = Field(description="URLs of relevant charts/images")
    language: str = Field(description="Language of the summary")

class FormattedReport(BaseModel):
    content: str = Field(description="Formatted report content with image placeholders")
    image_urls: List[str] = Field(description="List of image URLs to include")
    chart_descriptions: List[str] = Field(description="Descriptions of where to place charts")

# Custom Tools
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
            "num": 20,
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
            model="groq/llama3-8b-8192",
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
            "parse_mode": "HTML"
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

# PDF Generation Tool
def create_pdf_report(content: str, image_urls: List[str], language: str, output_path: str):
    """Create PDF report with images"""
    try:
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        title = f"Financial Market Summary - {datetime.now().strftime('%Y-%m-%d')} ({language})"
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Content
        for paragraph in content.split('\n\n'):
            if paragraph.strip():
                story.append(Paragraph(paragraph, styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Add images
        for i, img_url in enumerate(image_urls[:2]):
            try:
                response = requests.get(img_url, timeout=10)
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content))
                    img_path = f"temp_chart_{i}.png"
                    img.save(img_path)
                    
                    # Add image to PDF
                    story.append(Spacer(1, 12))
                    story.append(RLImage(img_path, width=400, height=300))
                    story.append(Spacer(1, 12))
                    
                    # Clean up temp file
                    os.remove(img_path)
            except Exception as e:
                logger.error(f"Error adding image to PDF: {e}")
        
        doc.build(story)
        logger.info(f"PDF report created: {output_path}")
        
    except Exception as e:
        logger.error(f"Error creating PDF report: {e}")

# CrewAI Agents
def create_search_agent():
    return Agent(
        role="Financial News Search Specialist",
        goal="Search and collect the most relevant financial news from the past hour after US market close",
        backstory="""You are an expert at finding breaking financial news and market updates. 
        You specialize in identifying the most impactful stories that traders and investors need to know about.""",
        tools=[search_financial_news, get_groq_analysis],
        verbose=True,
        allow_delegation=False
    )

def create_summary_agent():
    return Agent(
        role="Financial Market Analyst",
        goal="Create concise, informative summaries of financial market activity and news",
        backstory="""You are a seasoned financial analyst with expertise in distilling complex market information 
        into clear, actionable insights. You focus on what matters most to traders and investors.""",
        verbose=True,
        allow_delegation=False
    )

def create_formatting_agent():
    return Agent(
        role="Content Formatting Specialist", 
        goal="Format financial summaries with relevant charts and visual elements",
        backstory="""You are an expert at creating visually appealing financial reports. 
        You know how to find and integrate relevant charts and images that support the narrative.""",
        tools=[find_financial_charts],
        verbose=True,
        allow_delegation=False
    )

def create_translation_agent():
    return Agent(
        role="Financial Content Translator",
        goal="Translate financial summaries while maintaining accuracy and format",
        backstory="""You are a professional translator specialized in financial content. 
        You ensure that complex financial terms are accurately translated while preserving meaning.""",
        verbose=True,
        allow_delegation=False
    )

def create_distribution_agent():
    return Agent(
        role="Content Distribution Manager",
        goal="Distribute financial summaries through various channels including Telegram",
        backstory="""You are responsible for ensuring that financial summaries reach their intended audience 
        through the most appropriate channels and formats.""",
        tools=[send_telegram_message],
        verbose=True,
        allow_delegation=False
    )

# CrewAI Flow Implementation
class FinancialSummaryFlow(Flow):
    def __init__(self):
        super().__init__()
        self.search_agent = create_search_agent()
        self.summary_agent = create_summary_agent()
        self.formatting_agent = create_formatting_agent()
        self.translation_agent = create_translation_agent()
        self.distribution_agent = create_distribution_agent()
        
        # Ensure output directory exists
        Path(config.OUTPUT_DIR).mkdir(exist_ok=True)

    @Flow.listen("start")
    def search_financial_news_flow(self):
        logger.info("Starting financial news search...")
        
        search_task = Task(
            description="""Search for the most important US financial market news from the past hour. 
            Focus on:
            1. Market closing updates
            2. Major stock movements  
            3. Economic indicators
            4. Corporate earnings
            5. Federal Reserve updates
            
            Use both Serper search and Groq analysis to get comprehensive coverage.
            Return structured data with relevance scores.""",
            agent=self.search_agent,
            expected_output="A comprehensive list of financial news items with summaries, URLs, and relevance scores"
        )
        
        return search_task

    @Flow.listen("search_financial_news_flow")
    def create_market_summary_flow(self, search_results):
        logger.info("Creating market summary...")
        
        summary_task = Task(
            description=f"""Based on the search results: {search_results}
            
            Create a concise market summary (under 500 words) that includes:
            1. Key market movements and closing prices
            2. Most significant news events
            3. Economic indicators or Fed updates
            4. Notable corporate developments
            5. Market outlook based on today's events
            
            Structure the summary with clear sections and highlight the most important information.""",
            agent=self.summary_agent,
            expected_output="A well-structured market summary under 500 words with key insights"
        )
        
        return summary_task

    @Flow.listen("create_market_summary_flow")
    def format_with_charts_flow(self, summary_content):
        logger.info("Formatting content with charts...")
        
        formatting_task = Task(
            description=f"""Take the market summary: {summary_content}
            
            1. Find 2 relevant financial charts/images that support the content
            2. Format the content for professional presentation
            3. Indicate where charts should be placed for maximum impact
            4. Ensure the layout is clean and readable
            
            Return formatted content with image URLs and placement instructions.""",
            agent=self.formatting_agent,
            expected_output="Formatted content with 2 relevant chart URLs and placement instructions"
        )
        
        return formatting_task

    @Flow.listen("format_with_charts_flow") 
    def translate_content_flow(self, formatted_content):
        logger.info("Translating content...")
        
        languages = ["Arabic", "Hindi", "Hebrew"]
        translations = {}
        
        for language in languages:
            translation_task = Task(
                description=f"""Translate the following financial summary to {language}: {formatted_content}
                
                Requirements:
                1. Maintain all financial terms accuracy
                2. Preserve formatting and structure
                3. Keep chart placement indicators
                4. Ensure cultural appropriateness for financial content
                
                Important: Keep all URLs and numerical data unchanged.""",
                agent=self.translation_agent,
                expected_output=f"Accurately translated financial summary in {language} with preserved formatting"
            )
            
            # Execute translation task
            crew = Crew(
                agents=[self.translation_agent],
                tasks=[translation_task],
                verbose=True
            )
            
            result = crew.kickoff()
            translations[language] = result
            
        return {"original": formatted_content, "translations": translations}

    @Flow.listen("translate_content_flow")
    def distribute_content_flow(self, all_content):
        logger.info("Distributing content...")
        
        # Generate PDFs for each language
        pdf_paths = []
        
        # Original English
        original_content = all_content["original"]
        
        # Extract image URLs (assuming they're in the content)
        import re
        image_urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\.(?:jpg|jpeg|png|gif)', str(original_content))
        
        # Create English PDF
        english_path = f"{config.OUTPUT_DIR}/financial_summary_english.pdf"
        create_pdf_report(str(original_content), image_urls, "English", english_path)
        pdf_paths.append(english_path)
        
        # Create PDFs for translations
        for language, content in all_content["translations"].items():
            pdf_path = f"{config.OUTPUT_DIR}/financial_summary_{language.lower()}.pdf"
            create_pdf_report(str(content), image_urls, language, pdf_path)
            pdf_paths.append(pdf_path)
        
        # Send to Telegram
        distribution_task = Task(
            description=f"""Distribute the financial summary to Telegram channel.
            
            Content to send: {original_content}
            
            1. Send the English summary first
            2. Include information about available translations
            3. Format for easy reading on mobile devices
            4. Include relevant hashtags for financial content
            
            Make the message engaging and informative.""",
            agent=self.distribution_agent,
            expected_output="Confirmation of successful distribution to Telegram channel"
        )
        
        crew = Crew(
            agents=[self.distribution_agent],
            tasks=[distribution_task],
            verbose=True
        )
        
        result = crew.kickoff()
        
        return {
            "distribution_result": result,
            "pdf_paths": pdf_paths,
            "telegram_sent": True
        }

# Main execution function
def main():
    """Main function to run the financial summary flow"""
    try:
        logger.info("Starting Financial Summary System...")
        
        # Validate environment variables
        required_vars = ["SERPER_API_KEY", "GROQ_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID"]
        missing_vars = [var for var in required_vars if not getattr(config, var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return
        
        # Initialize and run the flow
        flow = FinancialSummaryFlow()
        
        # Start the flow
        result = flow.kickoff()
        
        logger.info("Financial Summary System completed successfully!")
        logger.info(f"Results: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    # Set environment variables (replace with your actual keys)
    os.environ["SERPER_API_KEY"] = "your_serper_api_key"
    os.environ["GROQ_API_KEY"] = "your_groq_api_key" 
    os.environ["TELEGRAM_BOT_TOKEN"] = "your_telegram_bot_token"
    os.environ["TELEGRAM_CHANNEL_ID"] = "your_telegram_channel_id"
    
    main()
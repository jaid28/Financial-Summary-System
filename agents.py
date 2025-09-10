import logging
from crewai import Agent, Task, Crew, Flow
from tools import search_financial_news, get_groq_analysis, find_financial_charts, send_telegram_message
from utils import create_pdf_report, extract_image_urls_from_text
from config import config

logger = logging.getLogger(__name__)

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
            
            Create a concise market summary (under {config.MAX_SUMMARY_WORDS} words) that includes:
            1. Key market movements and closing prices
            2. Most significant news events
            3. Economic indicators or Fed updates
            4. Notable corporate developments
            5. Market outlook based on today's events
            
            Structure the summary with clear sections and highlight the most important information.""",
            agent=self.summary_agent,
            expected_output=f"A well-structured market summary under {config.MAX_SUMMARY_WORDS} words with key insights"
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
        
        translations = {}
        
        for language in config.TARGET_LANGUAGES:
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
        
        # Extract image URLs from content
        image_urls = extract_image_urls_from_text(original_content)
        
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

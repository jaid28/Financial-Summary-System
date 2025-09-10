# Financial-Summary-System
Financial News Summary System - Setup Guide
Overview
This CrewAI-based system automatically generates daily financial market summaries with charts and translations after US market close (01:30 IST).
Architecture
Agent Flow:

Search Agent - Gathers recent financial news using Serper API and Groq analysis
Summary Agent - Creates concise market summaries under 500 words
Formatting Agent - Finds relevant charts and formats content professionally
Translation Agent - Translates to Arabic, Hindi, and Hebrew
Distribution Agent - Sends to Telegram and generates PDF reports

Prerequisites
API Keys Required:

Serper API (for web search): https://serper.dev/

Groq API (free tier available): https://console.groq.com/

Telegram Bot Token: Create via @BotFather on Telegram

Telegram Channel ID: Your channel/group ID

System Requirements:
Python 3.8+
Internet connection
~2GB free space for dependencies

Installation
1. Clone/Download the Code
'''bash
## Create project directory
mkdir financial-summary-system
cd financial-summary-system

## Copy the main script as main.py

2. Install Dependencies
bashpip install -r requirements.txt

3. Environment Setup
Create a .env file in the project root:
env
## API Keys
SERPER_API_KEY=your_serper_api_key_here
GROQ_API_KEY=your_groq_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHANNEL_ID=your_telegram_channel_id_here

## Optional Configuration
LITELLM_MODEL=groq/llama3-8b-8192
OUTPUT_DIR=output

4. API Key Setup Guide
Serper API:
Visit https://serper.dev/
Sign up for free account
Copy API key from dashboard
Free tier: 2,500 requests/month

Groq API:
Visit https://console.groq.com/
Create account and verify email
Generate API key
Free tier available with good limits

Telegram Bot:
Message @BotFather on Telegram
Use /newbot command
Follow prompts to create bot
Save the bot token

Telegram Channel ID:
Create a Telegram channel
Add your bot as admin
Use @userinfobot to get channel ID
Channel ID format: -1001234567890

Usage
Basic Execution:
bashpython main.py
Scheduled Execution (Linux/Mac):
Add to crontab for daily execution at 1:30 AM IST:

'''bash
## Edit crontab
crontab -e
## Add this line (adjust path):
30 1 * * * /usr/bin/python3 /path/to/financial-summary-system/main.py
Windows Task Scheduler:

Open Task Scheduler
Create Basic Task
Set trigger to daily at 1:30 AM
Action: Start Program → python.exe
Arguments: path/to/main.py

Output Files
The system generates:

output/financial_summary_english.pdf
output/financial_summary_arabic.pdf
output/financial_summary_hindi.pdf
output/financial_summary_hebrew.pdf
financial_summary.log (execution logs)

Configuration Options
Model Selection:
python
## In config.py or environment
LITELLM_MODEL = "groq/llama3-8b-8192"  # Free
LITELLM_MODEL = "gpt-3.5-turbo"        # Paid
LITELLM_MODEL = "claude-3-haiku"       # Paid
Customizing Search:
python
## Modify search parameters in search_financial_news()
hours_back = 2  # Look back 2 hours instead of 1
num_results = 30  # Get more news items
Language Customization:
python
## In translate_content_flow()
languages = ["Spanish", "French", "German"]  # Change target languages
Troubleshooting
Common Issues:

Import Errors:
bashpip install --upgrade crewai crewai-tools

API Key Issues:
Verify API keys are correct
Check API quotas/limits
Ensure environment variables are loaded


Telegram Errors:
Bot must be admin of channel
Check channel ID format (-1001234567890)
Verify bot token


PDF Generation Issues:
bashpip install --upgrade reportlab Pillow

Memory Issues:
Reduce number of news items processed
Use lighter LLM model
Process translations sequentially

Debug Mode:
python
## Enable verbose logging
logging.basicConfig(level=logging.DEBUG)

## Test individual components
if __name__ == "__main__":
    # Test search only
    search_results = search_financial_news("US market close today", 1)
    print(search_results)

Monitoring and Maintenance
Log Files:
Check financial_summary.log for execution details
Monitor API usage and quotas
Set up alerts for failures

Performance Optimization:
Use caching for repeated searches
Optimize image processing
Implement retry logic for API calls

Updates:
Keep CrewAI updated: pip install --upgrade crewai
Monitor API changes
Update model versions as needed

Security Considerations

Store API keys securely
Use environment variables
Restrict Telegram bot permissions
Monitor API usage for unusual activity

Support and Extensions

Potential Enhancements:

Add YouTube video summaries
Include social media sentiment
Historical trend analysis
Mobile app integration
Email distribution
Multi-timezone support

Community Resources:

CrewAI GitHub: https://github.com/joaomdmoura/crewAI

CrewAI Documentation: https://docs.crewai.com/

LiteLLM Documentation: https://docs.litellm.ai/

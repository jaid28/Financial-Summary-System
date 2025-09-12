import os
import sys
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import config
from src.agents import FinancialSummaryFlow

# Setup logging
def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper()),
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'financial_summary.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main function to run the financial summary flow"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Financial Summary System...")
        
        # Validate configuration
        config.validate()
        config.print_config()
        
        # Ensure output directory exists
        Path(config.OUTPUT_DIR).mkdir(exist_ok=True)
        
        # Initialize and run the flow
        logger.info("Initializing CrewAI Flow...")
        flow = FinancialSummaryFlow()
        
        # Start the flow
        logger.info("Starting flow execution...")
        result = flow.kickoff()
        
        logger.info("Financial Summary System completed successfully!")
        logger.info(f"Results: {result}")
        
        return result
        
    except ValueError as ve:
        logger.error(f"Configuration error: {ve}")
        print(f"\n❌ Configuration Error: {ve}")
        print("Please check your .env file and ensure all required API keys are set.")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
        print(f"\n❌ System Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_logging()
    main()

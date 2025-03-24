import asyncio
from loguru import logger
from src.config import settings
from src.services.deepseek_service import DeepseekClient


async def daily_report():
    try:
        logger.info("Initializing DeepseekClient...")
        client = DeepseekClient()
        logger.info("Getting domestic news from Deepseek...")
        domestic = await client.get_domestic_news()
        logger.success("Successfully fetched domestic news.")
        
        logger.info("Saving domestic report...")
        client.save_report(domestic, "domestic")
        logger.success("Successfully saved domestic report.")
        
    except Exception as e:
        logger.error(f"Failed to generate daily reports: {str(e)}")
        raise  # Re-raise the exception to see the full traceback


if __name__ == "__main__":
    try:
        logger.info("Starting daily report task...")
        asyncio.run(daily_report())
        logger.success("Daily report task completed successfully.")
    except Exception as e:
        logger.critical(f"Critical error in main execution: {str(e)}")
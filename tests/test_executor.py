import asyncio
from playwright.async_api import async_playwright
from src.agent.web.browser.interaction.executor import CommandExecutor
from src.agent.llm.gemini_client import GeminiAgent
from src.agent.utils.logging_config import setup_logging
import os
from dotenv import load_dotenv

async def test_executor():
    """Test the command executor with browser automation."""
    # Set up logging
    logger = setup_logging()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize Gemini agent
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    agent = GeminiAgent(api_key)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Create executor
        executor = CommandExecutor(page, agent)
        
        try:
            # Test command
            command = "go to google.com and search for python tutorials"
            logger.info(f"Executing command: {command}")
            
            result = await executor.execute_command(command)
            logger.info(f"Execution result: {result}")
            
        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_executor()) 
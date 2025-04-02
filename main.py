from playwright.async_api import async_playwright
from src.agent.web.browser.config import BrowserConfig
from src.agent.web.browser.browser import Browser
import asyncio
import os
from dotenv import load_dotenv
from src.agent.utils.logging_config import setup_logging
from src.agent.llm.gemini_client import GeminiAgent




async def test_google_search(browser):

    logger = setup_logging()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize Gemini agent
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
    agent = GeminiAgent(api_key)
        
        # Test cases
    test_commands = [
        # "go to youtube and search for python projects and Wait for results to load and click on 2nd result",
        "go to duckduckgo and search for cars in images and open 2nd image",
        # "login to github.com with username 'test' and password 'test123'",
        # "go to amazon.com and search for headphones",
        # "go to github and search for python projects. Open 3rd one !"
    ]
    
    for command in test_commands:
            logger.info(f"\nTesting command: {command}")
            try:
                await browser.interact(command)
                # plan = await agent.plan_actions(command)
                # if plan:
                #     logger.info("Successfully generated plan:")
                #     logger.info(f"Description: {plan.get('plan_description')}")
                #     logger.info("\nSteps:")
                #     for step in plan.get('steps', []):
                #         logger.info(f"\nStep {step.get('step_number')}:")
                #         logger.info(f"Description: {step.get('description')}")
                #         logger.info(f"Action: {step.get('action')}")
                # else:
                #     logger.warning("Failed to generate plan")
            except Exception as e:
                logger.error(f"Error: {str(e)}")


async def main():
    """Main entry point for testing the browser interaction."""
    config = BrowserConfig()
    
    # Initialize the Gemini agent with API key
    agent = GeminiAgent(api_key=os.getenv('GOOGLE_GEMINI_API_KEY'))
    
    async with async_playwright() as p:
        browser_type = getattr(p, config.browser_type)
        playwright_browser = await browser_type.launch(**config.browser_launch_options)
        context = await playwright_browser.new_context(**config.context_options)
        page = await context.new_page()
        
        # Create our browser controller with Gemini agent
        browser = Browser(playwright_browser, context, page, config, agent)
        
        try:
            print("\n=== Testing  ===")
            await test_google_search(browser)
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        
        finally:
            print("\nClosing browser...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())


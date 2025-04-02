import asyncio
from src.agent.llm.gemini_client import GeminiAgent
from src.agent.utils.logging_config import setup_logging
import os
from dotenv import load_dotenv

async def test_llm():
    """Test basic LLM functionality"""
    # Set up logging
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
        "go to google.com and search for python tutorials",
        "login to github.com with username 'test' and password 'test123'",
        "go to amazon.com and search for headphones",
        "go to github and search for python projects. Open 3rd one !"
    ]
    
    for command in test_commands:
        logger.info(f"\nTesting command: {command}")
        try:
            plan = await agent.plan_actions(command)
            if plan:
                logger.info("Successfully generated plan:")
                logger.info(f"Description: {plan.get('plan_description')}")
                logger.info("\nSteps:")
                for step in plan.get('steps', []):
                    logger.info(f"\nStep {step.get('step_number')}:")
                    logger.info(f"Description: {step.get('description')}")
                    logger.info(f"Action: {step.get('action')}")
            else:
                logger.warning("Failed to generate plan")
        except Exception as e:
            logger.error(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_llm()) 
from playwright.async_api import Page, Browser as PlaywrightBrowser, BrowserContext
from typing import Optional, Dict
from .config import BrowserConfig
from .interaction.errors import BrowserError
from .interaction.parser import CommandParser
from .interaction.element_finder import ElementFinder
from .interaction.executor import CommandExecutor
import re
import random
import asyncio
import logging

logger = logging.getLogger("ai-browser-agent")

class Browser:
    """Main browser controller class."""
    
    def __init__(self, 
                 browser: PlaywrightBrowser, 
                 context: BrowserContext, 
                 page: Page, 
                 config: BrowserConfig,
                 agent):
        self.browser = browser
        self.context = context
        self.page = page
        self.config = config
        self._current_url: Optional[str] = None
        self.parser = CommandParser()
        self.element_finder = ElementFinder(agent)
        self.executor = CommandExecutor()
        self.agent = agent
        
        # Setup popup and dialog handling
        asyncio.create_task(self._setup_popup_handling())

    async def _add_human_delay(self, min_ms=100, max_ms=300):
        """Add random delay to simulate human behavior."""
        delay = random.randint(min_ms, max_ms)
        await self.page.wait_for_timeout(delay)

    async def _setup_popup_handling(self):
        """Setup handlers for popups and dialogs."""
        # Handle new popup windows
        self.page.on("popup", lambda popup: popup.close())
        
        # Auto-dismiss dialogs (alert, confirm, prompt)
        self.page.on("dialog", lambda dialog: dialog.dismiss())
        
        # Setup route to block unwanted resources
        await self.page.route("**/*", self._handle_route)

    async def _handle_route(self, route):
        """Handle network requests and block unwanted resources."""
        request = route.request
        resource_type = request.resource_type
        
        # Block known ad/tracking domains
        blocked_domains = [
            "google-analytics.com",
            "doubleclick.net",
            "facebook.com",
            "adnxs.com",
            # Add more ad domains as needed
        ]
        
        # Block unwanted resource types
        blocked_resources = [
            "image",  # Optional: block images to speed up browsing
            "media",
            "font",
            "other"
        ]
        
        url = request.url.lower()
        
        if any(domain in url for domain in blocked_domains):
            await route.abort()
        elif resource_type in blocked_resources:
            await route.abort()
        else:
            await route.continue_()

    async def _handle_cookie_banners(self):
        """Attempt to handle common cookie consent banners."""
        cookie_button_selectors = [
            '[id*="cookie"] button',
            '[class*="cookie"] button',
            '[id*="consent"] button',
            '[class*="consent"] button',
            'button[contains(text(), "Accept")]',
            'button[contains(text(), "I agree")]',
            'button[contains(text(), "Got it")]',
            # Reddit specific
            '#accept-all-cookies',
            '[data-testid="accept-all-cookies"]',
            'button:has-text("Accept all")',
        ]
        
        for selector in cookie_button_selectors:
            try:
                await self.page.click(selector, timeout=1000)
                await self._add_human_delay()
            except:
                continue

    async def interact(self, command: str) -> dict:
        """Execute a natural language command using LLM guidance"""
        try:
            # Get current page content
            page_content = await self.page.content()
            
            # Get structured plan from LLM
            logger.info(f"\nProcessing command: {command}")
            plan = await self.agent.plan_actions(command, page_content)
            
            if not plan or not plan.get("steps"):
                return {
                    "success": False,
                    "message": "Failed to generate action plan",
                    "error_type": "PlanningError"
                }
            
            # Parse plan into executable actions
            actions = self.parser.parse_plan(plan)
            logger.info(f"Parsed actions: {actions}")
            
            # Execute each action
            for action in actions:
                logger.info(f"Executing action: {action}")
                # Handle cookie banners and popups before each action
                await self._handle_cookie_banners()
                result = await self.executor.execute_action(self.page, action)
                logger.info(f"Action result: {result}")
                
                if not result["success"]:
                    logger.error(f"Action failed: {result['message']}")
                    return result
                    
                logger.info(f"Successfully executed action: {action['action']}")
                await self._add_human_delay()
            
            return {
                "success": True,
                "message": "Command executed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error during interaction: {e}")
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}",
                "error_type": "UnexpectedError"
            }

    async def _execute_action(self, action: Dict) -> Dict:
        """Execute a single browser action"""
        try:
            action_type = action["action"]
            
            if action_type == "goto":
                response = await self.page.goto(
                    action["url"],
                    wait_until="networkidle",
                    timeout=30000
                )
                await self._handle_cookie_banners()
                return {"success": bool(response and response.status < 400)}
                
            elif action_type == "click":
                await self.page.click(action["selector"])
                return {"success": True}
                
            elif action_type == "fill":
                await self.page.fill(action["selector"], action["text"])
                return {"success": True}
                
            elif action_type == "wait":
                await self.page.wait_for_timeout(action["seconds"] * 1000)
                return {"success": True}
                
            elif action_type == "submit":
                await self.page.click(action["selector"])
                await self.page.wait_for_load_state("networkidle")
                return {"success": True}
                
            elif action_type == "dismiss_popup":
                await self._handle_cookie_banners()
                return {"success": True}
                
            return {
                "success": False,
                "message": f"Unknown action type: {action_type}",
                "error_type": "UnknownAction"
            }
            
        except Exception as e:
            logger.error(f"Action failed: {e}")
            return {
                "success": False,
                "message": f"Action failed: {str(e)}",
                "error_type": "ActionError"
            }

    async def close(self):
        """Close the browser and all its resources."""
        await self.browser.close()

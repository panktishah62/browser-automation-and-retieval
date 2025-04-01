from typing import Protocol, Dict, Any
from playwright.async_api import Page
from .errors import AuthenticationError

class Command(Protocol):
    """Protocol for browser commands."""
    async def execute(self, page: Page, **kwargs) -> Dict[str, Any]:
        pass

class NavigateCommand:
    async def execute(self, page: Page, url: str) -> Dict[str, Any]:
        await page.goto(url)
        return {"current_url": page.url}

class ClickCommand:
    async def execute(self, page: Page, selector: str) -> Dict[str, Any]:
        await page.click(selector)
        return {"clicked": selector}

class TypeCommand:
    async def execute(self, page: Page, selector: str, text: str) -> Dict[str, Any]:
        await page.fill(selector, text)
        return {"typed": text, "into": selector}

class WaitForCommand:
    async def execute(self, page: Page, selector: str) -> Dict[str, Any]:
        await page.wait_for_selector(selector)
        return {"waited_for": selector}

class LoginCommand:
    async def execute(self, page: Page, username: str, password: str, site: str = None) -> Dict[str, Any]:
        try:
            # Handle different login forms based on the site
            if site == "github":
                await page.fill('input[name="login"]', username)
                await page.fill('input[name="password"]', password)
                await page.click('input[type="submit"]')
            elif site == "google":
                # Handle Google's two-step login process
                await page.fill('input[type="email"]', username)
                await page.click('#identifierNext')
                await page.wait_for_selector('input[type="password"]')
                await page.fill('input[type="password"]', password)
                await page.click('#passwordNext')
            else:
                # Generic login form handling
                await page.fill('input[type="text"], input[type="email"], input[name="username"], input[name="login"]', username)
                await page.fill('input[type="password"]', password)
                await page.click('button[type="submit"], input[type="submit"]')

            # Wait for navigation or error message
            try:
                # Wait for either success or error indicators
                await page.wait_for_load_state('networkidle')
                
                # Check for common error messages
                error_selectors = [
                    '.error-message',
                    '#error-message',
                    '.alert-error',
                    '[role="alert"]'
                ]
                
                for selector in error_selectors:
                    error_element = await page.query_selector(selector)
                    if error_element:
                        error_text = await error_element.text_content()
                        if error_text and any(keyword in error_text.lower() 
                                            for keyword in ['invalid', 'incorrect', 'failed', 'error']):
                            raise AuthenticationError(f"Login failed: {error_text}")

                return {
                    "status": "success",
                    "message": "Login successful",
                    "current_url": page.url
                }

            except AuthenticationError as e:
                raise e
            except Exception as e:
                raise AuthenticationError(f"Login verification failed: {str(e)}")

        except Exception as e:
            raise AuthenticationError(f"Login failed: {str(e)}") 
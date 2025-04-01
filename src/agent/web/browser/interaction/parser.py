from typing import Dict, Any, Tuple, List
import re
from .commands import NavigateCommand, ClickCommand, TypeCommand, WaitForCommand, LoginCommand
from .errors import BrowserError

class CommandParser:
    """Parses natural language commands into executable browser commands."""

    def parse(self, command: str) -> Tuple[Any, Dict[str, Any]]:
        """
        Parse a natural language command and return the appropriate command object
        and its parameters.
        """
        command = command.lower().strip()
        
        # Login command patterns
        login_patterns = [
            r"login (?:to |on |at )?(?P<site>[\w.]+) (?:with |using )?username ['\"](?P<username>.*?)['\"] (?:and |with )?password ['\"](?P<password>.*?)['\"]",
            r"sign in (?:to |on |at )?(?P<site>[\w.]+) (?:with |using )?username ['\"](?P<username>.*?)['\"] (?:and |with )?password ['\"](?P<password>.*?)['\"]"
        ]
        
        for pattern in login_patterns:
            match = re.match(pattern, command)
            if match:
                data = match.groupdict()
                return LoginCommand(), {
                    "username": data["username"],
                    "password": data["password"],
                    "site": data["site"].replace(".com", "")
                }
        
        # Navigation commands
        if command.startswith("go to "):
            url = command[6:].strip()
            # Add https if no protocol specified
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"
            return NavigateCommand(), {"url": url}
        
        # Type commands
        elif "type" in command and "into" in command:
            match = re.search(r"type ['\"](.*?)['\"] into (.*)", command)
            if match:
                text, selector = match.groups()
                selector = self._get_selector_for_input(selector)
                return TypeCommand(), {"selector": selector, "text": text}
        
        # Click commands
        elif command.startswith("click"):
            element = command[6:].strip()
            selector = self._get_selector_for_element(element)
            return ClickCommand(), {"selector": selector}
        
        # Wait commands
        elif command.startswith("wait for"):
            element = command[9:].strip()
            selector = self._get_selector_for_element(element)
            return WaitForCommand(), {"selector": selector}
        
        raise BrowserError(f"Could not parse command: {command}")

    def _get_selector_for_input(self, description: str) -> str:
        """Convert input description to a CSS selector."""
        description = description.lower()
        
        # Common input field patterns
        selectors = {
            "search box": "input[type='search'], input[name*='search'], input[placeholder*='search']",
            "username": "input[type='text'][name*='user'], input[name='username'], input[placeholder*='username']",
            "password": "input[type='password']",
            "email": "input[type='email']"
        }
        
        for key, selector in selectors.items():
            if key in description:
                return selector
                
        # Default to looking for input with matching attributes
        return f"input[placeholder*='{description}'], input[name*='{description}'], input[aria-label*='{description}']"

    def _get_selector_for_element(self, description: str) -> str:
        """Convert element description to a CSS selector."""
        description = description.lower()
        
        # Common element patterns
        selectors = {
            "search button": "button[type='submit'], button:has-text('Search')",
            "search results": "#search-results, .search-results, [aria-label='Search results']",
            "login button": "button:has-text('Login'), button:has-text('Sign in')",
            "submit button": "button[type='submit']"
        }
        
        for key, selector in selectors.items():
            if key in description:
                return selector
        
        # Default to looking for elements with matching text or attributes
        return f"text={description}, [aria-label*='{description}'], [name*='{description}']"

    def parse_plan(self, plan: Dict) -> List[Dict]:
        """Convert LLM plan into executable browser actions"""
        browser_actions = []
        
        for step in plan.get("steps", []):
            action_type = step["action_type"]
            details = step["details"]
            
            if action_type == "navigation":
                browser_actions.append({
                    "action": "goto",
                    "url": details["url"]
                })
                
            elif action_type == "click":
                # Try each selector in order
                for selector in details["selectors"]:
                    browser_actions.append({
                        "action": "click",
                        "selector": selector
                    })
                    
            elif action_type == "input":
                browser_actions.append({
                    "action": "fill",
                    "selector": details["selectors"][0],  # Use first selector
                    "text": details["text"]
                })
                
            elif action_type == "wait":
                browser_actions.append({
                    "action": "wait",
                    "seconds": details.get("seconds", 1)
                })
                
            elif action_type == "verify":
                browser_actions.append({
                    "action": "verify",
                    "selectors": details["selectors"]
                })
        
        return browser_actions 
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

    def _get_selector_for_input(self, description: str) -> List[str]:
        """Get a list of possible selectors for an input field."""
        description = description.lower()
        
        # Common input field patterns
        selectors = {
            "search": [
                "input[name='q']",
                "input[title='Search']",
                "input[type='search']",
                "input[aria-label*='search' i]",
                "textarea[name='q']",
                "textarea[aria-label*='search' i]"
            ],
            "username": [
                "input[type='text'][name*='user' i]",
                "input[name='username']",
                "input[id*='username' i]"
            ],
            "password": [
                "input[type='password']",
                "input[name*='pass' i]",
                "input[id*='password' i]"
            ]
        }
        
        for key, selector_list in selectors.items():
            if key in description:
                return selector_list
                
        return [f"input[placeholder*='{description}' i]", f"input[aria-label*='{description}' i]"]

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
            action = step["action"]
            action_type = action["type"]
            details = {
                "action": action_type,
                "target": action["target"],
                "value": action.get("value", ""),
                "selectors": action.get("selectors", [])
            }
            browser_actions.append(details)
        
        return browser_actions 
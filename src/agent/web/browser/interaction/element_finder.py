from typing import Dict, List
import logging

logger = logging.getLogger("ai-browser-agent")

class ElementFinder:
    """Uses LLM to identify page elements and plan actions."""
    
    def __init__(self, agent):
        self.agent = agent

    async def find_elements(self, url: str, intent: str) -> Dict:
        """Get element selectors and actions for the given intent."""
        try:
            # Get action plan from the agent
            actions = await self.agent.plan_actions(intent)
            
            # Convert action plan to expected format
            return {
                "actions": actions,
                "verification": {
                    "success_indicators": [
                        ".repo-list-item",
                        ".search-results",
                        "[data-testid='results-list']"
                    ],
                    "timeout_ms": 5000
                }
            }
            
        except Exception as e:
            logger.error(f"Error finding elements: {e}")
            return {
                "actions": [],
                "verification": {
                    "success_indicators": [],
                    "timeout_ms": 5000
                }
            } 
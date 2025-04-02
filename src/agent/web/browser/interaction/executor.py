from typing import Dict, List
import logging
from playwright.async_api import TimeoutError, Page
from dotenv import load_dotenv
import os

logger = logging.getLogger("ai-browser-agent")

class CommandExecutor:
    """Executes browser commands based on LLM-provided strategies"""
    
    def __init__(self):
        load_dotenv()  # Load environment variables

    def _resolve_env_value(self, value: str) -> str:
        """Resolve value from environment variables if needed"""
        if isinstance(value, str) and value.startswith("ENV:"):
            env_var = value.split("ENV:")[1]
            return os.getenv(env_var, "")
        return value

    async def execute_action(self, page: Page, action: Dict) -> Dict:
        """Execute a single browser action"""
        try:
            action_type = action["action"]
            
            # Resolve any ENV variables in the value
            if "value" in action:
                action["value"] = self._resolve_env_value(action["value"])
            
            if action_type == "navigation":
                logger.info(f"Navigating to: {action['value']}")
                response = await page.goto(
                    action["value"],
                    # wait_until="networkidle",
                    timeout=60000
                )
                # Wait for page to be ready
                await page.wait_for_load_state("domcontentloaded")
                success = bool(response and response.status < 400)
                logger.info(f"Navigation {'successful' if success else 'failed'}")
                return {"success": success}
                
            elif action_type == "click":
                for selector in action["selectors"]:
                    try:
                        logger.info(f"Attempting to click: {selector}")
                        element = await page.wait_for_selector(
                            selector,
                            state="visible",
                            timeout=10000
                        )
                        if element:
                            await element.click()
                            logger.info(f"Successfully clicked: {selector}")
                            return {"success": True}
                    except Exception as e:
                        logger.error(f"Click action failed for selector {selector}: {e}")
                        continue
                return {"success": False, "message": "Click action failed for all selectors"}
                
            elif action_type == "type":
                for selector in action["selectors"]:
                    try:
                        logger.info(f"Attempting to type into: {selector}")
                        element = await page.wait_for_selector(
                            selector,
                            state="visible",
                            timeout=10000
                        )
                        if element:
                            await element.fill(action["value"])
                            logger.info(f"Successfully typed into: {selector}")
                            return {"success": True}
                    except Exception as e:
                        logger.error(f"Type action failed for selector {selector}: {e}")
                        continue
                return {"success": False, "message": "Type action failed for all selectors"}
                
            elif action_type == "wait":
                if action.get("selectors"):
                    logger.info(f"Waiting for selectors: {action['selectors']}")
                    for selector in action["selectors"]:
                        try:
                            await page.wait_for_selector(
                                selector,
                                state="visible",
                                timeout=int(action["value"])
                            )
                            logger.info(f"Successfully found selector: {selector}")
                            return {"success": True}
                        except TimeoutError:
                            logger.warning(f"Timeout waiting for selector: {selector}")
                            continue
                    return {"success": False, "message": "Wait condition not met"}
                else:
                    logger.info(f"Waiting for {action['value']}ms")
                    await page.wait_for_timeout(int(action["value"]) * 1000)
                    logger.info("Wait completed")
                    return {"success": True}
                
            elif action_type == "submit":
                # Try different submit strategies
                try:
                    # First try to submit using Enter key on active element
                    await page.keyboard.press('Enter')
                    await page.wait_for_load_state("networkidle")
                    return {"success": True}
                except Exception:
                    # If Enter key doesn't work, try clicking submit buttons/forms
                    for selector in action["selectors"]:
                        try:
                            element = await page.wait_for_selector(
                                selector,
                                state="visible",
                                timeout=10000
                            )
                            if element:
                                await element.click()
                                await page.wait_for_load_state("networkidle")
                                return {"success": True}
                        except Exception as e:
                            logger.error(f"Submit action failed for selector {selector}: {e}")
                            continue
                return {"success": False, "message": "Submit action failed"}
                
            elif action_type == "press":
                try:
                    key = action["value"]
                    await page.keyboard.press(key)
                    # await page.wait_for_load_state("networkidle")
                    logger.info(f"Successfully pressed key: {key}")
                    return {"success": True}
                except Exception as e:
                    logger.error(f"Press action failed: {e}")
                    return {"success": False, "message": f"Press action failed: {str(e)}"}
                
            return {
                "success": False,
                "message": f"Unknown action type: {action_type}",
                "error_type": "UnknownAction"
            }
            
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {
                "success": False,
                "message": f"Action failed: {str(e)}",
                "error_type": "ActionError"
            }

    async def execute_plan(self, page, plan: Dict) -> Dict:
        """Execute a complete plan of actions"""
        try:
            for step in plan.get("steps", []):
                action_type = step["action_type"]
                details = step["details"]
                
                # Convert step to action format
                action = {
                    "action": action_type,
                    **details
                }
                
                result = await self.execute_action(page, action)
                if not result["success"]:
                    return result
                
            return {
                "success": True,
                "message": "Plan executed successfully"
            }
            
        except Exception as e:
            logger.error(f"Plan execution failed: {e}")
            return {
                "success": False,
                "message": f"Plan execution failed: {str(e)}",
                "error_type": "PlanError"
            }

    async def execute(self, page, command_data: Dict) -> Dict:
        """Execute a series of actions based on LLM guidance."""
        try:
            # Execute each action in sequence
            for action in command_data["actions"]:
                await self._execute_action(page, action, command_data["selectors"])

            # Verify success
            success = await self._verify_success(page, command_data["verification"])
            
            return {
                "success": success,
                "message": "Command executed successfully" if success else "Command execution failed"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error executing command: {str(e)}"
            }

    async def _execute_action(self, page, action: Dict, selectors: List[Dict]):
        """Execute a single action using multiple selector attempts."""
        element_selectors = self._get_selectors_for_element(selectors, action["element"])
        
        for selector in element_selectors:
            try:
                if action["type"] == "click":
                    await page.click(selector)
                    break
                elif action["type"] == "type":
                    await page.fill(selector, action["value"])
                    break
                elif action["type"] == "press":
                    await page.keyboard.press(action["key"])
                    break
            except:
                continue

    async def _verify_success(self, page, verification: Dict) -> bool:
        """Verify the command executed successfully."""
        for selector in verification["success_indicators"]:
            try:
                await page.wait_for_selector(selector, timeout=verification["timeout_ms"])
                return True
            except:
                continue
        return False

    def _get_selectors_for_element(self, selectors: List[Dict], element_name: str) -> List[str]:
        """Get all selectors for a given element."""
        for selector_group in selectors:
            if selector_group["element"] == element_name:
                return selector_group["selectors"]
        return [] 
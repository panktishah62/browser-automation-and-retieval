from typing import Dict, List
import logging

logger = logging.getLogger("ai-browser-agent")

class CommandExecutor:
    """Executes browser commands based on LLM-provided strategies"""
    
    async def execute_action(self, page, action: Dict) -> Dict:
        """Execute a single browser action"""
        try:
            action_type = action["action"]
            
            if action_type == "goto":
                response = await page.goto(
                    action["url"],
                    wait_until="networkidle",
                    timeout=30000
                )
                return {"success": bool(response and response.status < 400)}
                
            elif action_type == "click":
                await page.click(action["selector"])
                return {"success": True}
                
            elif action_type == "fill":
                await page.fill(action["selector"], action["text"])
                return {"success": True}
                
            elif action_type == "wait":
                await page.wait_for_timeout(action["seconds"] * 1000)
                return {"success": True}
                
            elif action_type == "submit":
                await page.click(action["selector"])
                await page.wait_for_load_state("networkidle")
                return {"success": True}
                
            elif action_type == "verify":
                try:
                    for selector in action["selectors"]:
                        await page.wait_for_selector(selector, timeout=5000)
                        return {"success": True}
                except:
                    return {"success": False, "message": "Verification failed"}
                
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
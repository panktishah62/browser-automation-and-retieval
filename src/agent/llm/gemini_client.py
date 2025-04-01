from google.generativeai import GenerativeModel
import google.generativeai as genai
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("ai-browser-agent")

class GeminiAgent:
    """Agent that uses Gemini to plan browser actions based on user commands"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = GenerativeModel('gemini-1.5-flash')
        self.generation_config = {
            "temperature": 0.2,  # Slightly higher for more descriptive plans
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }

    async def plan_actions(self, user_command: str, page_content: Optional[str] = None) -> Dict:
        """Generate a structured plan from natural language command"""
        context = ""
        if page_content:
            if len(page_content) > 8000:
                page_content = page_content[:8000] + "... (content truncated)"
            context = f"\nCurrent page content: {page_content}\n"
            
        prompt = f"""As a browser automation expert, break down this task into clear steps:

        USER COMMAND: "{user_command}"
        {context}

        Create a detailed step-by-step plan that a browser automation system can follow.
        Return the plan in this exact JSON format:

        {{
            "plan_description": "Brief description of what we're going to do",
            "steps": [
                {{
                    "step_number": 1,
                    "description": "Human readable description of what this step does",
                    "action": {{
                        "type": "navigation|click|type|wait|submit",
                        "target": "What we're interacting with",
                        "value": "Any value needed (e.g. URL, text to type)",
                        "selectors": ["CSS selectors to find the element"]
                    }}
                }}
            ]
        }}

        Example for "go to github and search for python projects":
        {{
            "plan_description": "Navigate to GitHub and perform a search for Python projects",
            "steps": [
                {{
                    "step_number": 1,
                    "description": "Navigate to GitHub homepage",
                    "action": {{
                        "type": "navigation",
                        "target": "GitHub homepage",
                        "value": "https://github.com",
                        "selectors": []
                    }}
                }},
                {{
                    "step_number": 2,
                    "description": "Click the search box to activate it",
                    "action": {{
                        "type": "click",
                        "target": "search box",
                        "value": "",
                        "selectors": ["[data-target='qbsearch-input.inputButton']", "[name='q']"]
                    }}
                }},
                {{
                    "step_number": 3,
                    "description": "Type search query",
                    "action": {{
                        "type": "type",
                        "target": "search input",
                        "value": "python projects",
                        "selectors": ["input[name='q']", "#query-builder-test"]
                    }}
                }},
                {{
                    "step_number": 4,
                    "description": "Submit search",
                    "action": {{
                        "type": "submit",
                        "target": "search form",
                        "value": "",
                        "selectors": ["[type='submit']", ".header-search-button"]
                    }}
                }}
            ]
        }}

        Provide a complete plan with all necessary steps to accomplish: {user_command}
        """

        try:
            logger.info(f"Generating plan for command: {user_command}")
            response = await self.model.generate_content_async(
                prompt,
                generation_config=self.generation_config
            )
            logger.info(f"Raw LLM response:\n{response}")
            
            # Extract and clean the response
            content = response.text.strip()
            logger.debug(f"Raw LLM response:\n{content}")
            
            # Parse the plan
            plan = self._extract_json_from_text(content)
            logger.info(f"Generated plan:\n{json.dumps(plan, indent=2)}")
            
            if not plan.get("steps"):
                logger.warning("No steps found in generated plan")
                return None
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            logger.exception("Full exception:")
            return None

    def _extract_json_from_text(self, text: str) -> Dict:
        """Extract JSON from text response"""
        try:
            # Clean up the text
            text = text.replace('\n', ' ').replace('```json', '').replace('```', '')
            text = text.strip('` \n"')
            
            # Try to parse as JSON
            data = json.loads(text)
            if isinstance(data, dict):
                return data
            elif isinstance(data, list):
                # Convert old format to new format
                return {
                    "steps": [{"action_type": "action", "details": action} for action in data],
                    "success_criteria": [],
                    "fallback_strategies": []
                }
            else:
                return {"steps": [], "success_criteria": [], "fallback_strategies": []}
            
        except json.JSONDecodeError:
            # Try to extract JSON object from text
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    return {"steps": [], "success_criteria": [], "fallback_strategies": []}
            return {"steps": [], "success_criteria": [], "fallback_strategies": []} 
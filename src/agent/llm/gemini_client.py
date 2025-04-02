import re
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

        For each step, if a selector is required, the system should first search the DOM using a combination of tag names, attributes, and text content before proceeding. 
        Ensure the automation system logs each step and selector it identifies. 
        Return the plan in this exact JSON format. Make sure the JSON format is correct and doesn't contain extra text, formatting issues, or broken syntax.
        
        Example for "login to github":
        {{
            "steps": [
                {{
                    "step_number": 1,
                    "description": "Navigate to GitHub login page",
                    "action": {{
                        "type": "navigation",
                        "target": "GitHub login page",
                        "value": "https://github.com/login",
                        "selectors": []
                    }}
                }},
                {{
                    "step_number": 2,
                    "description": "Enter username",
                    "action": {{
                        "type": "type",
                        "target": "username field",
                        "value": "ENV:GITHUB_USERNAME",
                        "selectors": ["#login_field", "input[name='login']"]
                    }}
                }},
                {{
                    "step_number": 3,
                    "description": "Enter password",
                    "action": {{
                        "type": "type",
                        "target": "password field",
                        "value": "ENV:GITHUB_PASSWORD",
                        "selectors": ["#password", "input[name='password']"]
                    }}
                }},
                {{
                    "step_number": 4,
                    "description": "Click sign in button",
                    "action": {{
                        "type": "submit",
                        "target": "login form",
                        "value": "",
                        "selectors": ["input[type='submit']", "button[type='submit']"]
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
        

        




    def _extract_json_from_text(self, text: str) -> dict:
        """Extract JSON from text response"""
        cleaned_response = re.sub(r"```json|```", "", text).strip()
    
    # Step 2: Remove trailing commas that might break JSON parsing
        cleaned_response = re.sub(r",\s*}", "}", cleaned_response)
        cleaned_response = re.sub(r",\s*]", "]", cleaned_response)
        
        try:
            # Step 3: Attempt to parse the cleaned JSON string
            parsed_data = json.loads(cleaned_response)
            logging.info("Successfully parsed LLM response to JSON.")
            return parsed_data
        except json.JSONDecodeError as e:
            logging.error(f"JSON decoding error: {e}")
            return {}  


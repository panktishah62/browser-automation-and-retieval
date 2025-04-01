from googleapiclient.discovery import build
from typing import Dict, List, Any
import os

class GoogleSearchAPI:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        if not self.api_key or not self.search_engine_id:
            raise ValueError("Google API key and Search Engine ID are required")
    
    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Perform a Google search using the Custom Search API.
        
        Args:
            query: Search query string
            **kwargs: Additional search parameters
            
        Returns:
            Dict containing search results
        """
        try:
            service = build("customsearch", "v1", developerKey=self.api_key)
            
            # Perform the search
            result = service.cse().list(
                q=query,
                cx=self.search_engine_id,
                **kwargs
            ).execute()
            
            return {
                "success": True,
                "message": "Search completed successfully",
                "results": self._format_results(result)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Search failed: {str(e)}",
                "error_type": "SearchError"
            }
    
    def _format_results(self, raw_results: Dict) -> List[Dict]:
        """Format the raw API results into a cleaner structure."""
        formatted = []
        
        if 'items' not in raw_results:
            return formatted
            
        for item in raw_results['items']:
            formatted.append({
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'displayLink': item.get('displayLink', '')
            })
            
        return formatted 
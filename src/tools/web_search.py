"""
R-Code Web Search Tool
=====================

Professional web search tool using Tavily Search Engine
integrated with LangGraph for the R-Code AI assistant.
"""

import os
from typing import Dict, Any, List, Optional
from langchain_tavily import TavilySearch
from langchain_core.tools import tool


class RCodeWebSearch:
    """Professional web search tool for R-Code AI assistant"""
    
    def __init__(self, max_results: int = 3):
        """
        Initialize the web search tool
        
        Args:
            max_results: Maximum number of search results to return
        """
        self.max_results = max_results
        self.tavily_search = None
        self._initialize_search()
    
    def _initialize_search(self):
        """Initialize Tavily search with API key"""
        api_key = os.getenv("TAVILY_API_KEY")
        if api_key:
            self.tavily_search = TavilySearch(
                max_results=self.max_results,
                api_key=api_key
            )
        else:
            print("⚠️  TAVILY_API_KEY not set. Web search will be unavailable.")
    
    def is_available(self) -> bool:
        """Check if web search is available"""
        return self.tavily_search is not None
    
    def search(self, query: str) -> Dict[str, Any]:
        """
        Perform web search
        
        Args:
            query: Search query string
            
        Returns:
            Dict containing search results
        """
        if not self.is_available():
            return {
                "error": "Web search unavailable. Please set TAVILY_API_KEY environment variable.",
                "query": query,
                "results": []
            }
        
        try:
            results = self.tavily_search.invoke(query)
            return {
                "query": query,
                "results": results.get("results", []),
                "success": True
            }
        except Exception as e:
            return {
                "error": f"Search failed: {str(e)}",
                "query": query,
                "results": [],
                "success": False
            }


# Global instance
_web_search = RCodeWebSearch()


@tool
def web_search(query: str) -> str:
    """
    Search the web for current information on any topic.
    
    Use this tool when you need to find up-to-date information,
    current events, recent developments, or when the user asks
    about something that might require web search.
    
    Args:
        query: The search query string
        
    Returns:
        String containing formatted search results
    """
    result = _web_search.search(query)
    
    if not result.get("success", False):
        return f"❌ Web search error: {result.get('error', 'Unknown error')}"
    
    # Format results for the AI
    formatted_results = []
    results = result.get("results", [])
    
    if not results:
        return f"🔍 No results found for: {query}"
    
    formatted_results.append(f"🔍 Web search results for: {query}\n")
    
    for i, item in enumerate(results[:_web_search.max_results], 1):
        title = item.get("title", "No title")
        url = item.get("url", "")
        content = item.get("content", "No content available")
        
        # Limit content length for readability
        if len(content) > 300:
            content = content[:300] + "..."
        
        formatted_results.append(f"{i}. **{title}**")
        formatted_results.append(f"   URL: {url}")
        formatted_results.append(f"   Content: {content}\n")
    
    return "\n".join(formatted_results)


@tool
def search_coding_help(query: str) -> str:
    """
    Search for coding help, programming tutorials, documentation, or technical solutions.
    
    Optimized for finding programming-related information, code examples,
    API documentation, and technical troubleshooting.
    
    Args:
        query: Programming or technical query
        
    Returns:
        String containing formatted coding-related search results
    """
    # Enhance query for coding-specific search
    enhanced_query = f"programming coding {query} tutorial documentation example"
    
    result = _web_search.search(enhanced_query)
    
    if not result.get("success", False):
        return f"❌ Coding search error: {result.get('error', 'Unknown error')}"
    
    results = result.get("results", [])
    if not results:
        return f"🔍 No coding help found for: {query}"
    
    formatted_results = [f"💻 Coding help for: {query}\n"]
    
    for i, item in enumerate(results[:_web_search.max_results], 1):
        title = item.get("title", "No title")
        url = item.get("url", "")
        content = item.get("content", "No content available")
        
        # Prioritize content with code-related keywords
        if any(keyword in content.lower() for keyword in 
               ['code', 'function', 'class', 'method', 'api', 'documentation', 'tutorial']):
            
            if len(content) > 400:
                content = content[:400] + "..."
            
            formatted_results.append(f"{i}. **{title}**")
            formatted_results.append(f"   📁 {url}")
            formatted_results.append(f"   📝 {content}\n")
    
    return "\n".join(formatted_results)


def get_web_search_tools() -> List:
    """
    Get list of web search tools for LangGraph integration
    
    Returns:
        List of web search tools
    """
    return [web_search, search_coding_help]


def is_web_search_available() -> bool:
    """Check if web search is available"""
    return _web_search.is_available()


# For backward compatibility and direct access
def search_web(query: str) -> Dict[str, Any]:
    """Direct web search function"""
    return _web_search.search(query)

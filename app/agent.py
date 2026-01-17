"""Research Agent using LangChain and Google Generative AI"""

import os
import asyncio
from typing import Optional, List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()


class ResearchAgent:
    """AI Research Agent powered by Google Generative AI"""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp", temperature: float = 0.3, max_tokens: int = 512):
        """
        Initialize the Research Agent
        
        Args:
            model_name: The Google Generative AI model to use
            temperature: Controls randomness in responses (0-1) - lower = more focused
            max_tokens: Maximum tokens in response - lower = cheaper
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment variables. "
                "Please set it in your .env file or environment."
            )
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            max_output_tokens=max_tokens,
            google_api_key=api_key
        )
        self.model_name = model_name
        self.max_tokens = max_tokens
        
    async def research(self, query: str, max_retries: int = 2) -> tuple[str, dict]:
        """
        Perform research on a given query (optimized for minimal token usage)
        
        Args:
            query: The research question or topic
            max_retries: Number of retry attempts for rate limit errors
            
        Returns:
            Tuple of (response content, token usage dict)
        """
        # Optimized prompt for minimal token consumption
        optimized_prompt = (
            f"Answer this concisely in {self.max_tokens//2} words or less. "
            f"Be direct and factual. No preamble or conclusion.\n\n"
            f"Question: {query}"
        )
        
        for attempt in range(max_retries + 1):
            try:
                response = await self.llm.ainvoke(optimized_prompt)
                
                # Extract token usage information
                token_usage = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
                
                # Debug: Print response structure
                print(f"Response type: {type(response)}")
                print(f"Response attributes: {dir(response)}")
                
                # Try to get usage metadata from response - try multiple paths
                if hasattr(response, 'response_metadata'):
                    print(f"Response metadata: {response.response_metadata}")
                    
                    # Try usage_metadata path
                    usage_metadata = response.response_metadata.get('usage_metadata', {})
                    if usage_metadata:
                        token_usage["prompt_tokens"] = usage_metadata.get('prompt_token_count', 0)
                        token_usage["completion_tokens"] = usage_metadata.get('candidates_token_count', 0)
                        token_usage["total_tokens"] = usage_metadata.get('total_token_count', 0)
                    
                    # Try direct token counts in response_metadata
                    if token_usage["total_tokens"] == 0:
                        token_usage["prompt_tokens"] = response.response_metadata.get('prompt_token_count', 0)
                        token_usage["completion_tokens"] = response.response_metadata.get('candidates_token_count', 0)
                        token_usage["total_tokens"] = response.response_metadata.get('total_token_count', 0)
                
                # If still no token count, estimate based on content
                if token_usage["total_tokens"] == 0:
                    # Rough estimation: ~4 characters per token
                    estimated_prompt = len(optimized_prompt) // 4
                    estimated_completion = len(str(response.content)) // 4
                    token_usage["prompt_tokens"] = estimated_prompt
                    token_usage["completion_tokens"] = estimated_completion
                    token_usage["total_tokens"] = estimated_prompt + estimated_completion
                    print(f"Using estimated token counts: {token_usage}")
                
                print(f"Final token usage: {token_usage}")
                return response.content, token_usage
                
            except Exception as e:
                error_str = str(e)
                
                # Check for quota/rate limit errors
                if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                    if attempt < max_retries:
                        # Wait before retry (exponential backoff)
                        wait_time = 2 ** attempt
                        print(f"Rate limit hit, retrying in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # Out of retries, return friendly error message
                        return (
                            "❌ **API Quota Exceeded**\n\n"
                            "You've hit your Google API rate limit. This usually means:\n\n"
                            "1. **Free tier quota exhausted** - Check your usage at https://makersuite.google.com/\n"
                            "2. **Too many requests** - Wait a few minutes and try again\n"
                            "3. **Daily limit reached** - Quota resets daily\n\n"
                            "💡 **Solutions:**\n"
                            "- Wait 1-2 minutes before trying again\n"
                            "- Use lower token limits (128-256) to conserve quota\n"
                            "- Consider enabling billing for higher limits\n"
                            f"\n📋 **Error details:** {error_str[:200]}",
                            {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                        )
                
                # Other errors
                return (
                    f"❌ **Error during research:**\n\n{error_str}\n\n"
                    "Please check your API key and try again.",
                    {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                )
        
        # Should never reach here
        return "Error: Max retries exceeded", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    def get_info(self) -> dict:
        """Get information about the agent"""
        return {
            "model": self.model_name,
            "status": "ready",
            "capabilities": [
                "Text generation",
                "Research queries",
                "Information synthesis"
            ]
        }


def get_model_price_tier(model_name: str) -> int:
    """
    Get price tier for a model (lower number = cheaper)
    
    Args:
        model_name: The model name
        
    Returns:
        Price tier (0 = cheapest, higher = more expensive)
    """
    model_lower = model_name.lower()
    
    # Experimental and flash models are cheapest
    if 'exp' in model_lower or 'experimental' in model_lower:
        return 0
    elif 'flash' in model_lower:
        return 1
    elif 'pro' in model_lower:
        return 2
    elif 'ultra' in model_lower:
        return 3
    else:
        return 1  # Default to mid-tier


def list_available_models() -> List[Dict[str, str]]:
    """
    List all available Google Generative AI models using the new google.genai package
    Ordered by price (cheapest first)
    
    Returns:
        List of model dictionaries with name, display_name, and price_indicator
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return []
    
    try:
        # Initialize client with the new API
        client = genai.Client(api_key=api_key)
        models = []
        
        # List models using the new API
        for model in client.models.list():
            # Filter for generative models (those that can generate content)
            if hasattr(model, 'supported_generation_methods'):
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.replace("models/", "") if hasattr(model, 'name') else str(model)
                    display_name = getattr(model, 'display_name', model_name)
                    price_tier = get_model_price_tier(model_name)
                    
                    # Add price indicator emoji
                    price_emoji = "💰" * (price_tier + 1) if price_tier < 3 else "💰💰💰+"
                    
                    models.append({
                        "name": model_name,
                        "display_name": display_name,
                        "description": getattr(model, 'description', ''),
                        "price_tier": price_tier,
                        "price_indicator": price_emoji
                    })
            else:
                # If no supported_generation_methods attribute, include all models
                model_name = model.name.replace("models/", "") if hasattr(model, 'name') else str(model)
                display_name = getattr(model, 'display_name', model_name)
                price_tier = get_model_price_tier(model_name)
                price_emoji = "💰" * (price_tier + 1) if price_tier < 3 else "💰💰💰+"
                
                models.append({
                    "name": model_name,
                    "display_name": display_name,
                    "description": getattr(model, 'description', ''),
                    "price_tier": price_tier,
                    "price_indicator": price_emoji
                })
        
        # Sort by price tier (cheapest first)
        models.sort(key=lambda x: x.get('price_tier', 1))
        return models
        
    except Exception as e:
        print(f"Error listing models: {e}")
        # Return default models as fallback (sorted by price)
        return [
            {
                "name": "gemini-2.0-flash-exp",
                "display_name": "Gemini 2.0 Flash (Experimental)",
                "description": "Latest experimental model",
                "price_tier": 0,
                "price_indicator": "💰"
            },
            {
                "name": "gemini-1.5-flash",
                "display_name": "Gemini 1.5 Flash",
                "description": "Fast and efficient model",
                "price_tier": 1,
                "price_indicator": "💰💰"
            },
            {
                "name": "gemini-1.5-pro",
                "display_name": "Gemini 1.5 Pro",
                "description": "Advanced model for complex tasks",
                "price_tier": 2,
                "price_indicator": "💰💰💰"
            }
        ]

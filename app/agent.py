"""Research Agent using LangChain and Google Generative AI"""

import os
import asyncio
from typing import List, Dict, TypedDict, Annotated
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
from google import genai
from google.genai import types

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Load environment variables
load_dotenv()


class ResearchAgent:
    """AI Research Agent powered by Google Generative AI"""
    
    def __init__(self, model_name: str = "gemini-2.0-flash", temperature: float = 0.3, max_tokens: int = 512):
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


# ============================================================================
# LANGGRAPH: DEEP RESEARCH MODE FOR PRODUCT MANAGEMENT
# ============================================================================

class PMResearchState(TypedDict):
    """State for Product Management Deep Research workflow"""
    query: str
    messages: Annotated[List, add_messages]
    research_plan: str
    market_analysis: str
    user_insights: str
    competitive_landscape: str
    risks_and_challenges: str
    devils_advocate: str
    recommendations: str
    final_report: str
    current_step: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class DeepResearchAgent:
    """
    LangGraph-powered Deep Research Agent
    Optimized for Product Management decision-making
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash", temperature: float = 0.7):
        """
        Initialize the Deep Research Agent with LangGraph workflow
        
        Args:
            model_name: The Google Generative AI model to use
            temperature: Higher temperature for creative PM insights
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found")
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            max_output_tokens=8192,  # High limit for comprehensive deep research
            google_api_key=api_key
        )
        self.model_name = model_name
        self.total_tokens_used = 0
        
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for PM deep research"""
        workflow = StateGraph(PMResearchState)
        
        # Add nodes (steps in the research process)
        workflow.add_node("plan", self._plan_research)
        workflow.add_node("market_analysis", self._analyze_market)
        workflow.add_node("user_insights", self._gather_user_insights)
        workflow.add_node("competitive_analysis", self._analyze_competition)
        workflow.add_node("risk_assessment", self._assess_risks)
        workflow.add_node("devils_advocate", self._devils_advocate)
        workflow.add_node("synthesize", self._synthesize_findings)
        
        # Define the flow
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "market_analysis")
        workflow.add_edge("market_analysis", "user_insights")
        workflow.add_edge("user_insights", "competitive_analysis")
        workflow.add_edge("competitive_analysis", "risk_assessment")
        workflow.add_edge("risk_assessment", "devils_advocate")
        workflow.add_edge("devils_advocate", "synthesize")
        workflow.add_edge("synthesize", END)
        
        return workflow.compile()
    
    def _track_tokens(self, response, state: PMResearchState) -> PMResearchState:
        """Track token usage from a response"""
        if hasattr(response, 'response_metadata'):
            usage = response.response_metadata.get('usage_metadata', {})
            state["prompt_tokens"] += usage.get('prompt_token_count', 0)
            state["completion_tokens"] += usage.get('candidates_token_count', 0)
            state["total_tokens"] = state["prompt_tokens"] + state["completion_tokens"]
        return state
    
    async def _plan_research(self, state: PMResearchState) -> PMResearchState:
        """Step 1: Create a research plan based on the PM question"""
        planning_prompt = f"""You are a senior product manager creating a research plan.

Question: {state['query']}

Break this down into a structured research plan covering:
1. Market & Opportunity
2. User Needs & Pain Points
3. Competitive Landscape
4. Risks & Challenges
5. Critical Analysis (Devil's Advocate)
6. Strategic Recommendations

Provide a concise plan (2-3 sentences per area). Be thorough and detailed."""

        response = await self.llm.ainvoke([HumanMessage(content=planning_prompt)])
        state = self._track_tokens(response, state)
        
        state["research_plan"] = response.content
        state["current_step"] = "Planning"
        state["messages"].append(AIMessage(content=f"📋 Research Plan:\n{response.content}"))
        
        return state
    
    async def _analyze_market(self, state: PMResearchState) -> PMResearchState:
        """Step 2: Analyze market opportunity and trends"""
        market_prompt = f"""You are a market analyst for product management.

Original Question: {state['query']}
Research Plan: {state['research_plan']}

Provide a COMPREHENSIVE MARKET & OPPORTUNITY ANALYSIS with specific details:
- Market size estimate with numbers (TAM/SAM/SOM if applicable)
- Growth rate and trajectory (percentages, trends)
- Current market trends and dynamics
- Target customer segments and their characteristics
- Market maturity stage
- Entry barriers and opportunities

Be detailed, specific, and data-driven. Provide 6-8 substantive points."""

        response = await self.llm.ainvoke([HumanMessage(content=market_prompt)])
        state = self._track_tokens(response, state)
        
        state["market_analysis"] = response.content
        state["current_step"] = "Market Analysis"
        state["messages"].append(AIMessage(content=f"📊 Market Analysis:\n{response.content}"))
        
        return state
    
    async def _gather_user_insights(self, state: PMResearchState) -> PMResearchState:
        """Step 3: Analyze user needs and pain points"""
        user_prompt = f"""You are a user research expert conducting deep analysis.

Question: {state['query']}
Market Context: {state['market_analysis']}

Provide COMPREHENSIVE USER NEEDS & PAIN POINTS ANALYSIS:
- Define 2-3 primary user personas with demographics and behaviors
- Identify specific pain points with severity levels
- Articulate user expectations, desires, and motivations
- Map the user journey and friction points
- Identify adoption barriers (cost, complexity, switching costs, etc.)
- Analyze willingness to pay and value perception

Be specific and thorough. Provide 6-8 detailed insights."""

        response = await self.llm.ainvoke([HumanMessage(content=user_prompt)])
        state = self._track_tokens(response, state)
        
        state["user_insights"] = response.content
        state["current_step"] = "User Research"
        state["messages"].append(AIMessage(content=f"👥 User Insights:\n{response.content}"))
        
        return state
    
    async def _analyze_competition(self, state: PMResearchState) -> PMResearchState:
        """Step 4: Competitive landscape analysis"""
        competitive_prompt = f"""You are a competitive intelligence analyst conducting thorough research.

Question: {state['query']}
Market Context: {state['market_analysis']}
User Context: {state['user_insights']}

Provide COMPREHENSIVE COMPETITIVE LANDSCAPE ANALYSIS:
- Identify specific competitors by name (direct and indirect)
- Analyze each competitor's positioning, strengths, and weaknesses
- Evaluate competitive advantages and moats
- Identify gaps in current market solutions
- Assess differentiation opportunities
- Analyze pricing strategies and business models
- Evaluate market share distribution

Be specific with company names and detailed analysis. Provide 6-8 strategic insights."""

        response = await self.llm.ainvoke([HumanMessage(content=competitive_prompt)])
        state = self._track_tokens(response, state)
        
        state["competitive_landscape"] = response.content
        state["current_step"] = "Competitive Analysis"
        state["messages"].append(AIMessage(content=f"⚔️ Competitive Landscape:\n{response.content}"))
        
        return state
    
    async def _assess_risks(self, state: PMResearchState) -> PMResearchState:
        """Step 5: Risk and challenge assessment"""
        risk_prompt = f"""You are a risk assessment specialist conducting detailed analysis.

Question: {state['query']}
Market: {state['market_analysis']}
Competition: {state['competitive_landscape']}

Provide COMPREHENSIVE RISKS & CHALLENGES ASSESSMENT:
- Technical risks (scalability, architecture, integration, security)
- Market risks (timing, adoption, competition, saturation)
- Financial risks (burn rate, unit economics, profitability)
- Operational risks (team, resources, partnerships)
- Regulatory and compliance risks
- Execution challenges
- Mitigation strategies for each major risk

Be realistic, specific, and thorough. Identify 6-8 significant risks with mitigation strategies."""

        response = await self.llm.ainvoke([HumanMessage(content=risk_prompt)])
        state = self._track_tokens(response, state)
        
        state["risks_and_challenges"] = response.content
        state["current_step"] = "Risk Assessment"
        state["messages"].append(AIMessage(content=f"⚠️ Risks & Challenges:\n{response.content}"))
        
        return state
    
    async def _devils_advocate(self, state: PMResearchState) -> PMResearchState:
        """Step 6: Devil's Advocate - Critical analysis of why this might fail"""
        devils_prompt = f"""You are a DEVIL'S ADVOCATE - a critical analyst whose job is to challenge assumptions and point out why this product might FAIL.

Question: {state['query']}

All Research:
- Market: {state['market_analysis']}
- Users: {state['user_insights']}
- Competition: {state['competitive_landscape']}
- Risks: {state['risks_and_challenges']}

Your task: Be brutally honest and critical. Identify:
- Why this product is likely to FAIL
- Over-optimistic assumptions in the research
- Hidden costs and challenges not yet considered
- Why competitors might crush this product
- Why users might NOT adopt it despite claimed pain points
- Timing issues (too early/too late to market)
- Resource constraints and execution impossibilities
- Financial reasons this won't be profitable
- Why the team/company might not be the right one to build this

Be pessimistic, realistic, and blunt. This analysis should make someone think twice. Provide 8-10 critical points that challenge the viability of this product."""

        response = await self.llm.ainvoke([HumanMessage(content=devils_prompt)])
        state = self._track_tokens(response, state)
        
        state["devils_advocate"] = response.content
        state["current_step"] = "Devil's Advocate"
        state["messages"].append(AIMessage(content=f"😈 Devil's Advocate:\n{response.content}"))
        
        return state
    
    async def _synthesize_findings(self, state: PMResearchState) -> PMResearchState:
        """Step 7: Synthesize all research into balanced, actionable recommendations"""
        synthesis_prompt = f"""You are a Chief Product Officer synthesizing research into a balanced decision framework.

Original Question: {state['query']}

Research Completed:
- Market Analysis: {state['market_analysis']}
- User Insights: {state['user_insights']}
- Competitive Landscape: {state['competitive_landscape']}
- Risks & Challenges: {state['risks_and_challenges']}
- Critical Analysis: {state['devils_advocate']}

Provide COMPREHENSIVE STRATEGIC RECOMMENDATIONS that balance optimism with realism:

1. **Clear Decision** (Go/No-Go/Pivot, with detailed rationale considering both opportunities AND critical challenges)
2. **Key Success Metrics** (specific, measurable KPIs to track)
3. **Recommended Approach** (phased rollout, MVP strategy, or full launch)
4. **Timeline and Milestones** (realistic with key decision points)
5. **Resource Requirements** (team, budget, time estimates)
6. **Go/No-Go Criteria** (what would make you stop or pivot)
7. **Decision Rationale** (balanced view acknowledging both opportunity and devil's advocate points)

Be realistic, balanced, and actionable. This should be a complete decision framework."""

        response = await self.llm.ainvoke([HumanMessage(content=synthesis_prompt)])
        state = self._track_tokens(response, state)
        
        state["recommendations"] = response.content
        state["current_step"] = "Synthesis Complete"
        
        # Create final comprehensive report
        final_report = f"""# Deep Research Report: Product Management Analysis

## 📋 Research Question
{state['query']}

## 📊 Market Analysis
{state['market_analysis']}

## 👥 User Insights
{state['user_insights']}

## ⚔️ Competitive Landscape
{state['competitive_landscape']}

## ⚠️ Risks & Challenges
{state['risks_and_challenges']}

## 😈 Devil's Advocate: Why This Might Fail
{state['devils_advocate']}

## 🎯 Strategic Recommendations
{state['recommendations']}

---
*Generated using LangGraph Deep Research Mode*
*Total Tokens Used: {state['total_tokens']} (Prompt: {state['prompt_tokens']}, Completion: {state['completion_tokens']})*
"""
        
        state["final_report"] = final_report
        state["messages"].append(AIMessage(content=f"✅ Final Report Complete"))
        
        return state
    
    async def deep_research(self, query: str) -> tuple[str, dict]:
        """
        Execute deep research workflow for product management questions
        
        Args:
            query: The product management question
            
        Returns:
            Tuple of (final report, metadata with token usage)
        """
        try:
            # Initialize state
            initial_state = PMResearchState(
                query=query,
                messages=[],
                research_plan="",
                market_analysis="",
                user_insights="",
                competitive_landscape="",
                risks_and_challenges="",
                devils_advocate="",
                recommendations="",
                final_report="",
                current_step="Initializing",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0
            )
            
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            metadata = {
                "steps_completed": 7,
                "model": self.model_name,
                "mode": "deep_research",
                "prompt_tokens": final_state["prompt_tokens"],
                "completion_tokens": final_state["completion_tokens"],
                "total_tokens": final_state["total_tokens"]
            }
            
            return final_state["final_report"], metadata
            
        except Exception as e:
            error_report = f"""❌ **Deep Research Error**

An error occurred during the research process:
{str(e)}

This might be due to:
- API rate limits (deep research makes multiple calls)
- Quota exhaustion
- Network issues

💡 Try:
- Waiting a few minutes
- Using standard research mode
- Checking your API quota at https://makersuite.google.com/
"""
            return error_report, {"error": str(e), "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    
    def get_info(self) -> dict:
        """Get information about the deep research agent"""
        return {
            "mode": "deep_research",
            "model": self.model_name,
            "workflow_steps": 7,
            "optimized_for": "Product Management",
            "features": [
                "Multi-step reasoning",
                "Market analysis",
                "User research",
                "Competitive intelligence",
                "Risk assessment",
                "Devil's Advocate (critical analysis)",
                "Strategic recommendations"
            ]
        }

"""FastAPI routes and endpoints"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import os
import time
from collections import deque

from app.agent import ResearchAgent, DeepResearchAgent, list_available_models


# Initialize FastAPI app
app = FastAPI(
    title="Research Agent API",
    description="AI-powered research agent using Google Generative AI",
    version="0.1.0"
)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# Initialize agent caches (will be lazy-loaded per model and max_tokens)
_agents: dict[tuple[str, int], ResearchAgent] = {}
_deep_agents: dict[str, DeepResearchAgent] = {}

# Simple rate limiter: track request timestamps
_request_timestamps = deque(maxlen=50)  # Keep last 50 requests
RATE_LIMIT_WINDOW = 60  # seconds
MAX_REQUESTS_PER_WINDOW = 10  # Max 10 requests per minute for free tier


def check_rate_limit():
    """Check if rate limit is exceeded"""
    now = time.time()
    
    # Remove timestamps older than the window
    while _request_timestamps and _request_timestamps[0] < now - RATE_LIMIT_WINDOW:
        _request_timestamps.popleft()
    
    # Check if we're at the limit
    if len(_request_timestamps) >= MAX_REQUESTS_PER_WINDOW:
        # Calculate wait time
        oldest_request = _request_timestamps[0]
        wait_seconds = int(RATE_LIMIT_WINDOW - (now - oldest_request)) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Please wait {wait_seconds} seconds before trying again. "
                   f"(Free tier limit: {MAX_REQUESTS_PER_WINDOW} requests per {RATE_LIMIT_WINDOW} seconds)"
        )
    
    # Add current timestamp
    _request_timestamps.append(now)


def get_agent(model_name: str = "gemini-2.0-flash", max_tokens: int = 512) -> ResearchAgent:
    """Get or create a research agent instance for a specific model and token limit"""
    global _agents
    cache_key = (model_name, max_tokens)
    if cache_key not in _agents:
        try:
            _agents[cache_key] = ResearchAgent(model_name=model_name, max_tokens=max_tokens)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
    return _agents[cache_key]


def get_deep_agent(model_name: str = "gemini-2.0-flash") -> DeepResearchAgent:
    """Get or create a deep research agent instance for a specific model"""
    global _deep_agents
    if model_name not in _deep_agents:
        try:
            _deep_agents[model_name] = DeepResearchAgent(model_name=model_name)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
    return _deep_agents[model_name]


# Request/Response models
class ResearchRequest(BaseModel):
    query: str
    model: str = "gemini-2.0-flash"
    max_tokens: int = 512  # Lower for free tier optimization


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ResearchResponse(BaseModel):
    query: str
    result: str
    model: str
    token_usage: TokenUsage


class DeepResearchResponse(BaseModel):
    query: str
    result: str
    model: str
    mode: str
    steps_completed: int
    token_usage: TokenUsage


# Routes
@app.get("/")
async def root():
    """Serve the main HTML page"""
    index_path = Path(__file__).parent.parent / "static" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Research Agent API", "docs": "/docs"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Research Agent is running",
        "version": "0.1.0"
    }


@app.get("/agent/info")
async def agent_info():
    """Get information about the research agent"""
    try:
        agent = get_agent()
        return agent.get_info()
    except HTTPException:
        return {
            "status": "not_configured",
            "message": "Agent not configured. Please set GOOGLE_API_KEY environment variable."
        }


@app.get("/models")
async def get_models():
    """Get list of available Google Generative AI models"""
    models = list_available_models()
    if not models:
        raise HTTPException(
            status_code=500,
            detail="Could not fetch models. Please check GOOGLE_API_KEY."
        )
    return {"models": models}


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    """
    Perform research on a given query (optimized for minimal token usage)
    Rate limited to protect free tier quota
    
    Args:
        request: Research request with query, model selection, and token limit
        
    Returns:
        Research results with token usage information
    """
    # Check rate limit before processing
    check_rate_limit()
    
    agent = get_agent(model_name=request.model, max_tokens=request.max_tokens)
    result, token_usage = await agent.research(request.query)
    
    return ResearchResponse(
        query=request.query,
        result=result,
        model=agent.model_name,
        token_usage=TokenUsage(**token_usage)
    )


@app.post("/deep-research", response_model=DeepResearchResponse)
async def deep_research(request: ResearchRequest):
    """
    Perform DEEP RESEARCH using LangGraph multi-step workflow
    Optimized for Product Management decision-making
    
    ⚠️ WARNING: Uses 5-10x more tokens than standard research
    
    Workflow:
    1. Research Planning
    2. Market Analysis
    3. User Insights
    4. Competitive Landscape
    5. Risk Assessment
    6. Devil's Advocate (Critical Analysis)
    7. Strategic Synthesis
    
    Args:
        request: Research request with PM question and model selection
        
    Returns:
        Comprehensive research report with all analysis steps
    """
    # Check rate limit (deep research counts as 1 request but uses more tokens)
    check_rate_limit()
    
    deep_agent = get_deep_agent(model_name=request.model)
    report, metadata = await deep_agent.deep_research(request.query)
    
    return DeepResearchResponse(
        query=request.query,
        result=report,
        model=deep_agent.model_name,
        mode="deep_research",
        steps_completed=metadata.get("steps_completed", 7),
        token_usage=TokenUsage(
            prompt_tokens=metadata.get("prompt_tokens", 0),
            completion_tokens=metadata.get("completion_tokens", 0),
            total_tokens=metadata.get("total_tokens", 0)
        )
    )

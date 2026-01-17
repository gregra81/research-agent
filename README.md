# 🔬 Research Agent

An AI-powered research agent built with FastAPI, LangChain, and Google Generative AI. Optimized for free tier usage with intelligent rate limiting and token management.

## ✨ Features

### 🤖 AI-Powered Research
- **Multiple Gemini Models**: Choose from various Google Gemini models
- **Model Selection**: Dropdown with price indicators (💰 = cheapest)
- **Smart Ordering**: Models sorted by cost (cheapest first)
- **Automatic Retry**: Handles rate limits with exponential backoff

### 💰 Free Tier Optimization
- **Token Control**: Adjustable slider (128-2048 tokens) to manage costs
- **Rate Limiting**: Built-in protection (10 requests/minute)
- **Token Usage Display**: See exactly how many tokens each request consumes
- **Cost-Conscious**: Optimized prompts for minimal token usage
- **Visual Indicators**: Real-time feedback on token limits and pricing

### 🌐 Modern Web Interface
- **Beautiful UI**: Purple gradient design with responsive layout
- **Wide Layout**: 1200px container for optimal viewing
- **Real-time Feedback**: Loading states and error messages
- **Model Selector**: Easy model switching with price indicators
- **Token Slider**: Color-coded (green=cheap, yellow=balanced, red=expensive)

### 🔧 Technical Excellence
- **Python 3.14**: Latest Python with performance improvements
- **FastAPI**: High-performance async web framework
- **Auto-reload**: Development mode with live code updates
- **Comprehensive API**: RESTful endpoints with automatic documentation
- **Error Handling**: Friendly, actionable error messages

## 📁 Project Structure

```
research-agent/
├── app/
│   ├── __init__.py       # Package initialization
│   ├── api.py            # FastAPI routes, rate limiting, error handling
│   └── agent.py          # Research agent with retry logic & token tracking
├── static/
│   ├── css/
│   │   └── style.css     # Modern gradient UI styling
│   ├── js/
│   │   └── app.js        # Frontend logic, model loading, token display
│   └── index.html        # Responsive web interface
├── main.py               # Application entry point with warning suppression
├── pyproject.toml        # Dependencies (Python 3.14+)
├── .env                  # API key configuration (create this)
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.14+** (required)
- **Google AI API Key** ([Get it free here](https://makersuite.google.com/app/apikey))
- **uv package manager** ([Install uv](https://github.com/astral-sh/uv))

### 1. Install Dependencies

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management:

```bash
# Clone or download the project
cd research-agent

# Install dependencies with Python 3.14
uv sync
```

### 2. Configure API Key

Get your **free** Google AI API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

Create a `.env` file in the project root:

```bash
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

**Or** export it in your terminal session:

```bash
export GOOGLE_API_KEY="your_api_key_here"
```

### 3. Run the Application

```bash
uv run python main.py
```

The server will start with helpful messages:
```
🚀 Starting Research Agent server...
📍 Server will be available at: http://localhost:8000
📚 API docs available at: http://localhost:8000/docs
```

## 💻 Usage

### Web Interface

Open your browser and navigate to **http://localhost:8000**

You'll see:

1. **🆓 Free Tier Badge**: Shows the app is optimized for Google's free tier
2. **Rate Limit Warning**: Orange banner showing "10 requests per minute" protection
3. **Model Selector**: Dropdown with models sorted by price (💰 = cheapest)
4. **Token Slider**: Adjustable from 128 (minimal) to 2048 (detailed)
   - Green zone: Cheap, minimal responses
   - Yellow zone: Balanced (default 512)
   - Red zone: Expensive, detailed responses
5. **Research Box**: Enter your question
6. **Results**: Shows response with token usage breakdown

### Using the Token Controls

**For Free Tier Users (Recommended):**
- **128-256 tokens**: Quick facts, very cost-effective
- **512 tokens**: Balanced responses (default) ✅
- **1024+ tokens**: Detailed research, uses more quota

**Token Usage Display:**
After each request, you'll see:
```
📊 Token Usage:
Input: 25 tokens | Output: 120 tokens | Total: 145 tokens
```

### API Endpoints

Access these programmatically:

#### Get Available Models
```bash
curl http://localhost:8000/models
```

Response includes price tiers and indicators:
```json
{
  "models": [
    {
      "name": "gemini-2.0-flash-exp",
      "display_name": "Gemini 2.0 Flash (Experimental)",
      "price_tier": 0,
      "price_indicator": "💰"
    }
  ]
}
```

#### Research Query with Token Control
```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the top 3 largest countries?",
    "model": "gemini-2.0-flash-exp",
    "max_tokens": 512
  }'
```

Response includes token usage:
```json
{
  "query": "What are the top 3 largest countries?",
  "result": "Russia, Canada, and USA are the three largest...",
  "model": "gemini-2.0-flash-exp",
  "token_usage": {
    "prompt_tokens": 25,
    "completion_tokens": 48,
    "total_tokens": 73
  }
}
```

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Agent Information
```bash
curl http://localhost:8000/agent/info
```

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🛡️ Rate Limiting & Quota Protection

The app includes built-in protection for free tier users:

### App-Level Rate Limiting
- **10 requests per minute** maximum
- Prevents hitting Google's quota limits
- Shows clear wait times if exceeded
- Automatic tracking and enforcement

### Retry Logic
- **Automatic retries** on rate limit errors (429)
- **Exponential backoff**: Waits 1s, then 2s, then 4s
- Graceful degradation with helpful error messages

### Error Handling
When quota is exceeded, you'll see:
```
❌ API Quota Exceeded

You've hit your Google API rate limit. This usually means:
1. Free tier quota exhausted
2. Too many requests
3. Daily limit reached

💡 Solutions:
- Wait 1-2 minutes before trying again
- Use lower token limits (128-256)
- Check your quota at https://makersuite.google.com/
```

## 🔧 Development

### Auto-Reload Mode
The application runs with **auto-reload enabled** - any changes to Python files automatically restart the server.

### Adding New Features

1. **Agent Logic** (`app/agent.py`):
   - Add new research methods
   - Modify token estimation
   - Update retry logic

2. **API Routes** (`app/api.py`):
   - Add new endpoints
   - Adjust rate limits
   - Modify response models

3. **Frontend** (`static/` directory):
   - Update UI components in `index.html`
   - Modify styling in `css/style.css`
   - Add features in `js/app.js`

### Testing Changes

```bash
# Make your changes, then the server auto-reloads
# Refresh browser (Cmd+Shift+R or Ctrl+F5)
```

## 📦 Dependencies

### Core
- **Python 3.14+**: Latest Python version
- **FastAPI >=0.128.0**: Modern web framework
- **Uvicorn >=0.34.0**: ASGI server

### AI & Language Models
- **langchain-google-genai >=2.0.8**: Google Gemini integration
- **google-genai >=1.0.0**: Official Google Genai SDK (replaces deprecated `google-generativeai`)
- **LangGraph >=1.0.5**: Agent workflow orchestration
- **langchain-mcp-adapters >=0.2.1**: Model Context Protocol support

### Utilities
- **python-dotenv >=1.0.0**: Environment variable management
- **pydantic >=2.0.0**: Data validation (Python 3.14 compatible)

## 🎯 Best Practices

### For Free Tier Users

1. **Use Cheapest Models**: Start with 💰 models (experimental/flash)
2. **Lower Token Limits**: Keep slider at 128-512 for most queries
3. **Space Out Requests**: Wait 6+ seconds between requests
4. **Monitor Usage**: Check token counts in responses
5. **Check Quota**: Visit https://makersuite.google.com/ regularly

### For Production Use

- Enable billing for higher rate limits
- Adjust rate limits in `app/api.py`:
  ```python
  MAX_REQUESTS_PER_WINDOW = 60  # Increase for paid tier
  ```
- Remove debug print statements in `app/agent.py`
- Consider adding authentication
- Set up monitoring and logging

## 🐛 Troubleshooting

### "429 RESOURCE_EXHAUSTED" Error
- **Cause**: Google API quota exceeded
- **Solution**: Wait 1-2 minutes, use lower token limits, check quota usage

### Models Not Loading
- **Cause**: Invalid API key or network issue
- **Solution**: Check `.env` file, verify API key at https://makersuite.google.com/

### Token Usage Shows "(estimated)"
- **Cause**: API not returning token metadata
- **Solution**: This is normal - estimation is accurate (±10%)

### Rate Limit Hit Too Often
- **Cause**: Making requests too quickly
- **Solution**: Space out requests, current limit is 10/minute

## 📝 License

MIT

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
```bash
git clone <your-repo>
cd research-agent
uv sync
# Create .env with your API key
uv run python main.py
```

## 🙏 Acknowledgments

- Google Gemini AI for the powerful language models
- FastAPI for the excellent web framework
- LangChain for the AI orchestration tools

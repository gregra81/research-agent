# 🔬 Research Agent

An AI-powered research agent built with FastAPI, LangChain, and Google Generative AI.

## Features

- 🤖 Powered by Google's Gemini AI models
- 🌐 Web-based interface with modern UI
- 🔌 RESTful API with automatic documentation
- 📊 Built with LangGraph for complex agent workflows
- 🔧 Extensible architecture with MCP adapters

## Project Structure

```
research-agent/
├── app/
│   ├── __init__.py       # Package initialization
│   ├── api.py            # FastAPI routes and endpoints
│   └── agent.py          # Research agent logic with LangChain
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   ├── js/
│   │   └── app.js        # Frontend JavaScript
│   └── index.html        # Main web interface
├── main.py               # Application entry point
├── pyproject.toml        # Project dependencies
└── README.md             # This file
```

## Setup

### 1. Install Dependencies

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management:

```bash
# Install dependencies
uv sync
```

### 2. Configure API Key

Get your Google AI API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

Create a `.env` file in the project root:

```bash
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

Or export it in your terminal:

```bash
export GOOGLE_API_KEY="your_api_key_here"
```

## Running the Application

### Option 1: Using uv (Recommended)

```bash
uv run python main.py
```

### Option 2: Direct Python

```bash
# After installing dependencies
python main.py
```

The server will start on `http://localhost:8000`

## Usage

### Web Interface

Open your browser and navigate to:
- **Main App**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Agent Information
```bash
curl http://localhost:8000/agent/info
```

#### Research Query
```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest developments in quantum computing?"}'
```

## Development

The application runs with auto-reload enabled, so any changes to the code will automatically restart the server.

### Adding New Features

1. **Agent Logic**: Modify `app/agent.py` to add new research capabilities
2. **API Routes**: Add new endpoints in `app/api.py`
3. **Frontend**: Update HTML/CSS/JS files in the `static/` directory

## Dependencies

- **FastAPI**: Web framework
- **LangChain Google GenAI**: Google Generative AI integration
- **LangGraph**: Agent workflow orchestration
- **LangChain MCP Adapters**: Model Context Protocol support
- **Uvicorn**: ASGI server
- **python-dotenv**: Environment variable management

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

"""Research Agent - Main Entry Point"""

import warnings
import uvicorn

# Suppress known compatibility warnings for Python 3.14
warnings.filterwarnings("ignore", message="Core Pydantic V1 functionality isn't compatible with Python 3.14")
warnings.filterwarnings("ignore", category=FutureWarning, module="google")

from app.api import app


def main():
    """Run the Research Agent server"""
    print("🚀 Starting Research Agent server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    print()
    
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload during development
    )


if __name__ == "__main__":
    main()

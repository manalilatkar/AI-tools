# 🔬 Deep Research Agent

An AI-powered research agent that scrapes company websites, analyzes content, and generates comprehensive reports based on your custom questions.

![Deep Research Agent](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![React](https://img.shields.io/badge/React-18.2-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)

## ✨ Features

- 🕷️ **Smart Web Scraping** - Recursively crawls websites with configurable depth and page limits
- 🤖 **Multi-Model Support** - Choose from Claude or GPT models based on your needs
- 📊 **Intelligent Categorization** - Automatically maps content to your research questions
- 📝 **Professional Reports** - Generates detailed, well-structured research reports
- 🎨 **Beautiful UI** - Clean, modern React interface with real-time progress tracking
- 🐳 **Docker Ready** - One-command deployment with Docker Compose

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- Or: Python 3.11+ and Node.js 18+
- API keys for Claude (Anthropic) and/or GPT (OpenAI)

### Option 1: Docker Deployment (Recommended)

1. **Clone and configure:**
   ```bash
   git clone <your-repo-url>
   cd deep-research-agent
   
   # Create environment file
   cp backend/.env.example .env
   ```

2. **Add your API keys to `.env`:**
   ```bash
   ANTHROPIC_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here  # Optional
   ```

3. **Launch:**
   ```bash
   docker-compose up --build
   ```

4. **Access the app:**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

## 🤖 Model Selection Guide

| Model | Best For | Speed | Cost | Context |
|-------|----------|-------|------|---------|
| **Claude Sonnet 4** | General research, balanced needs | ⚡⚡ | 💵💵 | 200K |
| **Claude Opus 4** | Complex analysis, detailed reports | ⚡ | 💵💵💵 | 200K |
| **Claude Haiku 4** | Quick summaries, high volume | ⚡⚡⚡ | 💵 | 200K |
| **GPT-4o** | Alternative perspective | ⚡⚡ | 💵💵 | 128K |
| **GPT-4o Mini** | Budget-conscious, simple tasks | ⚡⚡⚡ | 💵 | 128K |

### When to Use Each Model:

- **Claude Sonnet 4** (Default): The sweet spot for most research tasks. Great reasoning, good speed, reasonable cost. Start here.

- **Claude Opus 4**: When you need the absolute best analysis. Use for complex competitive intelligence, detailed market research, or when accuracy is critical and cost isn't a concern.

- **Claude Haiku 4**: Perfect for quick reconnaissance or when processing many websites. Great for initial scans before deeper dives.

- **GPT-4o**: Good alternative when you want a different perspective or cross-validate findings. Strong general capabilities.

- **GPT-4o Mini**: Best for simple fact-finding or when on a tight budget. Good enough for straightforward questions.

## 📖 Usage

1. **Enter the target website URL** (e.g., `https://company.com`)

2. **Add your research questions:**
   - What products/services does this company offer?
   - Who is the leadership team?
   - What is their pricing model?
   - What markets do they serve?
   - What technologies do they use?

3. **Select your AI model** based on your needs (see guide above)

4. **Configure advanced settings** (optional):
   - **Max Pages**: Limit how many pages to scrape (10-100)
   - **Max Depth**: How deep to crawl from the homepage (1-5)

5. **Start Research** and watch real-time progress

6. **Review your report** with:
   - Executive summary
   - Detailed findings per question
   - Source citations
   - Data gaps and recommendations

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React UI      │────▶│  FastAPI        │────▶│  LLM APIs       │
│   (Port 3000)   │     │  (Port 8000)    │     │  (Claude/GPT)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Web Scraper    │
                        │  (httpx + BS4)  │
                        └─────────────────┘
```

### Pipeline Stages:

1. **Scraping** - Crawls the target website, respecting depth limits
2. **Summarizing** - LLM generates concise summaries for each page
3. **Categorizing** - Maps content to research questions with relevance scores
4. **Reporting** - Produces final research report with citations

## 🔧 API Reference

### Start Research
```http
POST /research
Content-Type: application/json

{
  "website_url": "https://example.com",
  "questions": ["What products do they offer?"],
  "model": "claude-sonnet-4-20250514",
  "max_pages": 30,
  "max_depth": 2
}
```

### Check Status
```http
GET /research/{job_id}
```

### Get Available Models
```http
GET /models
```


### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes* | Your Anthropic API key |
| `OPENAI_API_KEY` | No | Your OpenAI API key (for GPT models) |
| `REACT_APP_API_URL` | No | Backend URL (default: http://localhost:8000) |

*At least one API key is required for the agent to function.

## 🛡️ Security Notes

- Never commit API keys to version control
- Use environment variables or secrets management
- Consider rate limiting in production
- The scraper respects `robots.txt` best practices

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a PR.

---

Built with ❤️ using Claude, FastAPI, and React

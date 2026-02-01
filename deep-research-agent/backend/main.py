"""
Deep Research Agent - Backend API
A powerful web scraping and analysis agent for company research
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Deep Research Agent API",
    description="Scrape websites, analyze content, and generate research reports",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for research jobs (use Redis/DB in production)
research_jobs = {}


class ResearchRequest(BaseModel):
    website_url: HttpUrl
    questions: list[str]
    model: str = "claude-sonnet-4-20250514"
    max_pages: int = 50
    max_depth: int = 3


class ResearchJob(BaseModel):
    id: str
    status: str
    website_url: str
    questions: list[str]
    model: str
    progress: dict
    pages_scraped: list[dict] = []
    summaries: list[dict] = []
    categorized_data: dict = {}
    report: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


# Model configurations with descriptions
MODEL_OPTIONS = {
    "claude-sonnet-4-20250514": {
        "name": "Claude Sonnet 4",
        "provider": "anthropic",
        "description": "Best balance of speed and intelligence. Ideal for most research tasks with excellent reasoning capabilities.",
        "use_case": "General research, balanced cost/performance",
        "context_window": 200000,
        "cost_tier": "medium"
    },
    "claude-opus-4-20250514": {
        "name": "Claude Opus 4",
        "provider": "anthropic",
        "description": "Most capable model for complex analysis. Superior at nuanced understanding and detailed report generation.",
        "use_case": "Complex research requiring deep analysis",
        "context_window": 200000,
        "cost_tier": "high"
    },
    "claude-haiku-4-20250514": {
        "name": "Claude Haiku 4",
        "provider": "anthropic",
        "description": "Fastest and most cost-effective. Great for quick summaries and high-volume processing.",
        "use_case": "Quick analysis, budget-conscious research",
        "context_window": 200000,
        "cost_tier": "low"
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "provider": "openai",
        "description": "OpenAI's flagship model. Strong general capabilities with good speed.",
        "use_case": "Alternative perspective, diverse analysis",
        "context_window": 128000,
        "cost_tier": "medium"
    },
    "gpt-4o-mini": {
        "name": "GPT-4o Mini",
        "provider": "openai",
        "description": "Lightweight OpenAI model. Fast and economical for simpler tasks.",
        "use_case": "Quick summaries, cost-sensitive workflows",
        "context_window": 128000,
        "cost_tier": "low"
    }
}


@app.get("/")
async def root():
    return {"message": "Deep Research Agent API", "version": "1.0.0"}


@app.get("/models")
async def get_models():
    """Get available LLM models with descriptions"""
    return MODEL_OPTIONS


@app.post("/research", response_model=dict)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start a new research job"""
    job_id = str(uuid.uuid4())

    job = ResearchJob(
        id=job_id,
        status="pending",
        website_url=str(request.website_url),
        questions=request.questions,
        model=request.model,
        progress={"stage": "initializing", "percent": 0, "message": "Starting research..."},
        created_at=datetime.utcnow().isoformat()
    )

    research_jobs[job_id] = job.model_dump()

    # Start background processing
    background_tasks.add_task(
        run_research_pipeline,
        job_id,
        str(request.website_url),
        request.questions,
        request.model,
        request.max_pages,
        request.max_depth
    )

    return {"job_id": job_id, "status": "started"}


@app.get("/research/{job_id}")
async def get_research_status(job_id: str):
    """Get the status of a research job"""
    if job_id not in research_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return research_jobs[job_id]


@app.delete("/research/{job_id}")
async def cancel_research(job_id: str):
    """Cancel a research job"""
    if job_id not in research_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    research_jobs[job_id]["status"] = "cancelled"
    return {"message": "Job cancelled"}


async def run_research_pipeline(
        job_id: str,
        website_url: str,
        questions: list[str],
        model: str,
        max_pages: int,
        max_depth: int
):
    """Main research pipeline"""
    try:
        # Update status
        update_job_progress(job_id, "scraping", 5, "Starting web scraping...")

        # Step 1: Scrape the website
        pages = await scrape_website(job_id, website_url, max_pages, max_depth)
        research_jobs[job_id]["pages_scraped"] = pages

        if not pages:
            raise Exception("No pages could be scraped from the website")

        update_job_progress(job_id, "summarizing", 30, f"Scraped {len(pages)} pages. Generating summaries...")

        # Step 2: Generate summaries for each page
        summaries = await generate_summaries(job_id, pages, model)
        research_jobs[job_id]["summaries"] = summaries

        update_job_progress(job_id, "categorizing", 60, "Categorizing content by questions...")

        # Step 3: Categorize content by questions
        categorized = await categorize_by_questions(job_id, summaries, questions, model)
        research_jobs[job_id]["categorized_data"] = categorized

        update_job_progress(job_id, "reporting", 80, "Generating final report...")

        # Step 4: Generate final report
        report = await generate_report(job_id, categorized, questions, website_url, model)
        research_jobs[job_id]["report"] = report

        # Complete
        research_jobs[job_id]["status"] = "completed"
        research_jobs[job_id]["progress"] = {"stage": "complete", "percent": 100, "message": "Research complete!"}
        research_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        research_jobs[job_id]["status"] = "failed"
        research_jobs[job_id]["error"] = str(e)
        research_jobs[job_id]["progress"] = {"stage": "error", "percent": 0, "message": str(e)}


def update_job_progress(job_id: str, stage: str, percent: int, message: str):
    """Update job progress"""
    if job_id in research_jobs:
        research_jobs[job_id]["progress"] = {
            "stage": stage,
            "percent": percent,
            "message": message
        }
        research_jobs[job_id]["status"] = "processing"


async def scrape_website(job_id: str, base_url: str, max_pages: int, max_depth: int) -> list[dict]:
    """Scrape website pages recursively"""
    visited = set()
    pages = []
    base_domain = urlparse(base_url).netloc

    async def scrape_page(url: str, depth: int):
        if depth > max_depth or len(pages) >= max_pages or url in visited:
            return

        visited.add(url)

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; DeepResearchAgent/1.0)"
                })

                if response.status_code != 200:
                    return

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    return

                soup = BeautifulSoup(response.text, "html.parser")

                # Remove script and style elements
                for element in soup(["script", "style", "nav", "footer", "header"]):
                    element.decompose()

                # Extract text content
                text = soup.get_text(separator="\n", strip=True)

                # Get title
                title = soup.title.string if soup.title else url

                # Get meta description
                meta_desc = ""
                meta_tag = soup.find("meta", attrs={"name": "description"})
                if meta_tag:
                    meta_desc = meta_tag.get("content", "")

                pages.append({
                    "url": url,
                    "title": title,
                    "meta_description": meta_desc,
                    "content": text[:50000],  # Limit content size
                    "depth": depth
                })

                update_job_progress(
                    job_id, "scraping",
                    min(25, 5 + len(pages)),
                    f"Scraped {len(pages)} pages..."
                )

                # Find links to follow
                if depth < max_depth:
                    links = soup.find_all("a", href=True)
                    tasks = []

                    for link in links:
                        href = link["href"]
                        full_url = urljoin(url, href)
                        parsed = urlparse(full_url)

                        # Only follow links on same domain
                        if parsed.netloc == base_domain and full_url not in visited:
                            # Skip common non-content pages
                            skip_patterns = ["login", "signup", "cart", "checkout", "#", "javascript:", "mailto:"]
                            if not any(p in full_url.lower() for p in skip_patterns):
                                tasks.append(scrape_page(full_url, depth + 1))

                    if tasks:
                        await asyncio.gather(*tasks[:10])  # Limit concurrent requests

        except Exception as e:
            print(f"Error scraping {url}: {e}")

    await scrape_page(base_url, 0)
    return pages


async def generate_summaries(job_id: str, pages: list[dict], model: str) -> list[dict]:
    """Generate summaries for each page using LLM"""
    summaries = []
    model_config = MODEL_OPTIONS.get(model, MODEL_OPTIONS["claude-sonnet-4-20250514"])

    for i, page in enumerate(pages):
        try:
            summary = await call_llm(
                model=model,
                provider=model_config["provider"],
                system="You are a research assistant. Summarize the webpage content concisely, focusing on key information, facts, and data points. Keep summaries under 500 words.",
                prompt=f"""Summarize this webpage:

Title: {page['title']}
URL: {page['url']}

Content:
{page['content'][:10000]}

Provide a concise summary highlighting:
1. Main topic/purpose
2. Key facts and data points
3. Important details or claims
"""
            )

            summaries.append({
                "url": page["url"],
                "title": page["title"],
                "summary": summary,
                "original_length": len(page["content"])
            })

            progress = 30 + int((i / len(pages)) * 30)
            update_job_progress(job_id, "summarizing", progress, f"Summarized {i + 1}/{len(pages)} pages...")

        except Exception as e:
            summaries.append({
                "url": page["url"],
                "title": page["title"],
                "summary": f"Error generating summary: {str(e)}",
                "original_length": len(page["content"])
            })

    return summaries


async def categorize_by_questions(
        job_id: str,
        summaries: list[dict],
        questions: list[str],
        model: str
) -> dict:
    """Categorize page summaries by relevance to each question"""
    model_config = MODEL_OPTIONS.get(model, MODEL_OPTIONS["claude-sonnet-4-20250514"])

    # Prepare summaries text
    summaries_text = "\n\n".join([
        f"Page: {s['title']}\nURL: {s['url']}\nSummary: {s['summary']}"
        for s in summaries
    ])

    questions_text = "\n".join([f"{i + 1}. {q}" for i, q in enumerate(questions)])

    categorization_prompt = f"""Analyze these webpage summaries and categorize them by relevance to each research question.

RESEARCH QUESTIONS:
{questions_text}

WEBPAGE SUMMARIES:
{summaries_text}

For each question, identify:
1. Which pages are most relevant
2. Key information from those pages that answers or relates to the question
3. A confidence score (high/medium/low) for the available information

Respond in JSON format:
{{
    "questions": [
        {{
            "question": "question text",
            "relevant_pages": [
                {{
                    "url": "page url",
                    "title": "page title", 
                    "relevance": "high/medium/low",
                    "key_info": "extracted relevant information"
                }}
            ],
            "summary": "overall summary of findings for this question",
            "confidence": "high/medium/low",
            "data_gaps": "what information is missing or unclear"
        }}
    ]
}}
"""

    try:
        response = await call_llm(
            model=model,
            provider=model_config["provider"],
            system="You are a research analyst. Categorize and analyze content with precision. Always respond with valid JSON.",
            prompt=categorization_prompt
        )

        # Parse JSON response
        # Find JSON in response
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            categorized = json.loads(response[json_start:json_end])
        else:
            categorized = {"questions": [], "error": "Could not parse categorization"}

    except json.JSONDecodeError:
        categorized = {"questions": [], "raw_response": response}
    except Exception as e:
        categorized = {"questions": [], "error": str(e)}

    return categorized


async def generate_report(
        job_id: str,
        categorized: dict,
        questions: list[str],
        website_url: str,
        model: str
) -> str:
    """Generate final research report"""
    model_config = MODEL_OPTIONS.get(model, MODEL_OPTIONS["claude-sonnet-4-20250514"])

    report_prompt = f"""Generate a comprehensive research report based on the analysis of {website_url}.

RESEARCH QUESTIONS:
{chr(10).join([f'{i + 1}. {q}' for i, q in enumerate(questions)])}

CATEGORIZED FINDINGS:
{json.dumps(categorized, indent=2)}

Create a professional research report with:
1. Executive Summary - Key findings overview
2. Methodology - Brief description of analysis approach
3. Detailed Findings - Section for each question with:
   - Direct answer to the question
   - Supporting evidence from scraped pages
   - Confidence level and data quality assessment
4. Data Gaps & Limitations - What information was not found
5. Recommendations - Suggested follow-up research or actions

Use clear formatting with headers and bullet points where appropriate.
Cite specific pages/URLs when referencing information.
"""

    report = await call_llm(
        model=model,
        provider=model_config["provider"],
        system="You are a senior research analyst. Write clear, professional reports with actionable insights. Use markdown formatting.",
        prompt=report_prompt
    )

    return report


async def call_llm(model: str, provider: str, system: str, prompt: str) -> str:
    """Call LLM API based on provider"""

    if provider == "anthropic":
        return await call_anthropic(model, system, prompt)
    elif provider == "openai":
        return await call_openai(model, system, prompt)
    else:
        raise ValueError(f"Unknown provider: {provider}")


async def call_anthropic(model: str, system: str, prompt: str) -> str:
    """Call Anthropic API"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        # Return mock response for demo
        return f"[Demo Mode - Set ANTHROPIC_API_KEY for real responses]\n\nThis is a placeholder summary for the content. In production, Claude would analyze the content and provide detailed insights."

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": model,
                "max_tokens": 4096,
                "system": system,
                "messages": [{"role": "user", "content": prompt}]
            }
        )

        if response.status_code != 200:
            raise Exception(f"Anthropic API error: {response.text}")

        data = response.json()
        return data["content"][0]["text"]


async def call_openai(model: str, system: str, prompt: str) -> str:
    """Call OpenAI API"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return f"[Demo Mode - Set OPENAI_API_KEY for real responses]\n\nThis is a placeholder summary."

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 4096
            }
        )

        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.text}")

        data = response.json()
        return data["choices"][0]["message"]["content"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

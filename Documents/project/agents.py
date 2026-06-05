"""
agents.py — The 3-agent research swarm
Planner → Researcher → Synthesizer
"""

import os
import json
import httpx
from dataclasses import dataclass
from typing import AsyncGenerator, Any
from dotenv import load_dotenv

from autogen_core.models import ModelFamily
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient, OpenAIChatCompletionClient

load_dotenv()


@dataclass(frozen=True)
class OpenAICompatibleProvider:
    model: str
    api_key: str
    base_url: str | None = None


PLACEHOLDER_PREFIXES = ("your-", "provider-", "not-needed")
SUPPORTED_LLM_PROVIDERS = {
    "azure",
    "openai",
    "github",
    "huggingface",
    "openrouter",
    "groq",
    "together",
    "fireworks",
    "local",
    "custom",
}
SUPPORTED_SEARCH_PROVIDERS = {"auto", "bing", "tavily", "serper", "brave", "none"}


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return not normalized or normalized.startswith(PLACEHOLDER_PREFIXES)


def _env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or _is_placeholder(value):
        return None
    return value


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _first_env(*names: str) -> str:
    for name in names:
        value = _env(name)
        if value:
            return value
    raise RuntimeError(f"Missing required environment variable. Set one of: {', '.join(names)}")


def _openai_compatible_config(provider: str) -> OpenAICompatibleProvider:
    if provider == "openai":
        return OpenAICompatibleProvider(
            model=_env("OPENAI_MODEL") or "gpt-4o-mini",
            api_key=_first_env("OPENAI_API_KEY"),
        )

    if provider == "github":
        return OpenAICompatibleProvider(
            model=_env("GITHUB_MODELS_MODEL") or "openai/gpt-4.1",
            base_url=_env("GITHUB_MODELS_BASE_URL") or "https://models.github.ai/inference",
            api_key=_first_env("GITHUB_TOKEN", "GITHUB_MODELS_API_KEY"),
        )

    if provider == "huggingface":
        return OpenAICompatibleProvider(
            model=_env("HUGGINGFACE_MODEL") or "meta-llama/Llama-3.1-8B-Instruct",
            base_url=_env("HUGGINGFACE_BASE_URL") or "https://router.huggingface.co/v1",
            api_key=_first_env("HUGGINGFACE_API_KEY", "HF_TOKEN"),
        )

    if provider == "local":
        return OpenAICompatibleProvider(
            model=_env("LOCAL_MODEL") or _first_env("OPENAI_COMPATIBLE_MODEL"),
            base_url=_env("LOCAL_BASE_URL") or _first_env("OPENAI_COMPATIBLE_BASE_URL"),
            api_key=_env("LOCAL_API_KEY") or _env("OPENAI_COMPATIBLE_API_KEY") or "local",
        )

    if provider in {"openrouter", "groq", "together", "fireworks", "custom"}:
        prefix = provider.upper()
        return OpenAICompatibleProvider(
            model=_first_env(f"{prefix}_MODEL", "OPENAI_COMPATIBLE_MODEL"),
            base_url=_first_env(f"{prefix}_BASE_URL", "OPENAI_COMPATIBLE_BASE_URL"),
            api_key=_first_env(f"{prefix}_API_KEY", "OPENAI_COMPATIBLE_API_KEY"),
        )

    raise RuntimeError(
        "Unsupported LLM_PROVIDER. Use azure, openai, github, huggingface, "
        "openrouter, groq, together, fireworks, local, or custom."
    )


def _model_info() -> dict:
    return {
        "vision": _env_bool("LLM_SUPPORTS_VISION", False),
        "function_calling": _env_bool("LLM_SUPPORTS_FUNCTION_CALLING", False),
        "json_output": _env_bool("LLM_SUPPORTS_JSON_OUTPUT", True),
        "family": os.getenv("LLM_MODEL_FAMILY", ModelFamily.UNKNOWN),
    }


# ── LLM client (shared) ──────────────────────────────────────────────────────
def get_model_client() -> AzureOpenAIChatCompletionClient | OpenAIChatCompletionClient:
    provider = (_env("LLM_PROVIDER") or "azure").lower()

    if provider == "azure":
        return AzureOpenAIChatCompletionClient(
            azure_deployment=_first_env("AZURE_OPENAI_DEPLOYMENT"),
            model=_env("AZURE_OPENAI_MODEL") or "gpt-4o",
            api_version=_first_env("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=_first_env("AZURE_OPENAI_ENDPOINT"),
            api_key=_first_env("AZURE_OPENAI_API_KEY"),
        )

    config = _openai_compatible_config(provider)
    kwargs = {
        "model": config.model,
        "api_key": config.api_key,
        "model_info": _model_info(),
    }
    if config.base_url:
        kwargs["base_url"] = config.base_url

    return OpenAIChatCompletionClient(**kwargs)


def _active_search_provider() -> str:
    provider = (_env("SEARCH_PROVIDER") or "auto").lower()
    if provider not in SUPPORTED_SEARCH_PROVIDERS:
        raise RuntimeError(
            "Unsupported SEARCH_PROVIDER. Use auto, bing, tavily, serper, brave, or none."
        )

    if provider != "auto":
        return provider

    if _env("BING_SEARCH_API_KEY"):
        return "bing"
    if _env("TAVILY_API_KEY"):
        return "tavily"
    if _env("SERPER_API_KEY"):
        return "serper"
    if _env("BRAVE_SEARCH_API_KEY"):
        return "brave"
    return "none"


def _result(title: str, url: str, snippet: str) -> dict[str, str]:
    return {"title": title, "url": url, "snippet": snippet}


# ── Web search tools ─────────────────────────────────────────────────────────
async def bing_search(query: str, count: int = 5) -> list[dict[str, str]]:
    """Search the web via Bing."""
    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": _first_env("BING_SEARCH_API_KEY")}
    params = {"q": query, "count": count, "responseFilter": "Webpages"}

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

    pages = data.get("webPages", {}).get("value", [])
    return [_result(p.get("name", ""), p.get("url", ""), p.get("snippet", "")) for p in pages]


async def tavily_search(query: str, count: int = 5) -> list[dict[str, str]]:
    """Search the web via Tavily."""
    headers = {"Authorization": f"Bearer {_first_env('TAVILY_API_KEY')}"}
    payload = {"query": query, "max_results": count, "search_depth": "basic"}

    async with httpx.AsyncClient() as client:
        resp = await client.post("https://api.tavily.com/search", headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()

    return [
        _result(item.get("title", ""), item.get("url", ""), item.get("content", ""))
        for item in data.get("results", [])
    ]


async def serper_search(query: str, count: int = 5) -> list[dict[str, str]]:
    """Search the web via Serper."""
    headers = {"X-API-KEY": _first_env("SERPER_API_KEY"), "Content-Type": "application/json"}
    payload = {"q": query, "num": count}

    async with httpx.AsyncClient() as client:
        resp = await client.post("https://google.serper.dev/search", headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()

    return [
        _result(item.get("title", ""), item.get("link", ""), item.get("snippet", ""))
        for item in data.get("organic", [])
    ]


async def brave_search(query: str, count: int = 5) -> list[dict[str, str]]:
    """Search the web via Brave Search."""
    headers = {"Accept": "application/json", "X-Subscription-Token": _first_env("BRAVE_SEARCH_API_KEY")}
    params = {"q": query, "count": count}

    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.search.brave.com/res/v1/web/search", headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

    return [
        _result(item.get("title", ""), item.get("url", ""), item.get("description", ""))
        for item in data.get("web", {}).get("results", [])
    ]


async def web_search(query: str, count: int = 5) -> list[dict[str, str]]:
    provider = _active_search_provider()
    if provider == "none":
        return []
    if provider == "bing":
        return await bing_search(query, count)
    if provider == "tavily":
        return await tavily_search(query, count)
    if provider == "serper":
        return await serper_search(query, count)
    if provider == "brave":
        return await brave_search(query, count)
    raise RuntimeError(f"Unsupported search provider: {provider}")


def config_status() -> dict[str, Any]:
    llm_provider = (_env("LLM_PROVIDER") or "azure").lower()
    requested_search_provider = (_env("SEARCH_PROVIDER") or "auto").lower()
    search_provider = _active_search_provider()
    issues = []
    warnings = []

    if llm_provider not in SUPPORTED_LLM_PROVIDERS:
        issues.append(f"Unsupported LLM_PROVIDER: {llm_provider}")
    else:
        try:
            if llm_provider == "azure":
                for name in (
                    "AZURE_OPENAI_DEPLOYMENT",
                    "AZURE_OPENAI_API_VERSION",
                    "AZURE_OPENAI_ENDPOINT",
                    "AZURE_OPENAI_API_KEY",
                ):
                    _first_env(name)
            else:
                _openai_compatible_config(llm_provider)
        except RuntimeError as exc:
            issues.append(str(exc))

    if search_provider == "none" and requested_search_provider == "auto":
        issues.append(
            "No search API key configured. Set SEARCH_PROVIDER=none to run without web search, "
            "or add BING_SEARCH_API_KEY, TAVILY_API_KEY, SERPER_API_KEY, or BRAVE_SEARCH_API_KEY."
        )
    elif search_provider == "none":
        warnings.append("Search is disabled. Answers will rely on the model's existing knowledge.")

    return {
        "ok": not issues,
        "llm_provider": llm_provider,
        "search_provider": search_provider,
        "issues": issues,
        "warnings": warnings,
    }


# ── Agent definitions ─────────────────────────────────────────────────────────
def make_planner(model_client: AzureOpenAIChatCompletionClient | OpenAIChatCompletionClient) -> AssistantAgent:
    return AssistantAgent(
        name="Planner",
        model_client=model_client,
        system_message="""You are the Planner agent in a research swarm.

Your job: take the user's research question and break it into exactly 3 focused 
sub-questions that together will produce a comprehensive answer.

Output ONLY valid JSON in this format — nothing else:
{
  "original_question": "<the user's question>",
  "subtasks": [
    {"id": 1, "query": "<focused sub-question 1>"},
    {"id": 2, "query": "<focused sub-question 2>"},
    {"id": 3, "query": "<focused sub-question 3>"}
  ]
}

Make the sub-questions specific, distinct, and searchable.""",
    )


def make_researcher(model_client: AzureOpenAIChatCompletionClient | OpenAIChatCompletionClient) -> AssistantAgent:
    return AssistantAgent(
        name="Researcher",
        model_client=model_client,
        system_message="""You are the Researcher agent in a research swarm.

You receive a focused query and web search results.
Read the results carefully and extract the most relevant facts, figures, and insights.

Output ONLY valid JSON in this format:
{
  "query": "<the query you researched>",
  "findings": [
    {"point": "<key finding>", "source": "<url>"},
    ...
  ],
  "summary": "<2-3 sentence summary of what you found>"
}""",
    )


def make_synthesizer(model_client: AzureOpenAIChatCompletionClient | OpenAIChatCompletionClient) -> AssistantAgent:
    return AssistantAgent(
        name="Synthesizer",
        model_client=model_client,
        system_message="""You are the Synthesizer agent in a research swarm.

You receive the original question and findings from 3 research tasks.
Produce a comprehensive, well-structured answer.

Output ONLY valid JSON in this format:
{
  "question": "<original question>",
  "answer": "<full markdown answer with headers and bullet points>",
  "key_takeaways": ["<takeaway 1>", "<takeaway 2>", "<takeaway 3>"],
  "sources": ["<url1>", "<url2>", "..."]
}""",
    )


# ── Swarm orchestration ───────────────────────────────────────────────────────
async def run_swarm(question: str) -> AsyncGenerator[dict, None]:
    """
    Orchestrate the 3-agent pipeline and yield status events.
    Each event is a dict that gets sent to the frontend via WebSocket/SSE.
    """
    model_client = get_model_client()

    planner = make_planner(model_client)
    researcher = make_researcher(model_client)
    synthesizer = make_synthesizer(model_client)

    # ── Step 1: Planner ───────────────────────────────────────────────────────
    yield {"agent": "Planner", "status": "running", "message": "Breaking down your question..."}

    planner_result = await planner.run(
        task=f"Research question: {question}"
    )
    planner_text = planner_result.messages[-1].content

    try:
        plan = json.loads(planner_text)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", planner_text, re.DOTALL)
        if match:
            try:
                plan = json.loads(match.group())
            except json.JSONDecodeError:
                plan = {"subtasks": []}
        else:
            plan = {"subtasks": []}

    yield {
        "agent": "Planner",
        "status": "done",
        "message": "Plan created",
        "data": plan,
    }

    # ── Step 2: Researcher (3 sub-tasks) ──────────────────────────────────────
    all_findings = []

    for subtask in plan.get("subtasks", []):
        query = subtask.get("query", "")
        yield {
            "agent": "Researcher",
            "status": "running",
            "message": f"Researching: {query}",
            "subtask_id": subtask.get("id"),
        }

        search_results = await web_search(query)
        research_result = await researcher.run(
            task=json.dumps({"query": query, "search_results": search_results}, indent=2)
        )
        research_text = research_result.messages[-1].content

        try:
            findings = json.loads(research_text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"\{.*\}", research_text, re.DOTALL)
            if match:
                try:
                    findings = json.loads(match.group())
                except json.JSONDecodeError:
                    findings = {"query": query, "findings": [], "summary": ""}
            else:
                findings = {"query": query, "findings": [], "summary": ""}

        all_findings.append(findings)

        yield {
            "agent": "Researcher",
            "status": "done",
            "message": f"Found {len(findings.get('findings', []))} insights",
            "subtask_id": subtask.get("id"),
            "data": findings,
        }

    # ── Step 3: Synthesizer ───────────────────────────────────────────────────
    yield {"agent": "Synthesizer", "status": "running", "message": "Synthesizing all findings..."}

    synth_input = json.dumps({
        "original_question": question,
        "research_results": all_findings,
    }, indent=2)

    synth_result = await synthesizer.run(task=synth_input)
    synth_text = synth_result.messages[-1].content

    try:
        synthesis = json.loads(synth_text)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", synth_text, re.DOTALL)
        if match:
            try:
                synthesis = json.loads(match.group())
            except json.JSONDecodeError:
                synthesis = {"answer": synth_text, "key_takeaways": [], "sources": []}
        else:
            synthesis = {"answer": synth_text, "key_takeaways": [], "sources": []}

    yield {
        "agent": "Synthesizer",
        "status": "done",
        "message": "Answer ready",
        "data": synthesis,
    }

    yield {"agent": "system", "status": "complete", "message": "Research complete"}

import logging

from ddgs import DDGS
from func_timeout import FunctionTimedOut, func_timeout
import trafilatura
from pytick.llm.llm_types import State
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage

from pytick.utility.utility import get_logger

logger = get_logger(__file__, logging.DEBUG)


def __duck_duck_go_search(query, max_results: int = 10) -> list[dict]:
    # 1. Search for news snippets
    with DDGS() as ddgs:
        # 'region' 'in-en' is for India, 'wt-wt' is worldwide
        search_results = list(
            ddgs.text(query, region="in-en", max_results=max_results))

        if not search_results:
            return [{"body": "I couldn't find any recent news on that topic."}]

        return search_results  # 'date', 'title', 'body', 'url', 'image', 'source'


def __fetch_url_content(url: str) -> str:
    """Fetch main content from a URL using trafilatura."""
    try:
        def _fetch():
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return ""
            content = trafilatura.extract(
                downloaded, include_comments=False, favor_precision=True)
            return content[:3000] if content else ""
        return _fetch()
    except FunctionTimedOut:
        logger.warning(f"Timeout fetching {url}")
        return ""
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return ""


def __local_chat_reply(query: str, messages: list, llm: BaseChatModel) -> str:
    """Generate a concise helper reply using local Ollama model and full web content."""
    search_text_parts = []
    web_search_reply = __duck_duck_go_search(query, max_results=10)
    # Fetch full content from each URL
    max_results = 0
    for item in web_search_reply:
        url = item.get('href', '').strip()
        title = item.get('title', '').strip()
        body = item.get('body', '').strip()

        # Try to fetch full content
        full_content = ""
        if url:
            try:
                full_content = func_timeout(
                    2, __fetch_url_content, args=(url,))
            except FunctionTimedOut:
                logger.warning(f"Timeout fetching {url}")
                full_content = ""
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                full_content = ""
        if full_content:
            # Use full content if available, otherwise use snippet
            content_to_use = full_content if full_content else body

            if title or content_to_use:
                part = f"Title: {title}\n  Content: {content_to_use[:1500]}\n  URL: {url}"
                search_text_parts.append(part)
            max_results += 1
        if max_results >= 2:  # Limit to top 2 results to avoid overwhelming the model
            break

    search_text = "\n".join(search_text_parts)
    if search_text == "":
        search_text = f"No content found"

    messages = [SystemMessage(
        f"Web search results for the query:\n\n{search_text}"), *messages]
    try:
        response = llm.invoke(messages)
        return str(response.content)
    except Exception as e:
        logger.warning(f"Local chat reply failed: {e}")
        return f"Failed: {query}"


def converter_agent(state: State, llm: BaseChatModel) -> State:
    """Make a web search query based on the user input and system prompt."""
    messages = state.get('messages', [])
    retry_count = state.get("retry_count", 0)
    if retry_count == 0:
        system_msg = SystemMessage(content=state.get('system_prompt', ''))
        user_input = None
        for msg in messages:
            if hasattr(msg, 'type') and msg.type == 'human':
                user_input = msg
                break

        if not user_input:
            return state
        messages = [system_msg, user_input]

        llm_reply = __local_chat_reply(
            query=user_input.content, messages=messages, llm=llm)
        return State(
            messages=[AIMessage(content=llm_reply)] + messages,
            message_type="valid",
            errors=[],
            retry_count=state.get("retry_count", 0) + 1
        )
    elif retry_count > 0:
        return State(
            message_type="invalid",
            errors=[],
            retry_count=state.get("retry_count", 0) + 1
        )

    # def __simple_google_search(self, query: str, max_results: int = 10) -> list[dict]:
    #     """Fetch context using GoogleNews library (more stable than scraping)."""
    #     if not query.strip():
    #         return []

    #     gn = GoogleNews(lang='en', country='US')
    #     res = gn.search(query, when='1d')  # or '7d', '1h', etc.

    #     entries = res.get('entries', [])
    #     results = []

    #     for entry in entries[:max_results]:
    #         title = (entry.get('title') or "").strip()
    #         url = (entry.get('link') or "").strip()
    #         snippet = (entry.get('summary') or "").strip()
    #         if not title and not snippet:
    #             continue
    #         results.append(
    #             {
    #                 "title": title,
    #                 "url": url,
    #                 "body": snippet,
    #             }
    #         )

    #     return results

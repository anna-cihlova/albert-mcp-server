from mcp.server.fastmcp import FastMCP
import feedparser
import requests
from datetime import datetime
from typing import Optional

# Feed Config
NEWS_FEEDS = {
    "huggingface": "https://huggingface.co/blog/feed",
    "kdnuggets": "https://www.kdnuggets.com/feed",
    "openai": "https://openai.com/blog/rss",
    "towardsai": "https://towardsai.net/feed",
    "googleai": "blog.google/technology/ai/rss/"
}

PODCAST_FEEDS = {
    "everydayai": "https://rss.buzzsprout.com/2175779.rss",
}

PUBLICATION_FEEDS = {
    "arxiv": "https://export.arxiv.org/rss/cs.AI",
}

# MCP Server
mcp = FastMCP("Morning Albert")

# Tools
@mcp.tool()
def get_ai_podcasts(max_items: int = 5) -> list[str]:
    """Fetch latest AI podcast episodes with transcripts if available, otherwise summaries."""

    episodes = []

    for feed_url in PODCAST_FEEDS.values():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:max_items]:
            pub_date = (
                datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
                if hasattr(entry, "published_parsed")
                else "Unknown date"
            )
            title = getattr(entry, "title", "No title")

            # Try to find transcript field
            transcript = None
            if hasattr(entry, "transcript"):
                transcript = entry.transcript
            elif hasattr(entry, "links"):
                # Some feeds provide transcript as a link
                for link in entry.links:
                    if link.get("rel") == "transcript" or "transcript" in link.get("type", ""):
                        transcript = f"Transcript available here: {link.get('href')}"
                        break

            # Fallback to summary
            summary = getattr(entry, "summary", "").strip()
            text = transcript if transcript else (summary if summary else "No summary available")

            # Safe link handling
            link = getattr(entry, "link", None)
            if not link:
                if hasattr(entry, "enclosures") and entry.enclosures:
                    # Only try if enclosures is non-empty
                    link = entry.enclosures[0].get("url", "No link available")
                else:
                    link = "No link available"

            formatted = f"- **{title}** ({pub_date}) → {link}\n  🎧 {text[:640]}..."
            episodes.append(formatted)

    return episodes if episodes else ["No new podcast episodes found."]



@mcp.tool()
def get_ai_news(today_only: bool = True, max_items: int = 20) -> list[str]:
    """Fetch AI-related news (default: all published today). Includes summaries if available."""

    news_items = []

    for feed_url in NEWS_FEEDS.values():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            # Parse publication date
            if hasattr(entry, "published_parsed"):
                pub_date = datetime(*entry.published_parsed[:6]).date()
                pub_date_str = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M")
            else:
                pub_date = None
                pub_date_str = "Unknown date"

            author = getattr(entry, "author", "Unknown author")
            summary = getattr(entry, "summary", "").strip()

            if not today_only or (pub_date and pub_date == datetime.utcnow().date()):
                formatted = f"- **{entry.title}** by {author} ({pub_date_str}) → {entry.link}"
                if summary:
                    formatted += f"\n  📝 {summary[:220]}..."  # keep it short
                news_items.append(formatted)

    return news_items[:max_items] if news_items else ["No AI news found today."]


@mcp.tool()
def check_new_ai_pubs(today_only: bool = True, max_items: int = 8) -> list[str]:
    """Check AI research publications (default: today only)."""

    papers = []
    today = datetime.utcnow().date()

    for feed_url in PUBLICATION_FEEDS.values():
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            pub_date = datetime(*entry.published_parsed[:6]).date() if hasattr(entry, "published_parsed") else None
            pub_date_str = pub_date.strftime("%Y-%m-%d") if pub_date else "Unknown date"

            authors = ", ".join([a.name for a in getattr(entry, "authors", [])]) if hasattr(entry, "authors") else "Unknown authors"

            if not today_only or (pub_date and pub_date == today):
                papers.append(f"- {entry.title} by {authors} ({pub_date_str}) → {entry.link}")

    return papers if papers else ["No new AI publications today."]


@mcp.tool()
def suggest_case_studies(max_items: int = 8) -> list[str]:
    """Suggest case studies to explore (from Hugging Face + KDNuggets)."""

    case_studies = []

    # Hugging Face case studies (static link list for now)
    case_studies.append("https://huggingface.co/blog?tag=case-studies")

    # KDNuggets articles
    case_studies.append("https://www.kdnuggets.com/")

    return case_studies[:max_items]


@mcp.tool()
def daily_digest(name: Optional[str] = None) -> str:
    """Full daily update: greeting, AI news, publications, and case studies."""

    greeting = f"👋 Good morning, {name}!\n" if name else "👋 Good morning!\n"

    episodes = get_ai_podcasts(today_only=True)
    news = get_ai_news(today_only=True)
    pubs = check_new_ai_pubs(today_only=True)
    case_studies = suggest_case_studies(max_items=8)

    formatted = greeting
    formatted += "\n📰 AI Podcasts' Summary (Today):\n" + "\n".join(episodes) + "\n"
    formatted += "\n📰 AI News (Today):\n" + "\n".join(news) + "\n"
    formatted += "\n📚 Publications (Today):\n" + "\n".join(pubs) + "\n"
    formatted += "\n💡 Case Studies:\n" + "\n".join(case_studies) + "\n"

    return formatted

# Main
def main():
    mcp.run()

if __name__ == "__main__":
    main()

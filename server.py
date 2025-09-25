from mcp.server.fastmcp import FastMCP
import feedparser, random, requests
from typing import Optional
from datetime import datetime

# MCP server name
mcp = FastMCP("Morning Albert")

# RSS feeds for AI news
AI_FEEDS = {
    "huggingface": "https://huggingface.co/blog/feed.xml",
    "openai": "https://openai.com/blog/rss/",
    "towardsai": "https://towardsai.net/feed",
    "wiz": "https://www.wiz.io/blog/rss.xml",
    "arxiv": "https://export.arxiv.org/rss/cs.AI"
}

# Get AI News
@mcp.tool()
def get_ai_news(source: str = "huggingface", max_items: int = 5, today_only: bool = True) -> list[str]:
    """Fetch the latest AI news with author and date."""

    if source not in AI_FEEDS:
        return [f"Unknown source {source}. Options: {list(AI_FEEDS.keys())}"]

    feed = feedparser.parse(AI_FEEDS[source])
    today = datetime.utcnow().date()
    items = []

    for entry in feed.entries:
        # Date
        pub_date_str = "Unknown date"
        pub_date = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6])
            pub_date_str = pub_date.strftime("%Y-%m-%d %H:%M")

        # Author
        author = getattr(entry, "author", "Unknown author")

        # Filter by today if needed
        if not today_only or (pub_date and pub_date.date() == today):
            items.append(f"- {entry.title} by {author} ({pub_date_str}) → {entry.link}")

        if len(items) >= max_items:
            break

    return items if items else ["No new AI news today."]


# Check new AI publications
@mcp.tool()
def check_new_ai_pubs(today_only: bool = True) -> list[str]:
    """Check ArXiv AI papers published today, with author(s) and date."""

    feed = feedparser.parse(AI_FEEDS["arxiv"])
    today = datetime.utcnow().date()
    papers = []

    for entry in feed.entries:
        pub_date = datetime(*entry.published_parsed[:6]).date()
        pub_date_str = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M")

        authors = ", ".join([a.name for a in getattr(entry, "authors", [])]) if hasattr(entry, "authors") else "Unknown authors"

        if not today_only or pub_date == today:
            papers.append(f"- {entry.title} by {authors} ({pub_date_str}) → {entry.link}")

    return papers if papers else ["No new AI publications today."]


# Suggest projects from news
@mcp.tool()
def suggest_projects_from_news(max_projects: int = 3) -> list[str]:
    """Suggest project ideas based on latest AI news/papers, with GitHub repos."""

    # Grab headlines from Hugging Face + ArXiv
    hf = feedparser.parse(AI_FEEDS["huggingface"]).entries[:5]
    ax = feedparser.parse(AI_FEEDS["arxiv"]).entries[:5]
    headlines = [e.title for e in hf + ax]

    if not headlines:
        return ["No news available."]

    random.shuffle(headlines)
    projects = []

    for h in headlines[:max_projects]:
        # Query GitHub API for related repos
        query = h.split()[0]  # crude: first word of headline
        github_url = f"https://api.github.com/search/repositories?q={query}+AI&sort=stars&order=desc"

        try:
            resp = requests.get(github_url, timeout=5).json()
            repo = resp["items"][0]["html_url"] if "items" in resp and resp["items"] else "No repo found"
        except:
            repo = "No repo found"

        projects.append(f"- Build a project inspired by: {h}\n  Resource: {repo}")

    return projects


# Daily Digest
@mcp.tool()
def daily_digest(name: Optional[str] = None) -> str:
    """Morning Albert: Full daily update with greeting, AI news, pubs, and projects."""
    if name:
        greeting = f"👋 Good morning, {name}!\n"
    else:
        greeting = "👋 Good morning!\n"

    news = get_ai_news(max_items=3, today_only=True)
    pubs = check_new_ai_pubs(today_only=True)
    projects = suggest_projects_from_news(max_projects=3)

    formatted = greeting
    formatted += "\n📰 AI News:\n" + "\n".join(news) + "\n"
    formatted += "\n📚 New Publications:\n" + "\n".join(pubs) + "\n"
    formatted += "\n💡 Project Ideas:\n" + "\n".join(projects) + "\n"

    return formatted

def main():
    mcp.run()

if __name__ == "__main__":
    main()

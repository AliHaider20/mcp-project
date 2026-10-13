import os 
import requests
from typing import Any

# Disable FastMCP's update check before importing FastMCP.
os.environ["FASTMCP_CHECK_FOR_UPDATES"] = "off"

from fastmcp import FastMCP
from typing import Optional

mcp = FastMCP("World news")

api_key = "adbc856225584ea083388dafdb382bd1"

@mcp.tool
def top_news(source_country: str, language: str, date: str, max_news_per_cluster: int = 1, headines_only: Optional[bool] = None) -> dict[str, Any]:
    """Returns the latest world news updates for a given source country, date, and language."""
    url = f"https://api.worldnewsapi.com/top-news?source-country={source_country}&language={language}&date={date}&max-news-per-cluster={max_news_per_cluster}"
    
    headers = {
        'x-api-key': api_key
    }
    print(url)

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"News API returned status {response.status_code}"}


# print(top_news("us", "en", "2024-05-29", api_key))

if __name__ == "__main__":
    mcp.run()
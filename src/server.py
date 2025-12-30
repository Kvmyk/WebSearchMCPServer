import asyncio
import logging
from typing import Any, Sequence
import json
import urllib.parse
import re

from mcp.server import Server
from mcp.server.sse import SseServerTransport
import mcp.types as types

# Local web scraping and content extraction
import httpx
from bs4 import BeautifulSoup
import trafilatura

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_server")

# Initialize MCP Server
server = Server("web-search")

# Initialize SSE Transport
sse_transport = SseServerTransport("/messages")

def extract_page_content(url: str, timeout: float = 10.0) -> dict:
    """Extract main content from a web page using trafilatura.
    
    Returns dict with: title, description, content (main text)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text
        
        # Extract main content using trafilatura
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            with_metadata=True,
            output_format='json'
        )
        
        if extracted:
            data = json.loads(extracted)
            return {
                'title': data.get('title', 'No title'),
                'description': data.get('description', '')[:300],  # First 300 chars
                'content': data.get('text', '')[:800]  # First 800 chars of main content
            }
        
        # Fallback: use BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('title')
        meta_desc = soup.find('meta', {'name': 'description'})
        
        # Get first paragraph
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text(strip=True) for p in paragraphs[:3]])[:800]
        
        return {
            'title': title.get_text(strip=True) if title else 'No title',
            'description': meta_desc.get('content', '')[:300] if meta_desc else '',
            'content': content
        }
        
    except Exception as e:
        logger.warning(f"Failed to extract content from {url}: {e}")
        return {
            'title': 'Content extraction failed',
            'description': '',
            'content': f'Error: {str(e)[:200]}'
        }

async def perform_search(query: str, max_results: int = 5, region: str = "wt-wt", timelimit: str | None = None) -> str:
    """Fully local search: scrape Google/DuckDuckGo + extract actual page content.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        region: Region code for search (default: wt-wt for worldwide)
        timelimit: Time limit for results (d=day, w=week, m=month, y=year, None=any)
    """
    logger.info(f"=== PERFORMING LOCAL SEARCH ===")
    logger.info(f"Query: {query}")
    logger.info(f"Max results: {max_results}")
    logger.info(f"Region: {region}")
    logger.info(f"Time limit: {timelimit}")
    
    try:
        def _search_and_extract():
            # Step 1: Scrape search results from DuckDuckGo HTML (simpler than Google)
            encoded_query = urllib.parse.quote_plus(query)
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            logger.info(f"Scraping search results from: {search_url}")
            
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                response = client.get(search_url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Parse DuckDuckGo HTML search results
                results = []
                
                # DDG uses div.result for each search result
                result_divs = soup.find_all('div', class_='result')
                
                for div in result_divs[:max_results]:
                    try:
                        # Extract link
                        link_tag = div.find('a', class_='result__a')
                        if not link_tag or not link_tag.get('href'):
                            continue
                        
                        # DDG uses uddg parameter, need to decode
                        href_raw = link_tag['href']
                        
                        # Extract actual URL from DDG redirect
                        if 'uddg=' in href_raw:
                            # Parse URL parameters properly
                            parsed = urllib.parse.urlparse(href_raw)
                            params = urllib.parse.parse_qs(parsed.query)
                            url = params.get('uddg', [''])[0]
                        else:
                            url = href_raw
                        
                        # Skip non-http links
                        if not url.startswith('http'):
                            continue
                        
                        # Extract title
                        title = link_tag.get_text(strip=True) if link_tag else 'No title'
                        
                        results.append({
                            'url': url,
                            'title': title
                        })
                        
                    except Exception as e:
                        logger.warning(f"Error parsing search result: {e}")
                        continue
                
                logger.info(f"Found {len(results)} search results")
                
                # Step 2: Extract content from each result page
                enriched_results = []
                for result in results:
                    logger.info(f"Extracting content from: {result['url']}")
                    content_data = extract_page_content(result['url'])
                    
                    enriched_results.append({
                        'url': result['url'],
                        'title': content_data['title'] or result['title'],
                        'description': content_data['description'],
                        'content': content_data['content']
                    })
                
                logger.info(f"Successfully extracted content from {len(enriched_results)} pages")
                return enriched_results
        
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, _search_and_extract)
        
        if not results:
            logger.warning("No results found!")
            return "No results found for the query."
        
        # Format results with full content for LLM
        formatted_results = []
        for i, result in enumerate(results):
            formatted = f"[{i+1}] {result['title']}\n"
            formatted += f"URL: {result['url']}\n"
            
            if result['description']:
                formatted += f"Description: {result['description']}\n"
            
            if result['content']:
                formatted += f"Content:\n{result['content']}\n"
            
            formatted_results.append(formatted)
            logger.debug(f"Result {i+1}: {result['title'][:50]}...")
        
        final_result = "\n---\n\n".join(formatted_results)
        logger.info(f"Returning {len(formatted_results)} formatted results with content")
        return final_result
        
    except Exception as e:
        logger.error(f"Search failed with error: {e}", exc_info=True)
        return f"Error performing search: {str(e)}"

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    logger.info("=== LIST TOOLS CALLED ===")
    tools = [
        types.Tool(
            name="search_web",
            description="Przeszukuje internet lokalnie (scraping + ekstrakcja treści). Zwraca pełny kontekst ze stron dla lokalnego modelu AI. Użyj tego narzędzia, gdy potrzebujesz aktualnych informacji z internetu.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Zapytanie do wyszukiwarki (search query). Najlepiej w języku angielskim dla globalnych wyników."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maksymalna liczba wyników (domyślnie: 5).",
                        "default": 5
                    },
                    "region": {
                        "type": "string",
                        "description": "Region wyszukiwania. Opcje: 'wt-wt' (cały świat), 'pl-pl' (Polska), 'us-en' (USA), 'uk-en' (UK), 'de-de' (Niemcy). Domyślnie: 'wt-wt' dla globalnych wyników.",
                        "default": "wt-wt"
                    },
                    "timelimit": {
                        "type": "string",
                        "description": "Ograniczenie czasowe wyników: 'd' (ostatni dzień), 'w' (ostatni tydzień), 'm' (ostatni miesiąc), 'y' (ostatni rok). Puste = bez ograniczeń.",
                        "enum": ["d", "w", "m", "y", ""]
                    }
                },
                "required": ["query"]
            },
        )
    ]
    logger.info(f"Returning {len(tools)} tools")
    return tools

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    logger.info("=== CALL TOOL RECEIVED ===")
    logger.info(f"Tool name: {name}")
    logger.info(f"Arguments: {arguments}")
    
    if name == "search_web":
        if not arguments:
            logger.error("No arguments provided!")
            raise ValueError("Missing arguments")
        
        query = arguments.get("query")
        if not query:
            logger.error("No query in arguments!")
            raise ValueError("Missing 'query' argument")
            
        max_results = arguments.get("max_results", 5)
        region = arguments.get("region", "wt-wt")
        timelimit = arguments.get("timelimit") or None
        
        logger.info(f"Executing search for: {query}")
        logger.info(f"Region: {region}, Timelimit: {timelimit}")
        result_text = await perform_search(
            query=query,
            max_results=int(max_results),
            region=region,
            timelimit=timelimit
        )
        
        logger.info(f"Search completed, result length: {len(result_text)} chars")
        
        return [
            types.TextContent(
                type="text",
                text=result_text
            )
        ]
    
    logger.error(f"Unknown tool requested: {name}")
    raise ValueError(f"Unknown tool: {name}")

# Pure ASGI application
async def app(scope, receive, send):
    """Raw ASGI application for MCP SSE transport."""
    if scope["type"] != "http":
        return
    
    path = scope["path"]
    method = scope["method"]
    
    logger.debug(f"HTTP Request: {method} {path}")
    
    if path == "/sse" and method == "GET":
        logger.info("SSE connection established")
        async with sse_transport.connect_sse(scope, receive, send) as streams:
            read_stream, write_stream = streams
            await server.run(read_stream, write_stream, server.create_initialization_options())
    
    elif path.startswith("/messages") and method == "POST":
        logger.debug("Processing POST /messages")
        await sse_transport.handle_post_message(scope, receive, send)
    
    else:
        logger.warning(f"404 for: {method} {path}")
        await send({
            "type": "http.response.start",
            "status": 404,
            "headers": [[b"content-type", b"text/plain"]],
        })
        await send({
            "type": "http.response.body",
            "body": b"Not Found",
        })

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting MCP Web Search Server (Local Scraping + Content Extraction)...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Web Search MCP Server

A local Model Context Protocol (MCP) server that provides web search capabilities using [DuckDuckGo](https://pypi.org/project/duckduckgo-search/). Designed to run via Docker and integrate with [LM Studio](https://lmstudio.ai/).

## Features
- **Free**: Uses DuckDuckGo (no API keys required).
- **Private**: Runs locally on your machine.
- **Automatic**: Starts efficiently with Docker Desktop.
- **Standard**: Uses Server-Sent Events (SSE) for MCP communication.

## Prerequisites
- Docker Desktop installed.

## Installation & Usage

1. **Build and Start**:
   Open a terminal in this directory and run:
   ```bash
   docker-compose up -d
   ```
   This will build the image and start the container in the background. It will automatically restart if Docker restarts.

2. **Connect LM Studio**:
   - Open LM Studio.
   - Go to the **MCP (Model Context Protocol)** section (usually under connections or developer settings).
   - Add a new MCP Server:
     - **Name**: Web Search
     - **Type**: SSE (HTTP)
     - **URL**: `http://localhost:8000/sse`
   - LM Studio should connect and list `search_web` as an available tool.

## Technical Details
- **Port**: 8000
- **Transport**: SSE
- **Tech Stack**: Python 3.12, FastAPI, MCP SDK, DuckDuckGo Search.

## Troubleshooting
If the server doesn't start or LM Studio can't connect:
1. Check logs:
   ```bash
   docker logs web-search-mcp
   ```
2. Verify port 8000 is free on your host.

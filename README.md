# Web Search MCP Server

Lokalny serwer Model Context Protocol (MCP) zapewniający możliwości wyszukiwania w sieci przy użyciu DuckDuckGo oraz ekstrakcji treści ze stron internetowych. Zaprojektowany do pracy z [LM Studio](https://lmstudio.ai/) i innymi klientami MCP.

## Funkcje
- **Darmowy**: Używa DuckDuckGo (bez wymaganych kluczy API)
- **Prywatny**: Działa lokalnie na Twoim komputerze
- **Automatyczny**: Łatwe uruchomienie z Docker
- **Standardowy**: Używa Server-Sent Events (SSE) dla komunikacji MCP
- **Ekstrakcja treści**: Automatycznie wyciąga główną treść ze stron internetowych za pomocą trafilatura

## Instalacja

### Metoda 1: Obraz z Docker Hub (Zalecana)

Pobierz i uruchom gotowy obraz z Docker Hub:

```bash
docker run -d -p 8000:8000 --name web_search_mcp kuba7331/web-search-mcp
```

**Sprawdź logi**:
```bash
docker logs web_search_mcp
```

### Metoda 2: Klonowanie i Uruchomienie Ręczne

1. **Sklonuj repozytorium**:
   ```bash
   git clone https://github.com/Kvmyk/WebSearchMCPServer.git
   cd WebSearchMCPServer
   ```

2. **Uruchom z Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Sprawdź logi**:
   ```bash
   docker logs web-search-mcp
   ```

## Połączenie z LM Studio

Po uruchomieniu serwera:

1. Otwórz **LM Studio**
2. Przejdź do sekcji **MCP (Model Context Protocol)** (zazwyczaj w ustawieniach lub zakładce connections/developer)
3. Dodaj nowy serwer MCP:
   - **Name**: `Web Search`
   - **Type**: `SSE (HTTP)`
   - **URL**: `http://localhost:8000/sse`
4. Kliknij **Connect**

LM Studio powinno się połączyć i wyświetlić narzędzie `search_web` jako dostępne.

## Testowanie

Projekt zawiera kompleksowy zestaw testów jednostkowych i integracyjnych.

**Uruchom wszystkie testy**:
```bash
pip install -r requirements.txt
pip install -r tests/requirements-test.txt
pytest tests/ -v
```

**Struktura testów**:
- `tests/test_server.py` - Testy funkcjonalności serwera MCP
- `tests/test_search.py` - Testy wyszukiwania i parsowania wyników DuckDuckGo
- `tests/test_content_extraction.py` - Testy ekstrakcji treści trafilatura/BeautifulSoup

## Szczegóły Techniczne

- **Port**: 8000
- **Transport**: SSE (Server-Sent Events)
- **Stos technologiczny**: 
  - Python 3.12
  - MCP SDK
  - DuckDuckGo HTML scraping
  - trafilatura (ekstrakcja treści)
  - BeautifulSoup4 (parsing HTML)
  - httpx (HTTP client)
  - uvicorn (ASGI server)

## Licencja

Ten projekt jest dostępny na licencji MIT License. Zobacz plik [LICENSE](LICENSE) dla szczegółów.




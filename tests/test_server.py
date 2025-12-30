"""
Tests for MCP server functionality.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server import server, handle_list_tools, handle_call_tool
import mcp.types as types


@pytest.mark.unit
class TestMCPServer:
    """Test suite for MCP server handlers."""
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test that list_tools returns the search_web tool."""
        tools = await handle_list_tools()
        
        assert len(tools) > 0
        assert any(tool.name == 'search_web' for tool in tools)
        
        search_tool = next(tool for tool in tools if tool.name == 'search_web')
        assert search_tool.description is not None
        assert 'query' in search_tool.inputSchema['properties']
        assert search_tool.inputSchema['required'] == ['query']
    
    @pytest.mark.asyncio
    async def test_list_tools_schema(self):
        """Test that search_web tool has correct schema."""
        tools = await handle_list_tools()
        search_tool = next(tool for tool in tools if tool.name == 'search_web')
        
        schema = search_tool.inputSchema
        properties = schema['properties']
        
        # Check all expected properties exist
        assert 'query' in properties
        assert 'max_results' in properties
        assert 'region' in properties
        assert 'timelimit' in properties
        
        # Check query is required
        assert 'query' in schema['required']
        
        # Check default values
        assert properties['max_results']['default'] == 5
        assert properties['region']['default'] == 'wt-wt'
    
    @pytest.mark.asyncio
    async def test_call_tool_search_web_success(self):
        """Test successful call to search_web tool."""
        arguments = {
            'query': 'test query',
            'max_results': 3
        }
        
        with patch('server.perform_search') as mock_search:
            mock_search.return_value = "Mocked search results"
            
            result = await handle_call_tool('search_web', arguments)
            
            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)
            assert result[0].text == "Mocked search results"
            
            mock_search.assert_called_once_with(
                query='test query',
                max_results=3,
                region='wt-wt',
                timelimit=None
            )
    
    @pytest.mark.asyncio
    async def test_call_tool_with_all_parameters(self):
        """Test call_tool with all optional parameters."""
        arguments = {
            'query': 'test',
            'max_results': 10,
            'region': 'pl-pl',
            'timelimit': 'w'
        }
        
        with patch('server.perform_search') as mock_search:
            mock_search.return_value = "Results"
            
            result = await handle_call_tool('search_web', arguments)
            
            mock_search.assert_called_once_with(
                query='test',
                max_results=10,
                region='pl-pl',
                timelimit='w'
            )
    
    @pytest.mark.asyncio
    async def test_call_tool_missing_arguments(self):
        """Test that missing arguments raises ValueError."""
        with pytest.raises(ValueError, match="Missing arguments"):
            await handle_call_tool('search_web', None)
    
    @pytest.mark.asyncio
    async def test_call_tool_missing_query(self):
        """Test that missing query raises ValueError."""
        arguments = {'max_results': 5}
        
        with pytest.raises(ValueError, match="Missing 'query' argument"):
            await handle_call_tool('search_web', arguments)
    
    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self):
        """Test that unknown tool name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await handle_call_tool('nonexistent_tool', {'query': 'test'})
    
    @pytest.mark.asyncio
    async def test_call_tool_default_parameters(self):
        """Test that default parameters are applied correctly."""
        arguments = {'query': 'test'}
        
        with patch('server.perform_search') as mock_search:
            mock_search.return_value = "Results"
            
            await handle_call_tool('search_web', arguments)
            
            # Verify defaults were used
            call_kwargs = mock_search.call_args[1]
            assert call_kwargs['max_results'] == 5
            assert call_kwargs['region'] == 'wt-wt'
            assert call_kwargs['timelimit'] is None


@pytest.mark.integration
class TestMCPServerIntegration:
    """Integration tests for MCP server."""
    
    @pytest.mark.asyncio
    async def test_full_search_workflow(self):
        """Test complete workflow from tool call to result."""
        arguments = {
            'query': 'Python programming',
            'max_results': 2
        }
        
        mock_search_result = """[1] Python Tutorial
URL: https://example.com/python
Description: Learn Python programming
Content: Python is a high-level programming language...

---

[2] Python Documentation
URL: https://python.org/docs
Description: Official Python docs
Content: Welcome to the official Python documentation..."""
        
        with patch('server.perform_search') as mock_search:
            mock_search.return_value = mock_search_result
            
            # First, verify tool is listed
            tools = await handle_list_tools()
            assert any(t.name == 'search_web' for t in tools)
            
            # Then call the tool
            result = await handle_call_tool('search_web', arguments)
            
            # Verify result structure
            assert len(result) == 1
            assert result[0].type == 'text'
            assert 'Python Tutorial' in result[0].text
            assert 'https://example.com/python' in result[0].text
    
    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that server is properly initialized."""
        # Verify server object exists and has correct name
        assert server is not None
        assert hasattr(server, 'name')
        # Note: The actual name attribute might be internal


@pytest.mark.unit
class TestASGIApplication:
    """Tests for ASGI application endpoints."""
    
    @pytest.mark.asyncio
    async def test_asgi_app_structure(self):
        """Test that ASGI app is properly defined."""
        from server import app
        
        # Verify app is a coroutine function
        import inspect
        assert inspect.iscoroutinefunction(app)
    
    @pytest.mark.asyncio
    async def test_invalid_scope_type(self):
        """Test that non-HTTP requests are ignored."""
        from server import app
        
        scope = {'type': 'websocket', 'path': '/', 'method': 'GET'}
        receive = AsyncMock()
        send = AsyncMock()
        
        # Should return early without error
        await app(scope, receive, send)
        
        # Send should not be called for non-HTTP
        send.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_404_response(self):
        """Test 404 response for unknown paths."""
        from server import app
        
        scope = {
            'type': 'http',
            'path': '/unknown',
            'method': 'GET'
        }
        receive = AsyncMock()
        send = AsyncMock()
        
        await app(scope, receive, send)
        
        # Verify 404 response was sent
        assert send.call_count >= 2
        start_call = send.call_args_list[0][0][0]
        assert start_call['type'] == 'http.response.start'
        assert start_call['status'] == 404

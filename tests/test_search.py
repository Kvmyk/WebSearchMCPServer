"""
Tests for web search functionality.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server import perform_search


@pytest.mark.unit
class TestWebSearch:
    """Test suite for perform_search function."""
    
    @pytest.mark.asyncio
    async def test_successful_search(self):
        """Test successful web search with mocked responses."""
        mock_search_html = """
        <html>
            <body>
                <div class="result">
                    <a class="result__a" href="/?uddg=https://example.com/1">First Result</a>
                </div>
                <div class="result">
                    <a class="result__a" href="/?uddg=https://example.com/2">Second Result</a>
                </div>
            </body>
        </html>
        """
        
        with patch('server.httpx.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            # Mock search results page
            mock_search_response = Mock()
            mock_search_response.text = mock_search_html
            mock_search_response.raise_for_status = Mock()
            
            # Mock individual page responses
            def get_side_effect(url, headers):
                if 'duckduckgo' in url:
                    return mock_search_response
                else:
                    response = Mock()
                    response.text = "<html><body><p>Test content</p></body></html>"
                    response.raise_for_status = Mock()
                    return response
            
            mock_client.get.side_effect = get_side_effect
            
            with patch('server.extract_page_content') as mock_extract:
                mock_extract.return_value = {
                    'title': 'Test Title',
                    'description': 'Test description',
                    'content': 'Test content'
                }
                
                result = await perform_search('test query', max_results=2)
                
                assert 'Test Title' in result
                assert 'https://example.com/1' in result
                assert 'https://example.com/2' in result
    
    @pytest.mark.asyncio
    async def test_search_with_no_results(self):
        """Test search when no results are found."""
        mock_html = "<html><body></body></html>"
        
        with patch('server.httpx.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.text = mock_html
            mock_response.raise_for_status = Mock()
            mock_client.get.return_value = mock_response
            
            result = await perform_search('nonexistent query')
            
            assert 'No results found' in result
    
    @pytest.mark.asyncio
    async def test_search_with_max_results(self):
        """Test that max_results parameter is respected."""
        # Create HTML with 10 results
        results_html = ''.join([
            f'<div class="result"><a class="result__a" href="/?uddg=https://example.com/{i}">Result {i}</a></div>'
            for i in range(10)
        ])
        mock_html = f"<html><body>{results_html}</body></html>"
        
        with patch('server.httpx.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            mock_search_response = Mock()
            mock_search_response.text = mock_html
            mock_search_response.raise_for_status = Mock()
            
            def get_side_effect(url, headers):
                if 'duckduckgo' in url:
                    return mock_search_response
                else:
                    response = Mock()
                    response.text = "<html><body><p>Content</p></body></html>"
                    response.raise_for_status = Mock()
                    return response
            
            mock_client.get.side_effect = get_side_effect
            
            with patch('server.extract_page_content') as mock_extract:
                mock_extract.return_value = {
                    'title': 'Title',
                    'description': 'Desc',
                    'content': 'Content'
                }
                
                result = await perform_search('test', max_results=3)
                
                # Count occurrences of result markers
                result_count = result.count('[1]') + result.count('[2]') + result.count('[3]')
                assert result_count >= 3
                assert '[4]' not in result
    
    @pytest.mark.asyncio
    async def test_search_error_handling(self):
        """Test proper error handling during search."""
        with patch('server.httpx.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.get.side_effect = Exception("Network error")
            
            result = await perform_search('test query')
            
            assert 'Error performing search' in result
            assert 'Network error' in result
    
    @pytest.mark.asyncio
    async def test_search_url_encoding(self):
        """Test that query is properly URL encoded."""
        mock_html = "<html><body></body></html>"
        
        with patch('server.httpx.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.text = mock_html
            mock_response.raise_for_status = Mock()
            mock_client.get.return_value = mock_response
            
            await perform_search('test query with spaces & symbols')
            
            # Verify the URL was called with encoded query
            call_args = mock_client.get.call_args
            called_url = call_args[0][0]
            assert 'test+query' in called_url or 'test%20query' in called_url
    
    @pytest.mark.asyncio
    async def test_search_with_region(self):
        """Test search with different region parameters."""
        mock_html = "<html><body></body></html>"
        
        with patch('server.httpx.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            mock_response = Mock()
            mock_response.text = mock_html
            mock_response.raise_for_status = Mock()
            mock_client.get.return_value = mock_response
            
            # Note: Current implementation doesn't use region parameter in URL
            # This test verifies the function accepts the parameter
            result = await perform_search('test', region='pl-pl')
            
            assert 'No results found' in result  # Expected for empty HTML


@pytest.mark.integration
class TestSearchIntegration:
    """Integration tests for search functionality."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_real_search_structure(self):
        """Test search returns properly structured results."""
        # This would be a real search in integration testing
        # For now, we mock it to verify structure
        with patch('server.httpx.Client') as mock_client_class:
            mock_html = """
            <html>
                <body>
                    <div class="result">
                        <a class="result__a" href="/?uddg=https://example.com">Example</a>
                    </div>
                </body>
            </html>
            """
            
            mock_client = Mock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            mock_search_response = Mock()
            mock_search_response.text = mock_html
            mock_search_response.raise_for_status = Mock()
            
            mock_page_response = Mock()
            mock_page_response.text = "<html><body><p>Content</p></body></html>"
            mock_page_response.raise_for_status = Mock()
            
            mock_client.get.side_effect = [mock_search_response, mock_page_response]
            
            with patch('server.extract_page_content') as mock_extract:
                mock_extract.return_value = {
                    'title': 'Example Title',
                    'description': 'Example description',
                    'content': 'Example content'
                }
                
                result = await perform_search('test query')
                
                # Verify result structure
                assert '[1]' in result
                assert 'URL:' in result
                assert 'Example Title' in result

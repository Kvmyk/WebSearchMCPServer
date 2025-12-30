"""
Tests for content extraction functionality.
"""
import pytest
from unittest.mock import Mock, patch
import httpx
from bs4 import BeautifulSoup
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server import extract_page_content


@pytest.mark.unit
class TestContentExtraction:
    """Test suite for extract_page_content function."""
    
    def test_successful_extraction_with_trafilatura(self):
        """Test successful content extraction using trafilatura."""
        mock_html = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <article>
                    <h1>Main Title</h1>
                    <p>This is the main content of the article.</p>
                </article>
            </body>
        </html>
        """
        
        mock_json = {
            'title': 'Test Article',
            'description': 'Test description',
            'text': 'Main Title. This is the main content of the article.'
        }
        
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.text = mock_html
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with patch('server.trafilatura.extract') as mock_extract:
                import json
                mock_extract.return_value = json.dumps(mock_json)
                
                result = extract_page_content('https://example.com/article')
                
                assert result['title'] == 'Test Article'
                assert result['description'] == 'Test description'
                assert 'main content' in result['content']
    
    def test_fallback_to_beautifulsoup(self):
        """Test fallback to BeautifulSoup when trafilatura fails."""
        mock_html = """
        <html>
            <head>
                <title>Fallback Test</title>
                <meta name="description" content="Fallback description">
            </head>
            <body>
                <p>First paragraph of content.</p>
                <p>Second paragraph of content.</p>
            </body>
        </html>
        """
        
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.text = mock_html
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with patch('server.trafilatura.extract') as mock_extract:
                mock_extract.return_value = None  # Simulate trafilatura failure
                
                result = extract_page_content('https://example.com/test')
                
                assert result['title'] == 'Fallback Test'
                assert 'Fallback description' in result['description']
                assert 'First paragraph' in result['content']
    
    def test_http_error_handling(self):
        """Test proper error handling for HTTP errors."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.HTTPStatusError(
                "404 Not Found",
                request=Mock(),
                response=Mock(status_code=404)
            )
            
            result = extract_page_content('https://example.com/notfound')
            
            assert result['title'] == 'Content extraction failed'
            assert 'Error' in result['content']
    
    def test_timeout_handling(self):
        """Test proper handling of request timeouts."""
        with patch('httpx.Client') as mock_client:
            mock_client.return_value.__enter__.return_value.get.side_effect = httpx.TimeoutException(
                "Request timed out"
            )
            
            result = extract_page_content('https://example.com/slow', timeout=1.0)
            
            assert result['title'] == 'Content extraction failed'
            assert 'Error' in result['content']
    
    def test_description_truncation(self):
        """Test that description is truncated to 300 characters."""
        long_description = "x" * 500
        mock_json = {
            'title': 'Test',
            'description': long_description,
            'text': 'Content'
        }
        
        mock_html = "<html><body>test</body></html>"
        
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.text = mock_html
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with patch('server.trafilatura.extract') as mock_extract:
                import json
                mock_extract.return_value = json.dumps(mock_json)
                
                result = extract_page_content('https://example.com')
                
                assert len(result['description']) == 300
    
    def test_content_truncation(self):
        """Test that content is truncated to 800 characters."""
        long_content = "y" * 1000
        mock_json = {
            'title': 'Test',
            'description': 'Desc',
            'text': long_content
        }
        
        mock_html = "<html><body>test</body></html>"
        
        with patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.text = mock_html
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response
            
            with patch('server.trafilatura.extract') as mock_extract:
                import json
                mock_extract.return_value = json.dumps(mock_json)
                
                result = extract_page_content('https://example.com')
                
                assert len(result['content']) == 800

"""
Tests for Task 2.4: Toast Notification Container

Validates that the toast notification container element exists with:
- Proper ARIA live region attributes
- Correct positioning at top-right
- Appropriate z-index management
"""

import pytest
from bs4 import BeautifulSoup
import os


def test_toast_container_exists(client):
    """Test that toast container element exists in HTML"""
    response = client.get('/')
    assert response.status_code == 200
    
    html = response.data.decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find toast container
    toast_container = soup.find('div', id='toast-container')
    assert toast_container is not None, "Toast container element should exist"


def test_toast_container_aria_attributes(client):
    """Test that toast container has proper ARIA live region attributes"""
    response = client.get('/')
    html = response.data.decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    
    toast_container = soup.find('div', id='toast-container')
    
    # Validate ARIA attributes (Requirement 16.1, 16.8)
    assert toast_container.get('role') == 'region', \
        "Toast container should have role='region'"
    
    assert toast_container.get('aria-live') == 'polite', \
        "Toast container should have aria-live='polite' for screen reader announcements"
    
    assert toast_container.get('aria-label') == 'Notifications', \
        "Toast container should have aria-label='Notifications'"


def test_toast_container_css_class(client):
    """Test that toast container has the correct CSS class"""
    response = client.get('/')
    html = response.data.decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    
    toast_container = soup.find('div', id='toast-container')
    
    # Check CSS class
    assert 'toast-container' in toast_container.get('class', []), \
        "Toast container should have 'toast-container' CSS class"


def test_toast_container_css_positioning():
    """Test that toast container CSS has proper positioning (Requirement 16.5)"""
    # Read CSS file
    css_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'style.css')
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check for toast-container styles
    assert '.toast-container' in css_content, \
        "CSS should define .toast-container class"
    
    # Check positioning properties
    assert 'position: fixed' in css_content or 'position:fixed' in css_content, \
        "Toast container should have fixed positioning"
    
    # Check for top-right positioning (Requirement 16.1)
    # Look for top and right properties in toast-container section
    toast_section_start = css_content.find('.toast-container {')
    if toast_section_start != -1:
        # Find the next closing brace
        toast_section_end = css_content.find('}', toast_section_start)
        toast_section = css_content[toast_section_start:toast_section_end]
        
        assert 'top:' in toast_section or 'top :' in toast_section, \
            "Toast container should have top positioning"
        assert 'right:' in toast_section or 'right :' in toast_section, \
            "Toast container should have right positioning for top-right placement"


def test_toast_container_z_index():
    """Test that toast container has appropriate z-index (Requirement 16.5)"""
    # Read CSS file
    css_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'style.css')
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check for z-index in toast-container
    toast_section_start = css_content.find('.toast-container {')
    if toast_section_start != -1:
        toast_section_end = css_content.find('}', toast_section_start)
        toast_section = css_content[toast_section_start:toast_section_end]
        
        assert 'z-index' in toast_section, \
            "Toast container should have z-index for proper layering"
        
        # Check for high z-index value (should be >= 1000 to stay on top)
        if 'z-index:' in toast_section:
            z_index_start = toast_section.find('z-index:') + len('z-index:')
            z_index_end = toast_section.find(';', z_index_start)
            z_index_value = toast_section[z_index_start:z_index_end].strip()
            assert int(z_index_value) >= 1000, \
                "Toast container z-index should be >= 1000 for proper layering"


def test_toast_styles_exist():
    """Test that toast notification styles are defined in CSS"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'style.css')
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check for key toast-related CSS classes
    assert '.toast {' in css_content or '.toast{' in css_content, \
        "CSS should define .toast class for individual notifications"
    
    assert '.toast--success' in css_content, \
        "CSS should define success toast variant"
    
    assert '.toast--error' in css_content, \
        "CSS should define error toast variant"
    
    assert '.toast--warning' in css_content, \
        "CSS should define warning toast variant"
    
    assert '.toast--info' in css_content, \
        "CSS should define info toast variant"


def test_toast_container_empty_initially(client):
    """Test that toast container is initially empty"""
    response = client.get('/')
    html = response.data.decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    
    toast_container = soup.find('div', id='toast-container')
    
    # Should have no child elements initially
    children = list(toast_container.children)
    # Filter out whitespace-only text nodes
    non_whitespace_children = [
        child for child in children 
        if not (isinstance(child, str) and child.strip() == '')
    ]
    
    assert len(non_whitespace_children) == 0, \
        "Toast container should be empty initially (no toast notifications)"


def test_toast_responsive_styles():
    """Test that toast container has responsive styles for mobile"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'style.css')
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Check for mobile media query styles
    assert '@media (max-width: 768px)' in css_content or \
           '@media(max-width: 768px)' in css_content or \
           '@media (max-width:768px)' in css_content, \
        "CSS should have mobile responsive styles"
    
    # Check that toast-container is styled in mobile view
    # Find mobile media query section
    mobile_query_start = css_content.find('@media')
    while mobile_query_start != -1:
        # Check if this media query contains toast-container
        query_end = css_content.find('}', mobile_query_start)
        # Find the matching closing brace for the media query
        brace_count = 1
        pos = css_content.find('{', mobile_query_start) + 1
        while pos < len(css_content) and brace_count > 0:
            if css_content[pos] == '{':
                brace_count += 1
            elif css_content[pos] == '}':
                brace_count -= 1
            pos += 1
        
        query_section = css_content[mobile_query_start:pos]
        if '768px' in query_section and '.toast-container' in query_section:
            # Found mobile styles for toast container
            break
        
        mobile_query_start = css_content.find('@media', pos)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

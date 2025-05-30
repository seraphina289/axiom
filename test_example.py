#!/usr/bin/env python3
"""
Example Python file to test advanced syntax highlighting and search functionality
"""

import re
import json
from typing import List, Dict, Optional
from pathlib import Path

class TextProcessor:
    """A sample class to demonstrate syntax highlighting"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}-\d{3}-\d{4}\b',
            'url': r'https?://[^\s]+'
        }
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def process_text(self, text: str, options: Optional[List[str]] = None) -> Dict[str, any]:
        """Process text with various options"""
        if options is None:
            options = ['default']
        
        result = {
            'original': text,
            'length': len(text),
            'words': len(text.split()),
            'options_used': options
        }
        
        # Find patterns
        for name, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                result[f'{name}_matches'] = matches
        
        return result
    
    def save_results(self, results: Dict, filename: str = "results.json"):
        """Save results to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {filename}")
        except Exception as e:
            print(f"Error saving results: {e}")

# Example usage
if __name__ == "__main__":
    processor = TextProcessor({
        'mode': 'advanced',
        'case_sensitive': True
    })
    
    sample_text = """
    Contact us at support@example.com or call 123-456-7890.
    Visit our website: https://www.example.com for more info.
    """
    
    results = processor.process_text(sample_text, ['email', 'phone', 'url'])
    processor.save_results(results)
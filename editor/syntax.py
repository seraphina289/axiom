"""
Syntax highlighting for Axiom editor
"""

import re
import logging
from typing import List, Tuple, Optional, Dict
from pathlib import Path


class SyntaxHighlighter:
    """Provides advanced syntax highlighting for various file types"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Enhanced color pair constants
        self.COLOR_NORMAL = 1      # White - normal text
        self.COLOR_KEYWORD = 2     # Blue - keywords, reserved words
        self.COLOR_STRING = 3      # Green - strings, literals
        self.COLOR_COMMENT = 4     # Yellow - comments, documentation
        self.COLOR_ERROR = 5       # Red - errors, warnings
        self.COLOR_NUMBER = 6      # Cyan - numbers, constants
        self.COLOR_OPERATOR = 7    # Magenta - operators, symbols
        self.COLOR_FUNCTION = 2    # Blue - function names, methods
        self.COLOR_CLASS = 6       # Cyan - class names, types
        self.COLOR_VARIABLE = 1    # White - variables, identifiers
        self.COLOR_PREPROCESSOR = 5 # Red - preprocessor directives
        self.COLOR_BRACKET = 7     # Magenta - brackets, delimiters
        
        # Advanced highlighting features
        self.highlight_matching_brackets = True
        self.highlight_trailing_whitespace = True
        self.highlight_long_lines = True
        self.max_line_length = 120
        
        # Current syntax type
        self.current_syntax = None
        
        # Syntax patterns for different languages
        self.syntax_patterns = {
            'python': self._get_python_patterns(),
            'javascript': self._get_javascript_patterns(),
            'html': self._get_html_patterns(),
            'css': self._get_css_patterns(),
            'json': self._get_json_patterns(),
            'xml': self._get_xml_patterns(),
            'markdown': self._get_markdown_patterns(),
            'sh': self._get_shell_patterns(),
            'bash': self._get_shell_patterns(),
            'c': self._get_c_patterns(),
            'cpp': self._get_cpp_patterns(),
            'java': self._get_java_patterns(),
            'rust': self._get_rust_patterns(),
            'go': self._get_go_patterns(),
        }
        
        # File extension mappings
        self.extension_map = {
            '.py': 'python',
            '.pyw': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'javascript',
            '.tsx': 'javascript',
            '.html': 'html',
            '.htm': 'html',
            '.xhtml': 'html',
            '.css': 'css',
            '.scss': 'css',
            '.sass': 'css',
            '.less': 'css',
            '.json': 'json',
            '.xml': 'xml',
            '.xsl': 'xml',
            '.xsd': 'xml',
            '.md': 'markdown',
            '.markdown': 'markdown',
            '.sh': 'sh',
            '.bash': 'bash',
            '.zsh': 'bash',
            '.fish': 'bash',
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.cc': 'cpp',
            '.hpp': 'cpp',
            '.hxx': 'cpp',
            '.java': 'java',
            '.rs': 'rust',
            '.go': 'go',
        }
    
    def highlight_line(self, line: str, filename: Optional[str] = None, line_number: int = 0, 
                      cursor_col: int = -1) -> List[Tuple[str, int]]:
        """
        Advanced line highlighting with additional features
        Returns list of (text, color_pair) tuples
        """
        try:
            # Determine syntax type
            syntax_type = self._get_syntax_type(filename)
            
            if not syntax_type or syntax_type not in self.syntax_patterns:
                # Apply basic highlighting features even without syntax
                return self._apply_basic_highlighting(line, cursor_col)
            
            # Get patterns for this syntax type
            patterns = self.syntax_patterns[syntax_type]
            
            # Apply syntax highlighting
            highlighted = self._apply_patterns(line, patterns)
            
            # Apply additional highlighting features
            highlighted = self._apply_advanced_features(highlighted, line, cursor_col)
            
            return highlighted
            
        except Exception as e:
            self.logger.error(f"Syntax highlighting error: {e}")
            # Return unhighlighted text on error
            return [(line, self.COLOR_NORMAL)]
    
    def _apply_basic_highlighting(self, line: str, cursor_col: int = -1) -> List[Tuple[str, int]]:
        """Apply basic highlighting features without syntax patterns"""
        segments = []
        
        # Check for trailing whitespace
        if self.highlight_trailing_whitespace:
            stripped = line.rstrip()
            if len(stripped) < len(line):
                segments.append((stripped, self.COLOR_NORMAL))
                segments.append((line[len(stripped):], self.COLOR_ERROR))
            else:
                segments.append((line, self.COLOR_NORMAL))
        else:
            segments.append((line, self.COLOR_NORMAL))
        
        return segments
    
    def _apply_advanced_features(self, segments: List[Tuple[str, int]], 
                                original_line: str, cursor_col: int = -1) -> List[Tuple[str, int]]:
        """Apply advanced highlighting features to already highlighted segments"""
        # Check line length
        if self.highlight_long_lines and len(original_line) > self.max_line_length:
            # Mark text after max length as error
            new_segments = []
            current_pos = 0
            
            for text, color in segments:
                if current_pos + len(text) <= self.max_line_length:
                    new_segments.append((text, color))
                else:
                    # Split at max length
                    split_point = self.max_line_length - current_pos
                    if split_point > 0:
                        new_segments.append((text[:split_point], color))
                        new_segments.append((text[split_point:], self.COLOR_ERROR))
                    else:
                        new_segments.append((text, self.COLOR_ERROR))
                current_pos += len(text)
            
            segments = new_segments
        
        # Highlight matching brackets (if cursor position is provided)
        if self.highlight_matching_brackets and cursor_col >= 0:
            segments = self._highlight_matching_brackets(segments, original_line, cursor_col)
        
        return segments
    
    def _highlight_matching_brackets(self, segments: List[Tuple[str, int]], 
                                   line: str, cursor_col: int) -> List[Tuple[str, int]]:
        """Highlight matching brackets around cursor position"""
        if cursor_col >= len(line):
            return segments
        
        bracket_pairs = {'(': ')', '[': ']', '{': '}', '<': '>'}
        reverse_pairs = {v: k for k, v in bracket_pairs.items()}
        
        char_at_cursor = line[cursor_col] if cursor_col < len(line) else ''
        
        if char_at_cursor in bracket_pairs or char_at_cursor in reverse_pairs:
            # Find matching bracket
            if char_at_cursor in bracket_pairs:
                # Forward search
                target = bracket_pairs[char_at_cursor]
                match_pos = self._find_matching_bracket_forward(line, cursor_col, char_at_cursor, target)
            else:
                # Backward search
                target = reverse_pairs[char_at_cursor]
                match_pos = self._find_matching_bracket_backward(line, cursor_col, target, char_at_cursor)
            
            if match_pos >= 0:
                # Highlight both brackets
                segments = self._highlight_character_at_position(segments, cursor_col, self.COLOR_BRACKET)
                segments = self._highlight_character_at_position(segments, match_pos, self.COLOR_BRACKET)
        
        return segments
    
    def _find_matching_bracket_forward(self, line: str, start: int, open_char: str, close_char: str) -> int:
        """Find matching closing bracket"""
        count = 1
        for i in range(start + 1, len(line)):
            if line[i] == open_char:
                count += 1
            elif line[i] == close_char:
                count -= 1
                if count == 0:
                    return i
        return -1
    
    def _find_matching_bracket_backward(self, line: str, start: int, open_char: str, close_char: str) -> int:
        """Find matching opening bracket"""
        count = 1
        for i in range(start - 1, -1, -1):
            if line[i] == close_char:
                count += 1
            elif line[i] == open_char:
                count -= 1
                if count == 0:
                    return i
        return -1
    
    def _highlight_character_at_position(self, segments: List[Tuple[str, int]], 
                                       pos: int, color: int) -> List[Tuple[str, int]]:
        """Highlight a single character at a specific position"""
        new_segments = []
        current_pos = 0
        
        for text, segment_color in segments:
            if current_pos + len(text) <= pos:
                # Before target position
                new_segments.append((text, segment_color))
                current_pos += len(text)
            elif current_pos > pos:
                # After target position
                new_segments.append((text, segment_color))
            else:
                # Contains target position
                local_pos = pos - current_pos
                if local_pos == 0:
                    # At start of segment
                    new_segments.append((text[0], color))
                    if len(text) > 1:
                        new_segments.append((text[1:], segment_color))
                elif local_pos == len(text) - 1:
                    # At end of segment
                    if len(text) > 1:
                        new_segments.append((text[:-1], segment_color))
                    new_segments.append((text[-1], color))
                else:
                    # In middle of segment
                    new_segments.append((text[:local_pos], segment_color))
                    new_segments.append((text[local_pos], color))
                    new_segments.append((text[local_pos + 1:], segment_color))
                current_pos += len(text)
        
        return new_segments
    
    def _get_syntax_type(self, filename: Optional[str]) -> Optional[str]:
        """Determine syntax type from filename or current setting"""
        if self.current_syntax:
            return self.current_syntax
        
        if not filename:
            return None
        
        # Get file extension
        ext = Path(filename).suffix.lower()
        return self.extension_map.get(ext)
    
    def set_syntax_type(self, syntax_type: str):
        """Manually set syntax type"""
        if syntax_type == 'auto' or syntax_type == 'none':
            self.current_syntax = None
        elif syntax_type in self.syntax_patterns:
            self.current_syntax = syntax_type
        else:
            raise ValueError(f"Unknown syntax type: {syntax_type}")
    
    def get_current_syntax(self) -> Optional[str]:
        """Get current syntax type"""
        return self.current_syntax
    
    def _apply_patterns(self, line: str, patterns: List[Dict]) -> List[Tuple[str, int]]:
        """Apply syntax patterns to a line"""
        if not line:
            return [(line, self.COLOR_NORMAL)]
        
        # Create list of matches with positions
        matches = []
        
        for pattern_info in patterns:
            pattern = pattern_info['pattern']
            color = pattern_info['color']
            
            for match in re.finditer(pattern, line):
                matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'color': color,
                    'priority': pattern_info.get('priority', 0)
                })
        
        # Sort matches by position and priority
        matches.sort(key=lambda x: (x['start'], -x['priority']))
        
        # Build highlighted segments
        segments = []
        pos = 0
        
        for match in matches:
            # Skip overlapping matches
            if match['start'] < pos:
                continue
            
            # Add unhighlighted text before match
            if match['start'] > pos:
                segments.append((line[pos:match['start']], self.COLOR_NORMAL))
            
            # Add highlighted match
            segments.append((line[match['start']:match['end']], match['color']))
            pos = match['end']
        
        # Add remaining unhighlighted text
        if pos < len(line):
            segments.append((line[pos:], self.COLOR_NORMAL))
        
        return segments if segments else [(line, self.COLOR_NORMAL)]
    
    # Enhanced syntax pattern definitions
    def _get_python_patterns(self) -> List[Dict]:
        """Get enhanced Python syntax patterns"""
        return [
            # Comments (highest priority)
            {'pattern': r'#.*$', 'color': self.COLOR_COMMENT, 'priority': 10},
            
            # Triple-quoted strings (docstrings)
            {'pattern': r'"""[\s\S]*?"""', 'color': self.COLOR_STRING, 'priority': 9},
            {'pattern': r"'''[\s\S]*?'''", 'color': self.COLOR_STRING, 'priority': 9},
            
            # Regular strings
            {'pattern': r'[fFrRbBuU]?"(?:[^"\\]|\\.)*"', 'color': self.COLOR_STRING, 'priority': 8},
            {'pattern': r"[fFrRbBuU]?'(?:[^'\\]|\\.)*'", 'color': self.COLOR_STRING, 'priority': 8},
            
            # Function definitions
            {'pattern': r'\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'color': self.COLOR_FUNCTION, 'priority': 8},
            
            # Class definitions
            {'pattern': r'\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)', 'color': self.COLOR_CLASS, 'priority': 8},
            
            # Decorators
            {'pattern': r'@[a-zA-Z_][a-zA-Z0-9_.]*', 'color': self.COLOR_PREPROCESSOR, 'priority': 8},
            
            # Keywords
            {'pattern': r'\b(def|class|if|elif|else|for|while|try|except|finally|with|as|import|from|return|yield|break|continue|pass|lambda|and|or|not|in|is|async|await|global|nonlocal|assert|del|raise)\b', 
             'color': self.COLOR_KEYWORD, 'priority': 7},
            
            # Built-in constants
            {'pattern': r'\b(True|False|None|__name__|__file__|__doc__|__package__|__version__)\b', 
             'color': self.COLOR_NUMBER, 'priority': 7},
            
            # Built-in functions
            {'pattern': r'\b(print|len|range|enumerate|zip|map|filter|sum|max|min|abs|round|type|isinstance|hasattr|getattr|setattr|delattr|dir|vars|globals|locals|eval|exec|compile|open|input|int|float|str|bool|list|tuple|dict|set|frozenset)\b', 
             'color': self.COLOR_FUNCTION, 'priority': 6},
            
            # Numbers (enhanced)
            {'pattern': r'\b0[xX][0-9a-fA-F]+[lL]?\b', 'color': self.COLOR_NUMBER, 'priority': 6},  # Hex
            {'pattern': r'\b0[oO][0-7]+[lL]?\b', 'color': self.COLOR_NUMBER, 'priority': 6},        # Octal
            {'pattern': r'\b0[bB][01]+[lL]?\b', 'color': self.COLOR_NUMBER, 'priority': 6},         # Binary
            {'pattern': r'\b\d+\.?\d*([eE][+-]?\d+)?[jJ]?\b', 'color': self.COLOR_NUMBER, 'priority': 6},  # Float/complex
            
            # Operators and delimiters
            {'pattern': r'[+\-*/%=<>!&|^~@]|//|\*\*|<<|>>|<=|>=|==|!=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<=|>>=|\*\*=|//=', 'color': self.COLOR_OPERATOR, 'priority': 5},
            
            # Brackets and delimiters
            {'pattern': r'[(){}\[\],:.;]', 'color': self.COLOR_BRACKET, 'priority': 4},
        ]
    
    def _get_javascript_patterns(self) -> List[Dict]:
        """Get JavaScript syntax patterns"""
        return [
            # Comments
            {'pattern': r'//.*$', 'color': self.COLOR_COMMENT, 'priority': 10},
            {'pattern': r'/\*.*?\*/', 'color': self.COLOR_COMMENT, 'priority': 10},
            
            # Strings
            {'pattern': r'"(?:[^"\\]|\\.)*"', 'color': self.COLOR_STRING, 'priority': 8},
            {'pattern': r"'(?:[^'\\]|\\.)*'", 'color': self.COLOR_STRING, 'priority': 8},
            {'pattern': r'`(?:[^`\\]|\\.)*`', 'color': self.COLOR_STRING, 'priority': 8},
            
            # Keywords
            {'pattern': r'\b(function|var|let|const|if|else|for|while|do|switch|case|break|continue|return|try|catch|finally|throw|new|this|typeof|instanceof|class|extends|constructor|async|await|true|false|null|undefined)\b', 
             'color': self.COLOR_KEYWORD, 'priority': 7},
            
            # Numbers
            {'pattern': r'\b\d+\.?\d*\b', 'color': self.COLOR_NUMBER, 'priority': 6},
            
            # Operators
            {'pattern': r'[+\-*/%=<>!&|^~]', 'color': self.COLOR_OPERATOR, 'priority': 5},
        ]
    
    def _get_html_patterns(self) -> List[Dict]:
        """Get HTML syntax patterns"""
        return [
            # Comments
            {'pattern': r'<!--.*?-->', 'color': self.COLOR_COMMENT, 'priority': 10},
            
            # Tags
            {'pattern': r'</?[a-zA-Z][a-zA-Z0-9]*\b[^>]*>', 'color': self.COLOR_KEYWORD, 'priority': 8},
            
            # Attributes
            {'pattern': r'\b[a-zA-Z-]+\s*=', 'color': self.COLOR_OPERATOR, 'priority': 7},
            
            # Strings (attribute values)
            {'pattern': r'"[^"]*"', 'color': self.COLOR_STRING, 'priority': 8},
            {'pattern': r"'[^']*'", 'color': self.COLOR_STRING, 'priority': 8},
        ]
    
    def _get_css_patterns(self) -> List[Dict]:
        """Get CSS syntax patterns"""
        return [
            # Comments
            {'pattern': r'/\*.*?\*/', 'color': self.COLOR_COMMENT, 'priority': 10},
            
            # Selectors
            {'pattern': r'[.#]?[a-zA-Z][a-zA-Z0-9_-]*(?=\s*{)', 'color': self.COLOR_KEYWORD, 'priority': 8},
            
            # Properties
            {'pattern': r'[a-zA-Z-]+\s*(?=:)', 'color': self.COLOR_OPERATOR, 'priority': 7},
            
            # Values
            {'pattern': r'"[^"]*"', 'color': self.COLOR_STRING, 'priority': 8},
            {'pattern': r"'[^']*'", 'color': self.COLOR_STRING, 'priority': 8},
            
            # Numbers and units
            {'pattern': r'\b\d+\.?\d*(px|em|rem|%|pt|pc|in|mm|cm|ex|ch|vw|vh|vmin|vmax|deg|rad|turn|s|ms|Hz|kHz)?\b', 
             'color': self.COLOR_NUMBER, 'priority': 6},
        ]
    
    def _get_json_patterns(self) -> List[Dict]:
        """Get JSON syntax patterns"""
        return [
            # Strings
            {'pattern': r'"(?:[^"\\]|\\.)*"', 'color': self.COLOR_STRING, 'priority': 8},
            
            # Numbers
            {'pattern': r'-?\b\d+\.?\d*([eE][+-]?\d+)?\b', 'color': self.COLOR_NUMBER, 'priority': 7},
            
            # Keywords
            {'pattern': r'\b(true|false|null)\b', 'color': self.COLOR_KEYWORD, 'priority': 7},
            
            # Operators
            {'pattern': r'[{}[\]:,]', 'color': self.COLOR_OPERATOR, 'priority': 6},
        ]
    
    def _get_xml_patterns(self) -> List[Dict]:
        """Get XML syntax patterns"""
        return [
            # Comments
            {'pattern': r'<!--.*?-->', 'color': self.COLOR_COMMENT, 'priority': 10},
            
            # CDATA
            {'pattern': r'<!\[CDATA\[.*?\]\]>', 'color': self.COLOR_STRING, 'priority': 9},
            
            # Tags
            {'pattern': r'</?[a-zA-Z][a-zA-Z0-9:_-]*\b[^>]*>', 'color': self.COLOR_KEYWORD, 'priority': 8},
            
            # Attributes
            {'pattern': r'\b[a-zA-Z:_-]+\s*=', 'color': self.COLOR_OPERATOR, 'priority': 7},
            
            # Strings
            {'pattern': r'"[^"]*"', 'color': self.COLOR_STRING, 'priority': 8},
            {'pattern': r"'[^']*'", 'color': self.COLOR_STRING, 'priority': 8},
        ]
    
    def _get_markdown_patterns(self) -> List[Dict]:
        """Get Markdown syntax patterns"""
        return [
            # Headers
            {'pattern': r'^#{1,6}\s+.*$', 'color': self.COLOR_KEYWORD, 'priority': 8},
            
            # Bold
            {'pattern': r'\*\*[^*]+\*\*', 'color': self.COLOR_OPERATOR, 'priority': 7},
            {'pattern': r'__[^_]+__', 'color': self.COLOR_OPERATOR, 'priority': 7},
            
            # Italic
            {'pattern': r'\*[^*]+\*', 'color': self.COLOR_NUMBER, 'priority': 6},
            {'pattern': r'_[^_]+_', 'color': self.COLOR_NUMBER, 'priority': 6},
            
            # Code
            {'pattern': r'`[^`]+`', 'color': self.COLOR_STRING, 'priority': 8},
            {'pattern': r'```.*?```', 'color': self.COLOR_STRING, 'priority': 9},
            
            # Links
            {'pattern': r'\[([^\]]+)\]\([^)]+\)', 'color': self.COLOR_KEYWORD, 'priority': 7},
        ]
    
    def _get_shell_patterns(self) -> List[Dict]:
        """Get Shell script syntax patterns"""
        return [
            # Comments
            {'pattern': r'#.*$', 'color': self.COLOR_COMMENT, 'priority': 10},
            
            # Strings
            {'pattern': r'"(?:[^"\\]|\\.)*"', 'color': self.COLOR_STRING, 'priority': 8},
            {'pattern': r"'(?:[^'\\]|\\.)*'", 'color': self.COLOR_STRING, 'priority': 8},
            
            # Keywords
            {'pattern': r'\b(if|then|else|elif|fi|case|esac|for|while|until|do|done|function|select|time|in)\b', 
             'color': self.COLOR_KEYWORD, 'priority': 7},
            
            # Variables
            {'pattern': r'\$[a-zA-Z_][a-zA-Z0-9_]*', 'color': self.COLOR_NUMBER, 'priority': 6},
            {'pattern': r'\$\{[^}]+\}', 'color': self.COLOR_NUMBER, 'priority': 6},
            
            # Operators
            {'pattern': r'[|&;<>(){}[\]]', 'color': self.COLOR_OPERATOR, 'priority': 5},
        ]
    
    def _get_c_patterns(self) -> List[Dict]:
        """Get C syntax patterns"""
        return [
            # Comments
            {'pattern': r'//.*$', 'color': self.COLOR_COMMENT, 'priority': 10},
            {'pattern': r'/\*.*?\*/', 'color': self.COLOR_COMMENT, 'priority': 10},
            
            # Preprocessor
            {'pattern': r'#\s*[a-zA-Z_][a-zA-Z0-9_]*', 'color': self.COLOR_OPERATOR, 'priority': 9},
            
            # Strings
            {'pattern': r'"(?:[^"\\]|\\.)*"', 'color': self.COLOR_STRING, 'priority': 8},
            {'pattern': r"'(?:[^'\\]|\\.)'", 'color': self.COLOR_STRING, 'priority': 8},
            
            # Keywords
            {'pattern': r'\b(auto|break|case|char|const|continue|default|do|double|else|enum|extern|float|for|goto|if|int|long|register|return|short|signed|sizeof|static|struct|switch|typedef|union|unsigned|void|volatile|while)\b', 
             'color': self.COLOR_KEYWORD, 'priority': 7},
            
            # Numbers
            {'pattern': r'\b\d+\.?\d*[fFlL]?\b', 'color': self.COLOR_NUMBER, 'priority': 6},
            
            # Operators
            {'pattern': r'[+\-*/%=<>!&|^~]', 'color': self.COLOR_OPERATOR, 'priority': 5},
        ]
    
    def _get_cpp_patterns(self) -> List[Dict]:
        """Get C++ syntax patterns"""
        patterns = self._get_c_patterns()
        
        # Add C++ specific keywords
        cpp_keywords = r'\b(and|and_eq|asm|bitand|bitor|bool|catch|class|compl|const_cast|delete|dynamic_cast|explicit|export|false|friend|inline|mutable|namespace|new|not|not_eq|operator|or|or_eq|private|protected|public|reinterpret_cast|static_cast|template|this|throw|true|try|typeid|typename|using|virtual|wchar_t|xor|xor_eq)\b'
        
        patterns.append({
            'pattern': cpp_keywords,
            'color': self.COLOR_KEYWORD,
            'priority': 7
        })
        
        return patterns
    
    def _get_java_patterns(self) -> List[Dict]:
        """Get Java syntax patterns"""
        return [
            # Comments
            {'pattern': r'//.*$', 'color': self.COLOR_COMMENT, 'priority': 10},
            {'pattern': r'/\*.*?\*/', 'color': self.COLOR_COMMENT, 'priority': 10},
            
            # Strings
            {'pattern': r'"(?:[^"\\]|\\.)*"', 'color': self.COLOR_STRING, 'priority': 8},
            {'pattern': r"'(?:[^'\\]|\\.)'", 'color': self.COLOR_STRING, 'priority': 8},
            
            # Keywords
            {'pattern': r'\b(abstract|assert|boolean|break|byte|case|catch|char|class|const|continue|default|do|double|else|enum|extends|final|finally|float|for|goto|if|implements|import|instanceof|int|interface|long|native|new|package|private|protected|public|return|short|static|strictfp|super|switch|synchronized|this|throw|throws|transient|try|void|volatile|while|true|false|null)\b', 
             'color': self.COLOR_KEYWORD, 'priority': 7},
            
            # Numbers
            {'pattern': r'\b\d+\.?\d*[fFdDlL]?\b', 'color': self.COLOR_NUMBER, 'priority': 6},
            
            # Operators
            {'pattern': r'[+\-*/%=<>!&|^~]', 'color': self.COLOR_OPERATOR, 'priority': 5},
        ]
    
    def _get_rust_patterns(self) -> List[Dict]:
        """Get Rust syntax patterns"""
        return [
            # Comments
            {'pattern': r'//.*$', 'color': self.COLOR_COMMENT, 'priority': 10},
            {'pattern': r'/\*.*?\*/', 'color': self.COLOR_COMMENT, 'priority': 10},
            
            # Strings
            {'pattern': r'"(?:[^"\\]|\\.)*"', 'color': self.COLOR_STRING, 'priority': 8},
            {'pattern': r"'(?:[^'\\]|\\.)'", 'color': self.COLOR_STRING, 'priority': 8},
            
            # Keywords
            {'pattern': r'\b(as|async|await|break|const|continue|crate|dyn|else|enum|extern|false|fn|for|if|impl|in|let|loop|match|mod|move|mut|pub|ref|return|self|Self|static|struct|super|trait|true|type|unsafe|use|where|while)\b', 
             'color': self.COLOR_KEYWORD, 'priority': 7},
            
            # Types
            {'pattern': r'\b(bool|char|str|i8|i16|i32|i64|i128|isize|u8|u16|u32|u64|u128|usize|f32|f64)\b', 
             'color': self.COLOR_NUMBER, 'priority': 6},
            
            # Operators
            {'pattern': r'[+\-*/%=<>!&|^~]', 'color': self.COLOR_OPERATOR, 'priority': 5},
        ]
    
    def _get_go_patterns(self) -> List[Dict]:
        """Get Go syntax patterns"""
        return [
            # Comments
            {'pattern': r'//.*$', 'color': self.COLOR_COMMENT, 'priority': 10},
            {'pattern': r'/\*.*?\*/', 'color': self.COLOR_COMMENT, 'priority': 10},
            
            # Strings
            {'pattern': r'"(?:[^"\\]|\\.)*"', 'color': self.COLOR_STRING, 'priority': 8},
            {'pattern': r"'(?:[^'\\]|\\.)'", 'color': self.COLOR_STRING, 'priority': 8},
            {'pattern': r'`[^`]*`', 'color': self.COLOR_STRING, 'priority': 8},
            
            # Keywords
            {'pattern': r'\b(break|case|chan|const|continue|default|defer|else|fallthrough|for|func|go|goto|if|import|interface|map|package|range|return|select|struct|switch|type|var)\b', 
             'color': self.COLOR_KEYWORD, 'priority': 7},
            
            # Built-in types
            {'pattern': r'\b(bool|byte|complex64|complex128|error|float32|float64|int|int8|int16|int32|int64|rune|string|uint|uint8|uint16|uint32|uint64|uintptr)\b', 
             'color': self.COLOR_NUMBER, 'priority': 6},
            
            # Constants
            {'pattern': r'\b(true|false|iota|nil)\b', 'color': self.COLOR_KEYWORD, 'priority': 7},
            
            # Operators
            {'pattern': r'[+\-*/%=<>!&|^~]', 'color': self.COLOR_OPERATOR, 'priority': 5},
        ]

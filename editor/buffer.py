"""
Text buffer management for Axiom editor
"""

import logging
from typing import List, Optional
from pathlib import Path
import re

from .error_handler import AxiomError
from .config import Config


class TextBuffer:
    """Manages the text content and file operations"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Text content stored as list of lines
        self.lines: List[str] = [""]
        
        # File metadata
        self.filename: Optional[str] = None
        self.encoding = "utf-8"
        self.line_ending = "\n"
        
        # Buffer state
        self.modified = False
        
        # Statistics
        self.total_chars = 0
        self.total_lines = 1
    
    def load_file(self, filename: str):
        """Load file content into buffer"""
        try:
            file_path = Path(filename)
            
            # Validate file
            if not file_path.exists():
                # Create new file
                self.lines = [""]
                self.filename = str(file_path.resolve())
                self.modified = False
                self._update_stats()
                self.logger.info(f"Created new file buffer: {filename}")
                return
            
            if not file_path.is_file():
                raise AxiomError(f"'{filename}' is not a regular file")
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.config.max_file_size:
                max_mb = self.config.max_file_size // (1024 * 1024)
                raise AxiomError(f"File too large (max {max_mb}MB)")
            
            # Detect encoding
            self.encoding = self._detect_encoding(file_path)
            
            # Read file content
            with open(file_path, 'r', encoding=self.encoding, errors='replace') as f:
                content = f.read()
            
            # Detect line endings
            self._detect_line_endings(content)
            
            # Split into lines
            if content:
                self.lines = content.splitlines()
                # Ensure at least one line exists
                if not self.lines:
                    self.lines = [""]
            else:
                self.lines = [""]
            
            self.filename = str(file_path.resolve())
            self.modified = False
            self._update_stats()
            
            self.logger.info(f"Loaded file: {filename} ({len(self.lines)} lines)")
            
        except UnicodeDecodeError as e:
            raise AxiomError(f"Cannot decode file '{filename}': {e}")
        except PermissionError:
            raise AxiomError(f"Permission denied: '{filename}'")
        except OSError as e:
            raise AxiomError(f"Cannot read file '{filename}': {e}")
        except Exception as e:
            raise AxiomError(f"Failed to load file '{filename}': {e}")
    
    def save_file(self, filename: Optional[str] = None):
        """Save buffer content to file"""
        try:
            if filename:
                self.filename = filename
            
            if not self.filename:
                raise AxiomError("No filename specified")
            
            file_path = Path(self.filename)
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare content
            content = self.line_ending.join(self.lines)
            
            # Write to temporary file first for safety
            temp_file = file_path.with_suffix(file_path.suffix + '.tmp')
            
            try:
                with open(temp_file, 'w', encoding=self.encoding, newline='') as f:
                    f.write(content)
                
                # Replace original file
                temp_file.replace(file_path)
                
                self.modified = False
                self.logger.info(f"Saved file: {self.filename}")
                
            except Exception as e:
                # Clean up temp file on error
                if temp_file.exists():
                    temp_file.unlink()
                raise e
                
        except PermissionError:
            raise AxiomError(f"Permission denied: '{self.filename}'")
        except OSError as e:
            raise AxiomError(f"Cannot write file '{self.filename}': {e}")
        except Exception as e:
            raise AxiomError(f"Failed to save file '{self.filename}': {e}")
    
    def insert_char(self, line_num: int, col: int, char: str):
        """Insert a character at the specified position"""
        try:
            if not (0 <= line_num < len(self.lines)):
                raise AxiomError(f"Invalid line number: {line_num}")
            
            line = self.lines[line_num]
            
            # Validate column position
            if not (0 <= col <= len(line)):
                col = len(line)
            
            # Insert character
            self.lines[line_num] = line[:col] + char + line[col:]
            self.modified = True
            self._update_stats()
            
        except Exception as e:
            self.logger.error(f"Failed to insert character: {e}")
            raise AxiomError(f"Insert character failed: {e}")
    
    def delete_char(self, line_num: int, col: int):
        """Delete character at the specified position"""
        try:
            if not (0 <= line_num < len(self.lines)):
                return
            
            line = self.lines[line_num]
            
            if 0 <= col < len(line):
                self.lines[line_num] = line[:col] + line[col + 1:]
                self.modified = True
                self._update_stats()
                
        except Exception as e:
            self.logger.error(f"Failed to delete character: {e}")
            raise AxiomError(f"Delete character failed: {e}")
    
    def insert_newline(self, line_num: int, col: int):
        """Insert a newline at the specified position"""
        try:
            if not (0 <= line_num < len(self.lines)):
                raise AxiomError(f"Invalid line number: {line_num}")
            
            line = self.lines[line_num]
            
            # Validate column position
            if not (0 <= col <= len(line)):
                col = len(line)
            
            # Split line at cursor position
            left_part = line[:col]
            right_part = line[col:]
            
            # Replace current line with left part
            self.lines[line_num] = left_part
            
            # Insert new line with right part
            self.lines.insert(line_num + 1, right_part)
            
            self.modified = True
            self._update_stats()
            
        except Exception as e:
            self.logger.error(f"Failed to insert newline: {e}")
            raise AxiomError(f"Insert newline failed: {e}")
    
    def join_lines(self, line_num: int):
        """Join current line with the next line"""
        try:
            if not (0 <= line_num < len(self.lines) - 1):
                return
            
            # Join lines
            current_line = self.lines[line_num]
            next_line = self.lines[line_num + 1]
            
            self.lines[line_num] = current_line + next_line
            
            # Remove the next line
            del self.lines[line_num + 1]
            
            self.modified = True
            self._update_stats()
            
        except Exception as e:
            self.logger.error(f"Failed to join lines: {e}")
            raise AxiomError(f"Join lines failed: {e}")
    
    def get_line(self, line_num: int) -> str:
        """Get line content by line number"""
        if 0 <= line_num < len(self.lines):
            return self.lines[line_num]
        return ""
    
    def get_line_count(self) -> int:
        """Get total number of lines"""
        return len(self.lines)
    
    def get_char_count(self) -> int:
        """Get total number of characters"""
        return self.total_chars
    
    def find_text(self, pattern: str, start_line: int = 0, start_col: int = 0, 
                  case_sensitive: bool = True, regex: bool = False, whole_word: bool = False,
                  wrap_around: bool = True) -> Optional[tuple]:
        """Advanced text search with multiple options"""
        try:
            compiled_pattern = None
            if regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                if whole_word:
                    pattern = r'\b' + pattern + r'\b'
                compiled_pattern = re.compile(pattern, flags)
            else:
                if not case_sensitive:
                    pattern = pattern.lower()
            
            # Search from start position to end
            result = self._search_range(pattern, start_line, start_col, len(self.lines), 
                                      case_sensitive, regex, whole_word, compiled_pattern)
            
            if result:
                return result
            
            # If wrap_around is enabled and we didn't start from beginning, search from start
            if wrap_around and (start_line > 0 or start_col > 0):
                result = self._search_range(pattern, 0, 0, start_line + 1,
                                          case_sensitive, regex, whole_word, compiled_pattern)
                if result and (result[0] < start_line or (result[0] == start_line and result[1] < start_col)):
                    return result
            
            return None
            
        except re.error as e:
            raise AxiomError(f"Invalid regex pattern: {e}")
        except Exception as e:
            raise AxiomError(f"Search failed: {e}")
    
    def _search_range(self, pattern: str, start_line: int, start_col: int, end_line: int,
                     case_sensitive: bool, regex: bool, whole_word: bool, compiled_pattern=None) -> Optional[tuple]:
        """Search within a specific range"""
        for line_num in range(start_line, min(end_line, len(self.lines))):
            line = self.lines[line_num]
            search_line = line if case_sensitive else line.lower()
            
            # Start from appropriate column
            start_pos = start_col if line_num == start_line else 0
            
            if regex and compiled_pattern:
                match = compiled_pattern.search(line, start_pos)
                if match:
                    return (line_num, match.start(), match.end())
            else:
                if whole_word:
                    # Find all word boundaries for whole word search
                    import re
                    word_pattern = r'\b' + re.escape(pattern) + r'\b'
                    flags = 0 if case_sensitive else re.IGNORECASE
                    matches = list(re.finditer(word_pattern, line))
                    for match in matches:
                        if match.start() >= start_pos:
                            return (line_num, match.start(), match.end())
                else:
                    pos = search_line.find(pattern, start_pos)
                    if pos != -1:
                        return (line_num, pos, pos + len(pattern))
        
        return None
    
    def find_all_occurrences(self, pattern: str, case_sensitive: bool = True, regex: bool = False,
                           whole_word: bool = False) -> List[tuple]:
        """Find all occurrences of pattern in buffer"""
        try:
            results = []
            compiled_pattern = None
            
            if regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                if whole_word:
                    pattern = r'\b' + pattern + r'\b'
                compiled_pattern = re.compile(pattern, flags)
            
            for line_num, line in enumerate(self.lines):
                search_line = line if case_sensitive else line.lower()
                
                if regex and compiled_pattern:
                    for match in compiled_pattern.finditer(line):
                        results.append((line_num, match.start(), match.end()))
                else:
                    if whole_word:
                        word_pattern = r'\b' + re.escape(pattern) + r'\b'
                        flags = 0 if case_sensitive else re.IGNORECASE
                        for match in re.finditer(word_pattern, line):
                            results.append((line_num, match.start(), match.end()))
                    else:
                        search_pattern = pattern if case_sensitive else pattern.lower()
                        start = 0
                        while True:
                            pos = search_line.find(search_pattern, start)
                            if pos == -1:
                                break
                            results.append((line_num, pos, pos + len(pattern)))
                            start = pos + 1
            
            return results
            
        except re.error as e:
            raise AxiomError(f"Invalid regex pattern: {e}")
        except Exception as e:
            raise AxiomError(f"Search failed: {e}")
    
    def replace_all(self, old_text: str, new_text: str, case_sensitive: bool = True, 
                   regex: bool = False, whole_word: bool = False) -> int:
        """Replace all occurrences of text and return count of replacements"""
        try:
            replacement_count = 0
            
            if regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                if whole_word:
                    old_text = r'\b' + old_text + r'\b'
                compiled_pattern = re.compile(old_text, flags)
                
                for line_num in range(len(self.lines)):
                    original_line = self.lines[line_num]
                    new_line, count = compiled_pattern.subn(new_text, original_line)
                    if count > 0:
                        self.lines[line_num] = new_line
                        replacement_count += count
            else:
                if whole_word:
                    import re
                    word_pattern = r'\b' + re.escape(old_text) + r'\b'
                    flags = 0 if case_sensitive else re.IGNORECASE
                    compiled_pattern = re.compile(word_pattern, flags)
                    
                    for line_num in range(len(self.lines)):
                        original_line = self.lines[line_num]
                        new_line, count = compiled_pattern.subn(new_text, original_line)
                        if count > 0:
                            self.lines[line_num] = new_line
                            replacement_count += count
                else:
                    for line_num in range(len(self.lines)):
                        line = self.lines[line_num]
                        if case_sensitive:
                            if old_text in line:
                                count = line.count(old_text)
                                self.lines[line_num] = line.replace(old_text, new_text)
                                replacement_count += count
                        else:
                            # Case-insensitive replacement is more complex
                            lower_line = line.lower()
                            lower_old = old_text.lower()
                            if lower_old in lower_line:
                                new_line = ""
                                start = 0
                                while True:
                                    pos = lower_line.find(lower_old, start)
                                    if pos == -1:
                                        new_line += line[start:]
                                        break
                                    new_line += line[start:pos] + new_text
                                    start = pos + len(old_text)
                                    replacement_count += 1
                                self.lines[line_num] = new_line
            
            if replacement_count > 0:
                self.modified = True
                self._update_stats()
            
            return replacement_count
            
        except re.error as e:
            raise AxiomError(f"Invalid regex pattern: {e}")
        except Exception as e:
            raise AxiomError(f"Replace all failed: {e}")
    
    def replace_text(self, old_text: str, new_text: str, line_num: int, 
                     start_col: int, end_col: int):
        """Replace text in specified range"""
        try:
            if not (0 <= line_num < len(self.lines)):
                return
            
            line = self.lines[line_num]
            
            # Validate positions
            start_col = max(0, min(start_col, len(line)))
            end_col = max(start_col, min(end_col, len(line)))
            
            # Replace text
            new_line = line[:start_col] + new_text + line[end_col:]
            self.lines[line_num] = new_line
            
            self.modified = True
            self._update_stats()
            
        except Exception as e:
            raise AxiomError(f"Replace text failed: {e}")
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding"""
        try:
            # Try common encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        f.read(1024)  # Read a small chunk to test
                    return encoding
                except UnicodeDecodeError:
                    continue
            
            # Default to utf-8 with error replacement
            return 'utf-8'
            
        except Exception:
            return 'utf-8'
    
    def _detect_line_endings(self, content: str):
        """Detect line ending style"""
        if '\r\n' in content:
            self.line_ending = '\r\n'  # Windows
        elif '\r' in content:
            self.line_ending = '\r'    # Classic Mac
        else:
            self.line_ending = '\n'    # Unix/Linux
    
    def _update_stats(self):
        """Update buffer statistics"""
        self.total_lines = len(self.lines)
        self.total_chars = sum(len(line) for line in self.lines) + (self.total_lines - 1)
    
    def get_stats(self) -> dict:
        """Get buffer statistics"""
        return {
            'lines': self.total_lines,
            'characters': self.total_chars,
            'filename': self.filename,
            'encoding': self.encoding,
            'line_ending': repr(self.line_ending),
            'modified': self.modified
        }

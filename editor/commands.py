"""
Command parser and executor for Axiom editor
"""

import logging
import re
from typing import Dict, Callable, List, Optional
from pathlib import Path

from .error_handler import AxiomError


class CommandParser:
    """Parses and executes editor commands with unique Axiom syntax"""
    
    def __init__(self, editor):
        self.editor = editor
        self.logger = logging.getLogger(__name__)
        
        # Command registry
        self.commands: Dict[str, Callable] = {
            # File operations
            'o': self._cmd_open,          # :o <file> - open file
            'open': self._cmd_open,       # :open <file> - open file
            's': self._cmd_save,          # :s - save current file
            'save': self._cmd_save,       # :save - save current file
            'sa': self._cmd_save_as,      # :sa <file> - save as new file
            'saveas': self._cmd_save_as,  # :saveas <file> - save as new file
            
            # Navigation and editing
            'g': self._cmd_goto,          # :g <line> - goto line
            'goto': self._cmd_goto,       # :goto <line> - goto line
            'f': self._cmd_find,          # :f <text> - find text
            'find': self._cmd_find,       # :find <text> - find text
            'r': self._cmd_replace,       # :r <old> <new> - replace text
            'replace': self._cmd_replace, # :replace <old> <new> - replace text
            
            # Editor control
            'q': self._cmd_quit,          # :q - quit
            'quit': self._cmd_quit,       # :quit - quit
            'q!': self._cmd_force_quit,   # :q! - force quit
            'sq': self._cmd_save_quit,    # :sq - save and quit
            'wq': self._cmd_save_quit,    # :wq - save and quit (vim style)
            
            # Configuration
            'set': self._cmd_set,         # :set <option> <value> - set option
            'show': self._cmd_show,       # :show <option> - show option value
            
            # Help and information
            'help': self._cmd_help,       # :help - show help
            'h': self._cmd_help,          # :h - show help
            'info': self._cmd_info,       # :info - show file info
            'stats': self._cmd_stats,     # :stats - show buffer statistics
            
            # Advanced features
            'ln': self._cmd_line_numbers, # :ln - toggle line numbers
            'syntax': self._cmd_syntax,   # :syntax <type> - set syntax highlighting
            'enc': self._cmd_encoding,    # :enc <encoding> - set encoding
            'eol': self._cmd_line_ending, # :eol <type> - set line ending
            
            # Enhanced search and replace
            'fs': self._cmd_find_advanced,    # :fs <text> [options] - advanced find
            'ra': self._cmd_replace_all,      # :ra <old> <new> [options] - replace all
            'fn': self._cmd_find_next,        # :fn - find next occurrence
            'fp': self._cmd_find_previous,    # :fp - find previous occurrence
        }
        
        # Command aliases for ease of use
        self.aliases = {
            'w': 's',           # :w -> :s (save)
            'write': 's',       # :write -> :s
            'e': 'o',           # :e -> :o (open)
            'edit': 'o',        # :edit -> :o
            'exit': 'sq',       # :exit -> :sq (save and quit)
            'x': 'sq',          # :x -> :sq
            'numbers': 'ln',    # :numbers -> :ln
            'encoding': 'enc',  # :encoding -> :enc
        }
    
    def execute(self, command_line: str):
        """Execute a command line"""
        try:
            if not command_line.strip():
                return
            
            # Parse command and arguments
            parts = self._parse_command(command_line)
            if not parts:
                return
            
            cmd_name = parts[0].lower()
            args = parts[1:]
            
            # Check for aliases
            if cmd_name in self.aliases:
                cmd_name = self.aliases[cmd_name]
            
            # Execute command
            if cmd_name in self.commands:
                self.commands[cmd_name](args)
            else:
                raise AxiomError(f"Unknown command: {cmd_name}")
                
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            self.editor.show_message(str(e), "error")
    
    def _parse_command(self, command_line: str) -> List[str]:
        """Parse command line into command and arguments"""
        # Handle quoted arguments
        parts = []
        current_arg = ""
        in_quotes = False
        escape_next = False
        
        for char in command_line:
            if escape_next:
                current_arg += char
                escape_next = False
            elif char == '\\':
                escape_next = True
            elif char == '"':
                in_quotes = not in_quotes
            elif char == ' ' and not in_quotes:
                if current_arg:
                    parts.append(current_arg)
                    current_arg = ""
            else:
                current_arg += char
        
        if current_arg:
            parts.append(current_arg)
        
        return parts
    
    # File operation commands
    def _cmd_open(self, args: List[str]):
        """Open file command"""
        if not args:
            raise AxiomError("Usage: :o <filename>")
        
        filename = args[0]
        self.editor.open_file(filename)
    
    def _cmd_save(self, args: List[str]):
        """Save file command"""
        if args:
            # Save as specific filename
            filename = args[0]
            self.editor.save_file(filename)
        else:
            # Save current file
            self.editor.save_file()
    
    def _cmd_save_as(self, args: List[str]):
        """Save as command"""
        if not args:
            raise AxiomError("Usage: :sa <filename>")
        
        filename = args[0]
        self.editor.save_file(filename)
    
    # Navigation commands
    def _cmd_goto(self, args: List[str]):
        """Go to line command"""
        if not args:
            raise AxiomError("Usage: :g <line_number>")
        
        try:
            line_num = int(args[0]) - 1  # Convert to 0-based index
            if line_num < 0:
                raise ValueError("Line number must be positive")
            
            max_line = len(self.editor.buffer.lines) - 1
            if line_num > max_line:
                line_num = max_line
            
            self.editor.cursor_y = line_num
            self.editor.cursor_x = 0
            self.editor._ensure_cursor_visible()
            
            self.editor.show_message(f"Moved to line {line_num + 1}", "info")
            
        except ValueError:
            raise AxiomError("Invalid line number")
    
    def _cmd_find(self, args: List[str]):
        """Find text command"""
        if not args:
            raise AxiomError("Usage: :f <search_text>")
        
        search_text = " ".join(args)
        
        # Store search parameters for find next/previous (basic search)
        self.editor.last_search = {
            'text': search_text,
            'case_sensitive': True,
            'regex': False,
            'whole_word': False
        }
        
        # Start search from current cursor position
        result = self.editor.buffer.find_text(
            search_text, 
            self.editor.cursor_y, 
            self.editor.cursor_x + 1
        )
        
        if result:
            line_num, start_col, end_col = result
            self.editor.cursor_y = line_num
            self.editor.cursor_x = start_col
            self.editor._ensure_cursor_visible()
            self.editor.show_message(f"Found '{search_text}' at line {line_num + 1}", "info")
        else:
            # Search from beginning
            result = self.editor.buffer.find_text(search_text, 0, 0)
            if result:
                line_num, start_col, end_col = result
                self.editor.cursor_y = line_num
                self.editor.cursor_x = start_col
                self.editor._ensure_cursor_visible()
                self.editor.show_message(f"Found '{search_text}' at line {line_num + 1} (wrapped)", "info")
            else:
                self.editor.show_message(f"Text '{search_text}' not found", "warning")
    
    def _cmd_replace(self, args: List[str]):
        """Replace text command"""
        if len(args) < 2:
            raise AxiomError("Usage: :r <old_text> <new_text>")
        
        old_text = args[0]
        new_text = args[1]
        
        # Find text starting from current position
        result = self.editor.buffer.find_text(old_text, self.editor.cursor_y, self.editor.cursor_x)
        
        if result:
            line_num, start_col, end_col = result
            self.editor.buffer.replace_text(old_text, new_text, line_num, start_col, end_col)
            self.editor.cursor_y = line_num
            self.editor.cursor_x = start_col + len(new_text)
            self.editor.modified = True
            self.editor._ensure_cursor_visible()
            self.editor.show_message(f"Replaced '{old_text}' with '{new_text}'", "info")
        else:
            self.editor.show_message(f"Text '{old_text}' not found", "warning")
    
    # Editor control commands
    def _cmd_quit(self, args: List[str]):
        """Quit command"""
        self.editor.quit_editor()
    
    def _cmd_force_quit(self, args: List[str]):
        """Force quit command"""
        self.editor.quit_editor(force=True)
    
    def _cmd_save_quit(self, args: List[str]):
        """Save and quit command"""
        try:
            self.editor.save_file()
            self.editor.quit_editor(force=True)
        except Exception as e:
            self.editor.show_message(f"Cannot save and quit: {e}", "error")
    
    # Configuration commands
    def _cmd_set(self, args: List[str]):
        """Set configuration option"""
        if len(args) < 2:
            raise AxiomError("Usage: :set <option> <value>")
        
        option = args[0].lower()
        value = args[1]
        
        try:
            if option == "tabwidth":
                self.editor.config.tab_width = int(value)
                self.editor.show_message(f"Tab width set to {value}", "info")
            elif option == "encoding":
                self.editor.buffer.encoding = value
                self.editor.show_message(f"Encoding set to {value}", "info")
            elif option == "linenumbers":
                self.editor.config.show_line_numbers = value.lower() in ['true', '1', 'yes', 'on']
                state = "enabled" if self.editor.config.show_line_numbers else "disabled"
                self.editor.show_message(f"Line numbers {state}", "info")
            elif option == "spacesfortabs":
                self.editor.config.use_spaces_for_tabs = value.lower() in ['true', '1', 'yes', 'on']
                state = "enabled" if self.editor.config.use_spaces_for_tabs else "disabled"
                self.editor.show_message(f"Spaces for tabs {state}", "info")
            else:
                raise AxiomError(f"Unknown option: {option}")
                
        except ValueError as e:
            raise AxiomError(f"Invalid value for {option}: {value}")
    
    def _cmd_show(self, args: List[str]):
        """Show configuration option"""
        if not args:
            # Show all options
            config_info = [
                f"Tab width: {self.editor.config.tab_width}",
                f"Show line numbers: {self.editor.config.show_line_numbers}",
                f"Use spaces for tabs: {self.editor.config.use_spaces_for_tabs}",
                f"Encoding: {self.editor.buffer.encoding}",
                f"Line ending: {repr(self.editor.buffer.line_ending)}",
            ]
            self.editor.show_message(" | ".join(config_info), "info")
            return
        
        option = args[0].lower()
        
        if option == "tabwidth":
            self.editor.show_message(f"Tab width: {self.editor.config.tab_width}", "info")
        elif option == "encoding":
            self.editor.show_message(f"Encoding: {self.editor.buffer.encoding}", "info")
        elif option == "linenumbers":
            self.editor.show_message(f"Line numbers: {self.editor.config.show_line_numbers}", "info")
        elif option == "spacesfortabs":
            self.editor.show_message(f"Spaces for tabs: {self.editor.config.use_spaces_for_tabs}", "info")
        else:
            raise AxiomError(f"Unknown option: {option}")
    
    # Information commands
    def _cmd_help(self, args: List[str]):
        """Show help information"""
        help_text = [
            "Axiom Text Editor Commands:",
            "File: :o <file> (open), :s (save), :sa <file> (save as), :q (quit)",
            "Edit: :g <line> (goto), :f <text> (find), :r <old> <new> (replace)",
            "Advanced: :fs <text> [-i -r -w] (advanced find), :ra <old> <new> [-i -r -w] (replace all), :fn (find next), :fp (find previous)",
            "Config: :set <opt> <val>, :show <opt>, :ln (line numbers), :syntax <type>",
            "Other: :help, :info, :stats | ESC (exit command mode)"
        ]
        self.editor.show_message(" | ".join(help_text), "info")
    
    def _cmd_info(self, args: List[str]):
        """Show file information"""
        filename = self.editor.current_file or "[No File]"
        lines = len(self.editor.buffer.lines)
        chars = sum(len(line) for line in self.editor.buffer.lines)
        encoding = self.editor.buffer.encoding
        modified = "[Modified]" if self.editor.modified else "[Saved]"
        
        info = f"File: {filename} | Lines: {lines} | Chars: {chars} | Encoding: {encoding} | {modified}"
        self.editor.show_message(info, "info")
    
    def _cmd_stats(self, args: List[str]):
        """Show buffer statistics"""
        stats = self.editor.buffer.get_stats()
        info = f"Lines: {stats['lines']} | Chars: {stats['characters']} | Encoding: {stats['encoding']}"
        self.editor.show_message(info, "info")
    
    # Feature toggle commands
    def _cmd_line_numbers(self, args: List[str]):
        """Toggle line numbers"""
        self.editor.config.show_line_numbers = not self.editor.config.show_line_numbers
        state = "enabled" if self.editor.config.show_line_numbers else "disabled"
        self.editor.show_message(f"Line numbers {state}", "info")
    
    def _cmd_syntax(self, args: List[str]):
        """Set syntax highlighting type"""
        if not args:
            current = self.editor.syntax_highlighter.get_current_syntax()
            self.editor.show_message(f"Current syntax: {current or 'auto-detect'}", "info")
            return
        
        syntax_type = args[0].lower()
        self.editor.syntax_highlighter.set_syntax_type(syntax_type)
        self.editor.show_message(f"Syntax highlighting set to: {syntax_type}", "info")
    
    def _cmd_encoding(self, args: List[str]):
        """Set file encoding"""
        if not args:
            self.editor.show_message(f"Current encoding: {self.editor.buffer.encoding}", "info")
            return
        
        encoding = args[0]
        try:
            # Test if encoding is valid
            "test".encode(encoding)
            self.editor.buffer.encoding = encoding
            self.editor.show_message(f"Encoding set to: {encoding}", "info")
        except LookupError:
            raise AxiomError(f"Unknown encoding: {encoding}")
    
    def _cmd_line_ending(self, args: List[str]):
        """Set line ending type"""
        if not args:
            current = repr(self.editor.buffer.line_ending)
            self.editor.show_message(f"Current line ending: {current}", "info")
            return
        
        eol_type = args[0].lower()
        
        if eol_type in ['unix', 'lf']:
            self.editor.buffer.line_ending = '\n'
        elif eol_type in ['windows', 'crlf']:
            self.editor.buffer.line_ending = '\r\n'
        elif eol_type in ['mac', 'cr']:
            self.editor.buffer.line_ending = '\r'
        else:
            raise AxiomError(f"Unknown line ending type: {eol_type}")
        
        self.editor.show_message(f"Line ending set to: {eol_type}", "info")
    
    # Enhanced search and replace commands
    def _cmd_find_advanced(self, args: List[str]):
        """Advanced find command with options"""
        if not args:
            raise AxiomError("Usage: :fs <text> [options: -i (case insensitive), -r (regex), -w (whole word)]")
        
        search_text = args[0]
        case_sensitive = True
        regex = False
        whole_word = False
        
        # Parse options
        for arg in args[1:]:
            if arg == "-i":
                case_sensitive = False
            elif arg == "-r":
                regex = True
            elif arg == "-w":
                whole_word = True
        
        # Store search parameters for find next/previous
        self.editor.last_search = {
            'text': search_text,
            'case_sensitive': case_sensitive,
            'regex': regex,
            'whole_word': whole_word
        }
        
        # Start search from current cursor position
        result = self.editor.buffer.find_text(
            search_text, 
            self.editor.cursor_y, 
            self.editor.cursor_x + 1,
            case_sensitive=case_sensitive,
            regex=regex,
            whole_word=whole_word
        )
        
        if result:
            line_num, start_col, end_col = result
            self.editor.cursor_y = line_num
            self.editor.cursor_x = start_col
            self.editor._ensure_cursor_visible()
            
            options_str = []
            if not case_sensitive:
                options_str.append("case-insensitive")
            if regex:
                options_str.append("regex")
            if whole_word:
                options_str.append("whole word")
            
            options_text = f" ({', '.join(options_str)})" if options_str else ""
            self.editor.show_message(f"Found '{search_text}' at line {line_num + 1}{options_text}", "info")
        else:
            self.editor.show_message(f"Text '{search_text}' not found", "warning")
    
    def _cmd_replace_all(self, args: List[str]):
        """Replace all occurrences with options"""
        if len(args) < 2:
            raise AxiomError("Usage: :ra <old_text> <new_text> [options: -i (case insensitive), -r (regex), -w (whole word)]")
        
        old_text = args[0]
        new_text = args[1]
        case_sensitive = True
        regex = False
        whole_word = False
        
        # Parse options
        for arg in args[2:]:
            if arg == "-i":
                case_sensitive = False
            elif arg == "-r":
                regex = True
            elif arg == "-w":
                whole_word = True
        
        try:
            count = self.editor.buffer.replace_all(
                old_text, new_text,
                case_sensitive=case_sensitive,
                regex=regex,
                whole_word=whole_word
            )
            
            if count > 0:
                self.editor.modified = True
                options_str = []
                if not case_sensitive:
                    options_str.append("case-insensitive")
                if regex:
                    options_str.append("regex")
                if whole_word:
                    options_str.append("whole word")
                
                options_text = f" ({', '.join(options_str)})" if options_str else ""
                self.editor.show_message(f"Replaced {count} occurrences{options_text}", "info")
            else:
                self.editor.show_message(f"No occurrences of '{old_text}' found", "warning")
                
        except Exception as e:
            self.editor.show_message(f"Replace failed: {e}", "error")
    
    def _cmd_find_next(self, args: List[str]):
        """Find next occurrence of last search"""
        if not hasattr(self.editor, 'last_search'):
            self.editor.show_message("No previous search. Use :f or :fs first", "warning")
            return
        
        search_params = self.editor.last_search
        
        # Search from next position
        result = self.editor.buffer.find_text(
            search_params['text'], 
            self.editor.cursor_y, 
            self.editor.cursor_x + 1,
            case_sensitive=search_params['case_sensitive'],
            regex=search_params['regex'],
            whole_word=search_params['whole_word']
        )
        
        if result:
            line_num, start_col, end_col = result
            self.editor.cursor_y = line_num
            self.editor.cursor_x = start_col
            self.editor._ensure_cursor_visible()
            self.editor.show_message(f"Found next '{search_params['text']}' at line {line_num + 1}", "info")
        else:
            self.editor.show_message(f"No more occurrences of '{search_params['text']}'", "warning")
    
    def _cmd_find_previous(self, args: List[str]):
        """Find previous occurrence of last search"""
        if not hasattr(self.editor, 'last_search'):
            self.editor.show_message("No previous search. Use :f or :fs first", "warning")
            return
        
        search_params = self.editor.last_search
        
        # Search backwards from current position
        # This is a simplified backward search - we'll search from beginning and find the last match before cursor
        all_results = self.editor.buffer.find_all_occurrences(
            search_params['text'],
            case_sensitive=search_params['case_sensitive'],
            regex=search_params['regex'],
            whole_word=search_params['whole_word']
        )
        
        # Find the last result before current cursor position
        previous_result = None
        for line_num, start_col, end_col in all_results:
            if line_num < self.editor.cursor_y or (line_num == self.editor.cursor_y and start_col < self.editor.cursor_x):
                previous_result = (line_num, start_col, end_col)
            else:
                break
        
        if previous_result:
            line_num, start_col, end_col = previous_result
            self.editor.cursor_y = line_num
            self.editor.cursor_x = start_col
            self.editor._ensure_cursor_visible()
            self.editor.show_message(f"Found previous '{search_params['text']}' at line {line_num + 1}", "info")
        else:
            self.editor.show_message(f"No previous occurrences of '{search_params['text']}'", "warning")

"""
Core editor functionality for Axiom text editor
"""

import curses
import curses.textpad
import logging
from typing import Optional, List, Tuple
from pathlib import Path

from .buffer import TextBuffer
from .commands import CommandParser
from .syntax import SyntaxHighlighter
from .error_handler import ErrorHandler, AxiomError
from .config import Config


class AxiomEditor:
    """Main editor class that handles the terminal interface and user interaction"""
    
    def __init__(self, stdscr, config: Config, error_handler: ErrorHandler):
        self.stdscr = stdscr
        self.config = config
        self.error_handler = error_handler
        self.logger = logging.getLogger(__name__)
        
        # Initialize curses settings
        self._setup_curses()
        
        # Editor state
        self.running = True
        self.current_file = None
        self.modified = False
        
        # Initialize components
        self.buffer = TextBuffer(self.config)
        self.command_parser = CommandParser(self)
        self.syntax_highlighter = SyntaxHighlighter()
        
        # Terminal dimensions
        self.height, self.width = self.stdscr.getmaxyx()
        
        # Status and command line
        self.status_line = self.height - 2
        self.command_line = self.height - 1
        
        # Cursor and view position
        self.cursor_x = 0
        self.cursor_y = 0
        self.scroll_x = 0
        self.scroll_y = 0
        
        # Mode tracking
        self.command_mode = False
        self.command_buffer = ""
        
        # Message display
        self.message = ""
        self.message_type = "info"  # info, warning, error
    
    def _setup_curses(self):
        """Setup curses terminal settings"""
        try:
            # Clear screen
            self.stdscr.clear()
            
            # Don't echo keys to screen
            curses.noecho()
            
            # React to keys instantly
            curses.cbreak()
            
            # Enable keypad
            self.stdscr.keypad(True)
            
            # Try to enable colors
            if curses.has_colors():
                curses.start_color()
                curses.use_default_colors()
                
                # Define color pairs
                curses.init_pair(1, curses.COLOR_WHITE, -1)      # Normal text
                curses.init_pair(2, curses.COLOR_BLUE, -1)       # Keywords
                curses.init_pair(3, curses.COLOR_GREEN, -1)      # Strings
                curses.init_pair(4, curses.COLOR_YELLOW, -1)     # Comments
                curses.init_pair(5, curses.COLOR_RED, -1)        # Errors
                curses.init_pair(6, curses.COLOR_CYAN, -1)       # Status
                curses.init_pair(7, curses.COLOR_MAGENTA, -1)    # Line numbers
            
            # Hide cursor initially
            curses.curs_set(0)
            
        except Exception as e:
            raise AxiomError(f"Failed to setup terminal: {e}")
    
    def run(self):
        """Main editor loop"""
        try:
            self.show_message("Axiom Text Editor v1.0.0 - Type :help for commands", "info")
            
            while self.running:
                # Update terminal size
                self._update_dimensions()
                
                # Refresh display
                self._refresh_display()
                
                # Handle input
                self._handle_input()
                
        except Exception as e:
            self.error_handler.handle_error(e, "Editor main loop error")
        finally:
            self._cleanup()
    
    def _update_dimensions(self):
        """Update terminal dimensions if changed"""
        try:
            new_height, new_width = self.stdscr.getmaxyx()
            if new_height != self.height or new_width != self.width:
                self.height = new_height
                self.width = new_width
                self.status_line = self.height - 2
                self.command_line = self.height - 1
                self.stdscr.clear()
        except Exception:
            pass  # Ignore dimension update errors
    
    def _refresh_display(self):
        """Refresh the entire display"""
        try:
            self.stdscr.clear()
            
            # Display text content
            self._display_text()
            
            # Display status line
            self._display_status()
            
            # Display command line or message
            if self.command_mode:
                self._display_command_line()
            else:
                self._display_message()
            
            # Update cursor position
            self._update_cursor()
            
            self.stdscr.refresh()
            
        except Exception as e:
            self.logger.error(f"Display refresh error: {e}")
    
    def _display_text(self):
        """Display the text content with syntax highlighting"""
        try:
            visible_lines = self.status_line
            
            for i in range(visible_lines):
                line_num = self.scroll_y + i
                
                # Display line number
                if self.config.show_line_numbers:
                    line_str = f"{line_num + 1:4d} "
                    try:
                        self.stdscr.addstr(i, 0, line_str, curses.color_pair(7))
                    except curses.error:
                        pass
                    start_col = 5
                else:
                    start_col = 0
                
                # Get line content
                if line_num < len(self.buffer.lines):
                    line = self.buffer.lines[line_num]
                    
                    # Apply horizontal scrolling
                    if self.scroll_x < len(line):
                        visible_line = line[self.scroll_x:]
                        
                        # Truncate to fit screen
                        max_chars = self.width - start_col
                        if len(visible_line) > max_chars:
                            visible_line = visible_line[:max_chars]
                        
                        # Apply enhanced syntax highlighting
                        if self.current_file:
                            cursor_col = self.cursor_x - self.scroll_x if i == self.cursor_y - self.scroll_y else -1
                            highlighted = self.syntax_highlighter.highlight_line(
                                visible_line, self.current_file, line_number=line_num, cursor_col=cursor_col
                            )
                            self._display_highlighted_line(i, start_col, highlighted)
                        else:
                            try:
                                self.stdscr.addstr(i, start_col, visible_line)
                            except curses.error:
                                pass
        
        except Exception as e:
            self.logger.error(f"Text display error: {e}")
    
    def _display_highlighted_line(self, row, start_col, highlighted_segments):
        """Display a line with syntax highlighting"""
        col = start_col
        for text, color_pair in highlighted_segments:
            if col >= self.width:
                break
            
            # Truncate text if it goes beyond screen width
            if col + len(text) > self.width:
                text = text[:self.width - col]
            
            try:
                self.stdscr.addstr(row, col, text, curses.color_pair(color_pair))
                col += len(text)
            except curses.error:
                break
    
    def _display_status(self):
        """Display status line"""
        try:
            # Prepare status information
            mode = "COMMAND" if self.command_mode else "EDIT"
            file_info = self.current_file or "[No File]"
            
            if self.modified:
                file_info += " [Modified]"
            
            position = f"Ln {self.cursor_y + 1}, Col {self.cursor_x + 1}"
            
            # Create status line
            left_status = f" {mode} | {file_info}"
            right_status = f"{position} "
            
            # Calculate spacing
            available_space = self.width - len(left_status) - len(right_status)
            if available_space > 0:
                status_line = left_status + " " * available_space + right_status
            else:
                status_line = left_status[:self.width]
            
            # Display status with highlighting
            try:
                self.stdscr.addstr(
                    self.status_line, 0, status_line[:self.width],
                    curses.color_pair(6) | curses.A_REVERSE
                )
            except curses.error:
                pass
        
        except Exception as e:
            self.logger.error(f"Status display error: {e}")
    
    def _display_command_line(self):
        """Display command line input"""
        try:
            command_display = f":{self.command_buffer}"
            try:
                self.stdscr.addstr(self.command_line, 0, command_display[:self.width])
            except curses.error:
                pass
        except Exception as e:
            self.logger.error(f"Command line display error: {e}")
    
    def _display_message(self):
        """Display message line"""
        try:
            if self.message:
                color_pair = 1  # Default
                if self.message_type == "error":
                    color_pair = 5
                elif self.message_type == "warning":
                    color_pair = 4
                elif self.message_type == "info":
                    color_pair = 6
                
                try:
                    self.stdscr.addstr(
                        self.command_line, 0, self.message[:self.width],
                        curses.color_pair(color_pair)
                    )
                except curses.error:
                    pass
        except Exception as e:
            self.logger.error(f"Message display error: {e}")
    
    def _update_cursor(self):
        """Update cursor position on screen"""
        try:
            if self.command_mode:
                # Cursor in command line
                cursor_col = min(len(self.command_buffer) + 1, self.width - 1)
                curses.curs_set(1)
                self.stdscr.move(self.command_line, cursor_col)
            else:
                # Cursor in text area
                display_y = self.cursor_y - self.scroll_y
                display_x = self.cursor_x - self.scroll_x
                
                # Add offset for line numbers
                if self.config.show_line_numbers:
                    display_x += 5
                
                # Ensure cursor is visible
                if (0 <= display_y < self.status_line and 
                    0 <= display_x < self.width):
                    curses.curs_set(1)
                    self.stdscr.move(display_y, display_x)
                else:
                    curses.curs_set(0)
        
        except Exception as e:
            self.logger.error(f"Cursor update error: {e}")
    
    def _handle_input(self):
        """Handle keyboard input"""
        try:
            key = self.stdscr.getch()
            
            if self.command_mode:
                self._handle_command_input(key)
            else:
                self._handle_edit_input(key)
        
        except Exception as e:
            self.error_handler.handle_error(e, "Input handling error")
    
    def _handle_command_input(self, key):
        """Handle input in command mode"""
        if key == ord('\n') or key == ord('\r'):
            # Execute command
            self._execute_command()
        elif key == 27:  # ESC
            # Exit command mode
            self.command_mode = False
            self.command_buffer = ""
            self.clear_message()
        elif key == curses.KEY_BACKSPACE or key == 127:
            # Backspace
            if self.command_buffer:
                self.command_buffer = self.command_buffer[:-1]
        elif 32 <= key <= 126:  # Printable characters
            self.command_buffer += chr(key)
    
    def _handle_edit_input(self, key):
        """Handle input in edit mode"""
        if key == ord(':'):
            # Enter command mode
            self.command_mode = True
            self.command_buffer = ""
            self.clear_message()
        elif key == curses.KEY_UP:
            self._move_cursor_up()
        elif key == curses.KEY_DOWN:
            self._move_cursor_down()
        elif key == curses.KEY_LEFT:
            self._move_cursor_left()
        elif key == curses.KEY_RIGHT:
            self._move_cursor_right()
        elif key == curses.KEY_HOME:
            self._move_cursor_home()
        elif key == curses.KEY_END:
            self._move_cursor_end()
        elif key == curses.KEY_PPAGE:  # Page Up
            self._move_page_up()
        elif key == curses.KEY_NPAGE:  # Page Down
            self._move_page_down()
        elif key == ord('\n') or key == ord('\r'):
            self._insert_newline()
        elif key == curses.KEY_BACKSPACE or key == 127:
            self._delete_char_back()
        elif key == curses.KEY_DC:  # Delete
            self._delete_char_forward()
        elif key == 9:  # Tab
            self._insert_tab()
        elif 32 <= key <= 126:  # Printable characters
            self._insert_char(chr(key))
        elif key == 3:  # Ctrl+C
            self.quit_editor()
    
    def _execute_command(self):
        """Execute a command"""
        try:
            self.command_mode = False
            command = self.command_buffer.strip()
            self.command_buffer = ""
            
            if command:
                self.command_parser.execute(command)
            
        except Exception as e:
            self.show_message(f"Command error: {e}", "error")
    
    # Movement methods
    def _move_cursor_up(self):
        if self.cursor_y > 0:
            self.cursor_y -= 1
            self._adjust_cursor_x()
            self._ensure_cursor_visible()
    
    def _move_cursor_down(self):
        if self.cursor_y < len(self.buffer.lines) - 1:
            self.cursor_y += 1
            self._adjust_cursor_x()
            self._ensure_cursor_visible()
    
    def _move_cursor_left(self):
        if self.cursor_x > 0:
            self.cursor_x -= 1
        elif self.cursor_y > 0:
            self.cursor_y -= 1
            self.cursor_x = len(self.buffer.lines[self.cursor_y])
        self._ensure_cursor_visible()
    
    def _move_cursor_right(self):
        current_line_length = len(self.buffer.lines[self.cursor_y])
        if self.cursor_x < current_line_length:
            self.cursor_x += 1
        elif self.cursor_y < len(self.buffer.lines) - 1:
            self.cursor_y += 1
            self.cursor_x = 0
        self._ensure_cursor_visible()
    
    def _move_cursor_home(self):
        self.cursor_x = 0
        self._ensure_cursor_visible()
    
    def _move_cursor_end(self):
        self.cursor_x = len(self.buffer.lines[self.cursor_y])
        self._ensure_cursor_visible()
    
    def _move_page_up(self):
        self.cursor_y = max(0, self.cursor_y - (self.status_line - 1))
        self._adjust_cursor_x()
        self._ensure_cursor_visible()
    
    def _move_page_down(self):
        max_y = len(self.buffer.lines) - 1
        self.cursor_y = min(max_y, self.cursor_y + (self.status_line - 1))
        self._adjust_cursor_x()
        self._ensure_cursor_visible()
    
    def _adjust_cursor_x(self):
        """Adjust cursor X position to be within current line bounds"""
        if self.cursor_y < len(self.buffer.lines):
            line_length = len(self.buffer.lines[self.cursor_y])
            self.cursor_x = min(self.cursor_x, line_length)
    
    def _ensure_cursor_visible(self):
        """Ensure cursor is visible by adjusting scroll position"""
        # Vertical scrolling
        if self.cursor_y < self.scroll_y:
            self.scroll_y = self.cursor_y
        elif self.cursor_y >= self.scroll_y + self.status_line:
            self.scroll_y = self.cursor_y - self.status_line + 1
        
        # Horizontal scrolling
        visible_width = self.width
        if self.config.show_line_numbers:
            visible_width -= 5
        
        if self.cursor_x < self.scroll_x:
            self.scroll_x = self.cursor_x
        elif self.cursor_x >= self.scroll_x + visible_width:
            self.scroll_x = self.cursor_x - visible_width + 1
        
        # Ensure scroll positions are non-negative
        self.scroll_x = max(0, self.scroll_x)
        self.scroll_y = max(0, self.scroll_y)
    
    # Text editing methods
    def _insert_char(self, char):
        """Insert a character at cursor position"""
        self.buffer.insert_char(self.cursor_y, self.cursor_x, char)
        self.cursor_x += 1
        self.modified = True
        self._ensure_cursor_visible()
    
    def _insert_newline(self):
        """Insert a newline at cursor position"""
        self.buffer.insert_newline(self.cursor_y, self.cursor_x)
        self.cursor_y += 1
        self.cursor_x = 0
        self.modified = True
        self._ensure_cursor_visible()
    
    def _insert_tab(self):
        """Insert tab or spaces at cursor position"""
        if self.config.use_spaces_for_tabs:
            spaces = " " * self.config.tab_width
            for _ in range(self.config.tab_width):
                self._insert_char(' ')
        else:
            self._insert_char('\t')
    
    def _delete_char_back(self):
        """Delete character before cursor (backspace)"""
        if self.cursor_x > 0:
            self.buffer.delete_char(self.cursor_y, self.cursor_x - 1)
            self.cursor_x -= 1
            self.modified = True
        elif self.cursor_y > 0:
            # Join with previous line
            prev_line_length = len(self.buffer.lines[self.cursor_y - 1])
            self.buffer.join_lines(self.cursor_y - 1)
            self.cursor_y -= 1
            self.cursor_x = prev_line_length
            self.modified = True
        self._ensure_cursor_visible()
    
    def _delete_char_forward(self):
        """Delete character at cursor position"""
        current_line_length = len(self.buffer.lines[self.cursor_y])
        if self.cursor_x < current_line_length:
            self.buffer.delete_char(self.cursor_y, self.cursor_x)
            self.modified = True
        elif self.cursor_y < len(self.buffer.lines) - 1:
            # Join with next line
            self.buffer.join_lines(self.cursor_y)
            self.modified = True
        self._ensure_cursor_visible()
    
    # File operations
    def open_file(self, filename: str):
        """Open a file"""
        try:
            self.buffer.load_file(filename)
            self.current_file = filename
            self.modified = False
            self.cursor_x = 0
            self.cursor_y = 0
            self.scroll_x = 0
            self.scroll_y = 0
            self.show_message(f"Opened '{filename}'", "info")
        except Exception as e:
            self.show_message(f"Failed to open '{filename}': {e}", "error")
    
    def save_file(self, filename: Optional[str] = None):
        """Save current buffer to file"""
        try:
            if filename:
                self.current_file = filename
            
            if not self.current_file:
                self.show_message("No filename specified", "error")
                return
            
            self.buffer.save_file(self.current_file)
            self.modified = False
            self.show_message(f"Saved '{self.current_file}'", "info")
            
        except Exception as e:
            self.show_message(f"Failed to save: {e}", "error")
    
    def quit_editor(self, force: bool = False):
        """Quit the editor"""
        if self.modified and not force:
            self.show_message("Unsaved changes! Use :q! to force quit or :sq to save and quit", "warning")
            return
        
        self.running = False
    
    def show_message(self, message: str, msg_type: str = "info"):
        """Show a message to the user"""
        self.message = message
        self.message_type = msg_type
        self.logger.info(f"Message ({msg_type}): {message}")
    
    def clear_message(self):
        """Clear the current message"""
        self.message = ""
        self.message_type = "info"
    
    def _cleanup(self):
        """Cleanup curses on exit"""
        try:
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
            curses.endwin()
        except Exception:
            pass  # Ignore cleanup errors

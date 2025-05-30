"""
Advanced error handling system for Axiom editor
"""

import logging
import traceback
import sys
from typing import Optional, Any, Dict, List
from pathlib import Path
import os


class AxiomError(Exception):
    """Base exception class for Axiom editor errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "AXIOM_ERROR"
        self.context = context or {}
        
    def __str__(self):
        return self.message


class FileError(AxiomError):
    """File operation related errors"""
    pass


class BufferError(AxiomError):
    """Text buffer related errors"""
    pass


class CommandError(AxiomError):
    """Command parsing and execution errors"""
    pass


class TerminalError(AxiomError):
    """Terminal/curses related errors"""
    pass


class ConfigError(AxiomError):
    """Configuration related errors"""
    pass


class ErrorHandler:
    """Advanced error handling with logging, recovery, and user feedback"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        
        # Error statistics
        self.error_count = 0
        self.warning_count = 0
        self.error_history: List[Dict[str, Any]] = []
        
        # Recovery strategies
        self.recovery_strategies = {
            FileError: self._recover_file_error,
            BufferError: self._recover_buffer_error,
            CommandError: self._recover_command_error,
            TerminalError: self._recover_terminal_error,
            ConfigError: self._recover_config_error,
        }
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup error logging configuration"""
        try:
            # Create logs directory if it doesn't exist
            log_dir = Path.home() / '.axiom' / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Setup file handler
            log_file = log_dir / 'axiom_errors.log'
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.WARNING)
            
            # Setup formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.DEBUG if self.debug else logging.WARNING)
            
        except Exception as e:
            # Fallback to stderr if logging setup fails
            print(f"Warning: Could not setup error logging: {e}", file=sys.stderr)
    
    def handle_error(self, error: Exception, context: str = "", 
                    recovery_attempted: bool = False) -> bool:
        """
        Handle an error with logging, user notification, and recovery attempts
        Returns True if error was recovered, False otherwise
        """
        try:
            # Increment error count
            self.error_count += 1
            
            # Determine error type and create appropriate error object
            if isinstance(error, AxiomError):
                axiom_error = error
            else:
                # Wrap non-Axiom errors
                error_type = type(error).__name__
                axiom_error = AxiomError(
                    f"{error_type}: {str(error)}",
                    error_code=f"WRAPPED_{error_type.upper()}",
                    context={"original_error": error, "context": context}
                )
            
            # Log the error
            self._log_error(axiom_error, context)
            
            # Record in error history
            self._record_error(axiom_error, context)
            
            # Attempt recovery if not already attempted
            if not recovery_attempted:
                recovery_success = self._attempt_recovery(axiom_error)
                if recovery_success:
                    self.logger.info(f"Successfully recovered from error: {axiom_error.message}")
                    return True
            
            # Generate user-friendly error message
            user_message = self._generate_user_message(axiom_error)
            
            if self.debug:
                # Include technical details in debug mode
                user_message += f" [Debug: {axiom_error.error_code}]"
            
            return False
            
        except Exception as meta_error:
            # Error in error handling - log to stderr and continue
            print(f"Meta-error in error handler: {meta_error}", file=sys.stderr)
            if self.debug:
                traceback.print_exc()
            return False
    
    def handle_warning(self, message: str, context: str = ""):
        """Handle a warning condition"""
        self.warning_count += 1
        
        warning_info = {
            'type': 'warning',
            'message': message,
            'context': context,
            'timestamp': self._get_timestamp()
        }
        
        self.error_history.append(warning_info)
        self.logger.warning(f"Warning in {context}: {message}")
    
    def _log_error(self, error: AxiomError, context: str):
        """Log error details"""
        log_message = f"Error in {context}: {error.message}"
        
        if error.context:
            log_message += f" | Context: {error.context}"
        
        self.logger.error(log_message)
        
        if self.debug:
            # Log full traceback in debug mode
            self.logger.debug("Full traceback:", exc_info=True)
    
    def _record_error(self, error: AxiomError, context: str):
        """Record error in history for analysis"""
        error_info = {
            'type': 'error',
            'error_code': error.error_code,
            'message': error.message,
            'context': context,
            'timestamp': self._get_timestamp(),
            'error_context': error.context
        }
        
        self.error_history.append(error_info)
        
        # Keep only last 100 errors to prevent memory issues
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
    
    def _attempt_recovery(self, error: AxiomError) -> bool:
        """Attempt to recover from error using appropriate strategy"""
        error_type = type(error)
        
        # Find recovery strategy
        strategy = None
        for err_class, recovery_func in self.recovery_strategies.items():
            if isinstance(error, err_class):
                strategy = recovery_func
                break
        
        if strategy:
            try:
                return strategy(error)
            except Exception as recovery_error:
                self.logger.error(f"Recovery strategy failed: {recovery_error}")
                return False
        
        # No specific recovery strategy
        return False
    
    def _recover_file_error(self, error: FileError) -> bool:
        """Attempt to recover from file operation errors"""
        if "Permission denied" in error.message:
            # Suggest alternative file location
            return False  # Cannot auto-recover from permission issues
        
        elif "File not found" in error.message:
            # Could create empty file or suggest alternatives
            return False  # Let user decide
        
        elif "File too large" in error.message:
            # Could offer to open in read-only mode
            return False  # Requires user decision
        
        return False
    
    def _recover_buffer_error(self, error: BufferError) -> bool:
        """Attempt to recover from buffer operation errors"""
        if "Invalid line number" in error.message:
            # Could adjust cursor position to valid range
            return True  # Often recoverable
        
        elif "Insert character failed" in error.message:
            # Could skip the operation and continue
            return True
        
        return False
    
    def _recover_command_error(self, error: CommandError) -> bool:
        """Attempt to recover from command errors"""
        # Most command errors are user input errors - not recoverable
        return False
    
    def _recover_terminal_error(self, error: TerminalError) -> bool:
        """Attempt to recover from terminal errors"""
        if "Terminal not compatible" in error.message:
            # Could fall back to simpler terminal mode
            return False  # Requires environment change
        
        return False
    
    def _recover_config_error(self, error: ConfigError) -> bool:
        """Attempt to recover from configuration errors"""
        # Could reset to default configuration
        return True  # Usually recoverable with defaults
    
    def _generate_user_message(self, error: AxiomError) -> str:
        """Generate user-friendly error message"""
        # Map technical errors to user-friendly messages
        user_messages = {
            "AXIOM_ERROR": "An unexpected error occurred",
            "FILE_NOT_FOUND": "File not found",
            "PERMISSION_DENIED": "Permission denied",
            "FILE_TOO_LARGE": "File is too large to open",
            "INVALID_ENCODING": "File encoding is not supported",
            "COMMAND_NOT_FOUND": "Unknown command",
            "INVALID_SYNTAX": "Invalid command syntax",
            "TERMINAL_ERROR": "Terminal display error",
            "BUFFER_OVERFLOW": "Text buffer is full",
        }
        
        # Look for specific error patterns
        message = error.message.lower()
        
        if "permission denied" in message:
            return "Permission denied. Check file permissions."
        elif "file not found" in message or "no such file" in message:
            return "File not found. Check the file path."
        elif "file too large" in message:
            return "File is too large. Try opening a smaller file."
        elif "encoding" in message:
            return "Cannot read file. Try a different encoding."
        elif "unknown command" in message:
            return "Unknown command. Type :help for available commands."
        elif "terminal" in message:
            return "Display error. Try resizing the terminal."
        elif "invalid" in message and "line" in message:
            return "Invalid line number specified."
        
        # Use mapped message or original message
        return user_messages.get(error.error_code, error.message)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for logging"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics"""
        return {
            'total_errors': self.error_count,
            'total_warnings': self.warning_count,
            'recent_errors': len([e for e in self.error_history if e['type'] == 'error']),
            'recent_warnings': len([e for e in self.error_history if e['type'] == 'warning']),
            'history_size': len(self.error_history)
        }
    
    def get_recent_errors(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent errors from history"""
        recent = [e for e in self.error_history if e['type'] == 'error']
        return recent[-count:] if recent else []
    
    def clear_error_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.error_count = 0
        self.warning_count = 0
        self.logger.info("Error history cleared")
    
    def export_error_log(self, filename: str) -> bool:
        """Export error history to file"""
        try:
            import json
            
            export_data = {
                'statistics': self.get_error_statistics(),
                'history': self.error_history,
                'export_timestamp': self._get_timestamp()
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Error log exported to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export error log: {e}")
            return False

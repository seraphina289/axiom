#!/usr/bin/env python3
"""
Axiom Text Editor - Terminal-based text editor with unique command syntax
"""

import sys
import argparse
import curses
import logging
from pathlib import Path
from typing import Optional

from editor.core import AxiomEditor
from editor.error_handler import ErrorHandler, AxiomError
from editor.config import Config


def setup_logging():
    """Setup logging configuration for debugging"""
    logging.basicConfig(
        filename='axiom.log',
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Axiom - Terminal-based text editor with unique command syntax",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  axiom                    Start with empty buffer
  axiom file.txt          Open file.txt
  axiom --help            Show this help message

Commands in editor:
  :o <file>               Open file
  :s                      Save current file
  :sa <file>              Save as new file
  :q                      Quit editor
  :sq                     Save and quit
  :help                   Show help
        """
    )
    
    parser.add_argument(
        'filename',
        nargs='?',
        help='File to open (optional)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Axiom Text Editor v1.0.0'
    )
    
    return parser.parse_args()


def validate_terminal():
    """Validate terminal capabilities"""
    if not sys.stdout.isatty():
        raise AxiomError("Axiom requires a terminal environment")
    
    try:
        # Test curses availability
        curses.setupterm()
    except Exception as e:
        raise AxiomError(f"Terminal not compatible with curses: {e}")


def main():
    """Main entry point for Axiom editor"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Setup logging if debug mode
        if args.debug:
            setup_logging()
            logging.info("Axiom starting in debug mode")
        
        # Validate terminal environment
        validate_terminal()
        
        # Initialize configuration
        config = Config()
        
        # Initialize error handler
        error_handler = ErrorHandler(debug=args.debug)
        
        # Validate file if provided
        filename = None
        if args.filename:
            file_path = Path(args.filename)
            
            # Check if file exists or if we can create it
            if file_path.exists():
                if not file_path.is_file():
                    raise AxiomError(f"'{args.filename}' is not a regular file")
                if not file_path.stat().st_size < config.max_file_size:
                    raise AxiomError(f"File too large (max {config.max_file_size // (1024*1024)}MB)")
            else:
                # Check if we can create the file
                try:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.touch()
                    file_path.unlink()  # Remove the test file
                except Exception as e:
                    raise AxiomError(f"Cannot create file '{args.filename}': {e}")
            
            filename = str(file_path.resolve())
        
        # Initialize and run the editor
        def run_editor(stdscr):
            editor = AxiomEditor(stdscr, config, error_handler)
            if filename:
                editor.open_file(filename)
            editor.run()
        
        # Run with curses wrapper for proper cleanup
        curses.wrapper(run_editor)
        
    except KeyboardInterrupt:
        print("\nAxiom interrupted by user")
        sys.exit(130)
    except AxiomError as e:
        print(f"Axiom Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

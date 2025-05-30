# Axiom Text Editor

Axiom is a powerful, terminal-based text editor built in Python with a unique command syntax and advanced error handling. It provides a modern editing experience while maintaining the efficiency and accessibility of terminal-based tools.

## Features

### Core Functionality
- **Terminal-based interface** using curses for cross-platform compatibility
- **Unique command syntax** designed for ease of use and memorability
- **Advanced error handling** with comprehensive recovery mechanisms
- **Syntax highlighting** for popular programming languages
- **Configurable settings** with persistent configuration management

### Text Editing
- Full keyboard navigation with standard shortcuts
- Insert, delete, copy, and paste operations
- Multi-line editing with automatic indentation
- Search and replace functionality with regex support
- Undo/redo system with configurable history levels

### File Operations
- Open, save, and create new files
- Support for large files (configurable size limits)
- Multiple encoding support (UTF-8, Latin-1, etc.)
- Automatic backup creation
- Cross-platform file path handling

### Syntax Highlighting
Supports syntax highlighting for:
- Python (.py, .pyw)
- JavaScript/TypeScript (.js, .jsx, .ts, .tsx)
- HTML (.html, .htm)
- CSS (.css, .scss, .sass)
- JSON (.json)
- XML (.xml, .xsl)
- Markdown (.md, .markdown)
- Shell scripts (.sh, .bash)
- C/C++ (.c, .cpp, .h, .hpp)
- Java (.java)
- Rust (.rs)
- Go (.go)

## Installation

### One-Line Installation (Recommended)
Install Axiom with a single command using our beautiful installer:

```bash
# Download and run the installer
curl -sL https://raw.githubusercontent.com/your-repo/axiom/main/install-axiom.sh | bash

# Or run locally if you have the source
./install-axiom.sh
```

### Manual Installation
1. **Clone or download** the Axiom source code
2. **Run the installer** from the source directory:
   ```bash
   chmod +x install-axiom.sh
   ./install-axiom.sh
   ```

### Requirements
- **Python 3.8+** (automatically verified by installer)
- **Terminal with curses support** (most Unix terminals, Windows Terminal)
- **10MB disk space** for installation

### Why Axiom is Executable After Installation

The installer creates a proper executable wrapper that:
- **Resolves Python path automatically** - No need to call `python axiom.py`
- **Sets up module imports correctly** - All editor components load seamlessly  
- **Integrates with system PATH** - Available from any directory
- **Handles permissions properly** - Executable bit set correctly
- **Works across shell environments** - Bash, Zsh, Fish compatible

The installed `axiom` command is a native executable that launches the Python application with proper module resolution, making it feel like any other system command.

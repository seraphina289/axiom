#!/bin/bash

# Axiom Text Editor
# Usage: curl -sL https://raw.githubusercontent.com/seraphina289/axiom/main/install-axiom.sh | bash

set -e

# Colors for beautiful output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Display the magnificent Axiom ASCII art
show_axiom_banner() {
    clear
    echo -e "${CYAN}${BOLD}"
    cat << "EOF"

    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║    ██████╗ ██╗  ██╗██╗ ██████╗ ███╗   ███╗                                  ║
    ║   ██╔══██╗╚██╗██╔╝██║██╔═══██╗████╗ ████║                                  ║
    ║   ███████║ ╚███╔╝ ██║██║   ██║██╔████╔██║                                  ║
    ║   ██╔══██║ ██╔██╗ ██║██║   ██║██║╚██╔╝██║                                  ║
    ║   ██║  ██║██╔╝ ██╗██║╚██████╔╝██║ ╚═╝ ██║                                  ║
    ║   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝     ╚═╝                                  ║
    ║                                                                              ║
    ║   ╭─────────────────────────────────────────────────────────────────────╮   ║
    ║   │                                                                     │   ║
    ║   │        THE ULTIMATE TERMINAL TEXT EDITOR                           │   ║
    ║   │        Crafted for Developers, Built for Excellence                │   ║
    ║   │                                                                     │   ║
    ║   │    ⚡ Lightning Fast    🎨 Syntax Highlighting                      │   ║
    ║   │    🔍 Smart Search      💡 Intelligent Features                     │   ║
    ║   │    🛠️  Highly Configurable  🚀 Modern Architecture                 │   ║
    ║   │                                                                     │   ║
    ║   ╰─────────────────────────────────────────────────────────────────────╯   ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝

EOF
    echo -e "${NC}"
    echo -e "${YELLOW}${BOLD}    Revolutionizing Terminal-Based Text Editing Since 2024${NC}"
    echo -e "${CYAN}    ═══════════════════════════════════════════════════════${NC}"
    echo
}

# Elegant status messages
msg_success() { echo -e "${GREEN}${BOLD}✓${NC} $1"; }
msg_info() { echo -e "${BLUE}${BOLD}◆${NC} $1"; }
msg_warning() { echo -e "${YELLOW}${BOLD}⚠${NC} $1"; }
msg_error() { echo -e "${RED}${BOLD}✗${NC} $1"; }
msg_step() { echo -e "${MAGENTA}${BOLD}➤${NC} $1"; }

# Animated progress indicator
animate_progress() {
    local duration=$1
    local message="$2"
    local chars="⣾⣽⣻⢿⡿⣟⣯⣷"
    
    echo -n -e "${CYAN}$message${NC} "
    for i in $(seq 1 $duration); do
        for (( j=0; j<${#chars}; j++ )); do
            echo -ne "\b${chars:$j:1}"
            sleep 0.05
        done
    done
    echo -e "\b${GREEN}✓${NC}"
}

# System requirements validation
validate_system() {
    msg_step "Validating system environment"
    
    # Detect operating system
    case "$(uname -s)" in
        Linux*)  OS="Linux" ;;
        Darwin*) OS="macOS" ;;
        CYGWIN*) OS="Windows" ;;
        MINGW*)  OS="Windows" ;;
        *)       OS="Unknown" ;;
    esac
    
    msg_info "Operating System: $OS"
    
    # Validate Python installation
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VER=$(python3 --version 2>&1 | cut -d' ' -f2)
        MAJOR=$(echo $PYTHON_VER | cut -d'.' -f1)
        MINOR=$(echo $PYTHON_VER | cut -d'.' -f2)
        
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 8 ]; then
            msg_success "Python $PYTHON_VER detected"
        else
            msg_error "Python 3.8+ required, found $PYTHON_VER"
            echo
            echo -e "${RED}${BOLD}Installation cannot continue without Python 3.8+${NC}"
            echo -e "${YELLOW}Please install Python 3.8+ and retry installation${NC}"
            exit 1
        fi
    else
        msg_error "Python 3.8+ is required but not installed"
        exit 1
    fi
    
    # Verify terminal capabilities
    if python3 -c "import curses" 2>/dev/null; then
        msg_success "Terminal interface support confirmed"
    else
        msg_warning "Limited terminal support detected"
    fi
    
    # Check available space
    if command -v df >/dev/null 2>&1; then
        AVAILABLE_KB=$(df . | tail -1 | awk '{print $4}')
        if [ "$AVAILABLE_KB" -gt 10240 ]; then  # 10MB
            msg_success "Sufficient disk space available"
        else
            msg_warning "Low disk space detected"
        fi
    fi
}

# Determine optimal installation location
configure_installation() {
    msg_step "Configuring installation paths"
    
    if [ "$EUID" -eq 0 ] || [ -w "/usr/local/bin" ]; then
        INSTALL_BIN="/usr/local/bin"
        INSTALL_LIB="/usr/local/lib/axiom"
        SCOPE="system-wide"
        NEEDS_SUDO=true
    else
        mkdir -p "$HOME/.local/bin" "$HOME/.local/lib"
        INSTALL_BIN="$HOME/.local/bin"
        INSTALL_LIB="$HOME/.local/lib/axiom"
        SCOPE="user-specific"
        NEEDS_SUDO=false
    fi
    
    msg_info "Installation scope: $SCOPE"
    msg_info "Binary location: $INSTALL_BIN"
    msg_info "Library location: $INSTALL_LIB"
}

# Create the complete Axiom installation
deploy_axiom() {
    msg_step "Deploying Axiom Text Editor"
    
    # Create temporary workspace
    WORKSPACE=$(mktemp -d)
    cd "$WORKSPACE"
    
    animate_progress 8 "Preparing installation environment"
    
    # Get source directory
    SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Verify source files exist
    if [ -f "$SOURCE_DIR/axiom.py" ] && [ -d "$SOURCE_DIR/editor" ]; then
        msg_success "Source files located successfully"
        
        # Create installation structure
        mkdir -p axiom-package/editor
        
        # Copy all source files
        cp "$SOURCE_DIR/axiom.py" axiom-package/
        cp -r "$SOURCE_DIR/editor"/* axiom-package/editor/
        [ -f "$SOURCE_DIR/README.md" ] && cp "$SOURCE_DIR/README.md" axiom-package/
        
        animate_progress 6 "Processing installation files"
        
        # Create the main executable wrapper
        cat > axiom-package/axiom << 'EOF'
#!/usr/bin/env python3
"""
Axiom Text Editor - Main Executable
This wrapper ensures proper module loading and execution
"""

import sys
import os
from pathlib import Path

# Add the library directory to Python path
lib_dir = Path(__file__).parent
sys.path.insert(0, str(lib_dir))

# Import and run the main application
try:
    from axiom import main
    main()
except ImportError as e:
    print(f"Error: Axiom installation appears to be corrupted: {e}")
    print("Please reinstall Axiom to fix this issue.")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)
EOF
        
        # Make all files executable
        chmod +x axiom-package/axiom
        chmod +x axiom-package/axiom.py
        
        animate_progress 4 "Installing to system"
        
        # Install to target location
        if [ "$NEEDS_SUDO" = true ]; then
            sudo mkdir -p "$INSTALL_LIB"
            sudo cp -r axiom-package/* "$INSTALL_LIB/"
            sudo ln -sf "$INSTALL_LIB/axiom" "$INSTALL_BIN/axiom"
            sudo chmod +x "$INSTALL_BIN/axiom"
        else
            mkdir -p "$INSTALL_LIB"
            cp -r axiom-package/* "$INSTALL_LIB/"
            ln -sf "$INSTALL_LIB/axiom" "$INSTALL_BIN/axiom"
            chmod +x "$INSTALL_BIN/axiom"
        fi
        
        msg_success "Axiom deployed successfully"
        
    else
        msg_error "Source files not found in current directory"
        echo
        echo -e "${YELLOW}${BOLD}Expected files:${NC}"
        echo -e "  • axiom.py (main application)"
        echo -e "  • editor/ (module directory)"
        echo
        echo -e "${BLUE}Please run this installer from the Axiom source directory${NC}"
        exit 1
    fi
    
    # Cleanup
    cd /
    rm -rf "$WORKSPACE"
}

# Configure shell environment
setup_environment() {
    if [ "$NEEDS_SUDO" = false ]; then
        msg_step "Configuring user environment"
        
        # Check if user bin directory is in PATH
        if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
            msg_info "Adding ~/.local/bin to PATH"
            
            # Detect shell and configure appropriately
            SHELL_NAME=$(basename "$SHELL")
            case $SHELL_NAME in
                bash)
                    RC_FILE="$HOME/.bashrc"
                    ;;
                zsh)
                    RC_FILE="$HOME/.zshrc"
                    ;;
                fish)
                    RC_FILE="$HOME/.config/fish/config.fish"
                    ;;
                *)
                    RC_FILE="$HOME/.profile"
                    ;;
            esac
            
            if [ -f "$RC_FILE" ] && ! grep -q "/.local/bin" "$RC_FILE"; then
                echo '' >> "$RC_FILE"
                echo '# Added by Axiom Text Editor installer' >> "$RC_FILE"
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC_FILE"
                msg_success "PATH configured in $RC_FILE"
                msg_warning "Please restart your terminal or run: source $RC_FILE"
            fi
        else
            msg_success "PATH already properly configured"
        fi
    fi
}

# Verify installation integrity
verify_installation() {
    msg_step "Verifying installation integrity"
    
    # Test basic command execution
    if command -v axiom >/dev/null 2>&1; then
        if axiom --version >/dev/null 2>&1; then
            msg_success "Axiom executable verified and functional"
        else
            msg_warning "Axiom installed but may have runtime issues"
        fi
    else
        msg_error "Axiom command not found in PATH"
        echo
        echo -e "${YELLOW}Troubleshooting:${NC}"
        echo -e "  • Restart your terminal"
        echo -e "  • Check PATH configuration"
        echo -e "  • Try: $INSTALL_BIN/axiom --version"
        return 1
    fi
}

# Display success message and usage guide
show_completion() {
    echo
    echo -e "${GREEN}${BOLD}"
    cat << "EOF"
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║                 🎉 INSTALLATION SUCCESSFUL! 🎉                  ║
    ║                                                                  ║
    ║              Axiom Text Editor is Ready to Use                  ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    echo -e "${CYAN}${BOLD}Quick Start Commands:${NC}"
    echo -e "  ${YELLOW}axiom${NC}                    Launch with empty buffer"
    echo -e "  ${YELLOW}axiom filename.py${NC}        Open specific file"
    echo -e "  ${YELLOW}axiom --help${NC}             Display help information"
    echo
    
    echo -e "${CYAN}${BOLD}Essential Editor Commands:${NC}"
    echo -e "  ${MAGENTA}:o <file>${NC}               Open file"
    echo -e "  ${MAGENTA}:s${NC}                      Save current file"
    echo -e "  ${MAGENTA}:q${NC}                      Quit editor"
    echo -e "  ${MAGENTA}:help${NC}                   Show all commands"
    echo
    
    echo -e "${CYAN}${BOLD}Advanced Features:${NC}"
    echo -e "  ${MAGENTA}:fs <text> [-i -r -w]${NC}   Advanced search with options"
    echo -e "  ${MAGENTA}:ra <old> <new>${NC}         Replace all occurrences"
    echo -e "  ${MAGENTA}:syntax <language>${NC}      Set syntax highlighting"
    echo -e "  ${MAGENTA}:ln${NC}                     Toggle line numbers"
    echo
    
    echo -e "${CYAN}${BOLD}Supported Languages:${NC}"
    echo -e "  Python • JavaScript • HTML • CSS • JSON • XML • Markdown"
    echo -e "  Shell • C/C++ • Java • Rust • Go • and many more..."
    echo
    
    echo -e "${GREEN}${BOLD}Welcome to the future of terminal text editing!${NC}"
    echo -e "${BLUE}Happy coding with Axiom! 🚀${NC}"
    echo
}

# Handle uninstallation
uninstall_axiom() {
    msg_step "Removing Axiom Text Editor"
    
    configure_installation
    
    if [ "$NEEDS_SUDO" = true ]; then
        sudo rm -f "$INSTALL_BIN/axiom"
        sudo rm -rf "$INSTALL_LIB"
    else
        rm -f "$INSTALL_BIN/axiom"
        rm -rf "$INSTALL_LIB"
    fi
    
    msg_success "Axiom has been completely removed"
    echo -e "${BLUE}Thank you for using Axiom Text Editor!${NC}"
}

# Main installation orchestrator
main() {
    # Handle command line arguments
    case "${1:-}" in
        --help|-h)
            echo -e "${BOLD}Axiom Text Editor Installation Script${NC}"
            echo
            echo -e "${CYAN}Usage:${NC}"
            echo -e "  $0                Install Axiom Text Editor"
            echo -e "  $0 --uninstall    Remove Axiom completely"
            echo -e "  $0 --help         Show this help message"
            echo
            echo -e "${CYAN}Remote Installation:${NC}"
            echo -e "  curl -sL https://raw.githubusercontent.com/your-repo/axiom/main/install-axiom.sh | bash"
            exit 0
            ;;
        --uninstall)
            show_axiom_banner
            echo -e "${RED}${BOLD}Uninstalling Axiom Text Editor${NC}"
            echo -e "${RED}══════════════════════════════════${NC}"
            echo
            uninstall_axiom
            exit 0
            ;;
        --version|-v)
            echo "Axiom Text Editor Installer v1.0.0"
            exit 0
            ;;
    esac
    
    # Begin installation process
    show_axiom_banner
    
    echo -e "${MAGENTA}${BOLD}Starting Installation Process${NC}"
    echo -e "${MAGENTA}═══════════════════════════════════════════${NC}"
    echo
    
    validate_system
    echo
    configure_installation
    echo
    deploy_axiom
    echo
    setup_environment
    echo
    verify_installation
    echo
    show_completion
}

# Execute main function with all arguments
main "$@"

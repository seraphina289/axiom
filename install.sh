#!/bin/bash

# Axiom Text Editor - Installation Script
# Cool installer with visual effects and comprehensive setup

set -e  # Exit on any error

# Colors and styling
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# Unicode symbols
CHECKMARK="✓"
CROSS="✗"
ARROW="→"
STAR="★"
ROCKET="🚀"
GEAR="⚙️"
SPARKLE="✨"

# Configuration
AXIOM_VERSION="1.0.0"
INSTALL_DIR="$HOME/.local/bin"
AXIOM_HOME="$HOME/.axiom"
REPO_URL="https://github.com/yourusername/axiom-editor"  # Update this
PYTHON_MIN_VERSION="3.8"

# Banner function
show_banner() {
    clear
    echo -e "${PURPLE}${BOLD}"
    cat << "EOF"
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║      █████╗ ██╗  ██╗██╗ ██████╗ ███╗   ███╗                 ║
    ║     ██╔══██╗╚██╗██╔╝██║██╔═══██╗████╗ ████║                 ║
    ║     ███████║ ╚███╔╝ ██║██║   ██║██╔████╔██║                 ║
    ║     ██╔══██║ ██╔██╗ ██║██║   ██║██║╚██╔╝██║                 ║
    ║     ██║  ██║██╔╝ ██╗██║╚██████╔╝██║ ╚═╝ ██║                 ║
    ║     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝     ╚═╝                 ║
    ║                                                               ║
    ║                    TEXT EDITOR INSTALLER                     ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${RESET}"
    echo -e "${CYAN}${BOLD}                    Welcome to Axiom v${AXIOM_VERSION}${RESET}"
    echo -e "${DIM}              Terminal-based text editor with unique command syntax${RESET}"
    echo
}

# Progress bar function
progress_bar() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((current * width / total))
    local remaining=$((width - completed))
    
    printf "\r${BLUE}["
    printf "%${completed}s" | tr ' ' '█'
    printf "%${remaining}s" | tr ' ' '░'
    printf "] ${percentage}%% ${RESET}"
}

# Animated spinner
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Log function
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${BLUE}${BOLD}[${timestamp}]${RESET} ${GREEN}${CHECKMARK}${RESET} $message"
            ;;
        "WARN")
            echo -e "${BLUE}${BOLD}[${timestamp}]${RESET} ${YELLOW}⚠${RESET}  $message"
            ;;
        "ERROR")
            echo -e "${BLUE}${BOLD}[${timestamp}]${RESET} ${RED}${CROSS}${RESET} $message"
            ;;
        "STEP")
            echo -e "${PURPLE}${BOLD}[${timestamp}]${RESET} ${CYAN}${ARROW}${RESET} $message"
            ;;
    esac
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Version comparison
version_ge() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# System checks
check_system() {
    log "STEP" "Performing system compatibility checks..."
    echo
    
    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log "INFO" "Operating System: Linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        log "INFO" "Operating System: macOS"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        log "WARN" "Windows detected - WSL recommended for best experience"
    else
        log "ERROR" "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    # Check Python
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        if version_ge "$PYTHON_VERSION" "$PYTHON_MIN_VERSION"; then
            log "INFO" "Python $PYTHON_VERSION detected"
        else
            log "ERROR" "Python $PYTHON_MIN_VERSION or higher required (found $PYTHON_VERSION)"
            exit 1
        fi
    else
        log "ERROR" "Python 3 not found. Please install Python 3.8 or higher"
        exit 1
    fi
    
    # Check pip
    if command_exists pip3; then
        log "INFO" "pip3 available"
    else
        log "WARN" "pip3 not found - attempting to install packages without it"
    fi
    
    # Check terminal capabilities
    if [[ -t 1 ]]; then
        log "INFO" "Terminal environment detected"
    else
        log "WARN" "Non-interactive terminal detected"
    fi
    
    # Check curses support
    python3 -c "import curses" 2>/dev/null && log "INFO" "Python curses module available" || {
        log "ERROR" "Python curses module not available"
        echo -e "${YELLOW}Try installing: sudo apt-get install python3-dev (Ubuntu/Debian)${RESET}"
        exit 1
    }
    
    echo
}

# Create directories
setup_directories() {
    log "STEP" "Setting up directories..."
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    log "INFO" "Created installation directory: $INSTALL_DIR"
    
    # Create Axiom home directory
    mkdir -p "$AXIOM_HOME"
    mkdir -p "$AXIOM_HOME/config"
    mkdir -p "$AXIOM_HOME/themes"
    mkdir -p "$AXIOM_HOME/plugins"
    mkdir -p "$AXIOM_HOME/backups"
    log "INFO" "Created Axiom home directory: $AXIOM_HOME"
    
    echo
}

# Install dependencies
install_dependencies() {
    log "STEP" "Installing Python dependencies..."
    
    # Create requirements if not exists
    cat > /tmp/axiom_requirements.txt << EOF
# Axiom Text Editor Dependencies
# Add your actual dependencies here
# colorama>=0.4.4
# keyboard>=0.13.5
EOF
    
    if command_exists pip3; then
        pip3 install -r /tmp/axiom_requirements.txt --user --quiet &
        spinner $!
        log "INFO" "Dependencies installed successfully"
    else
        log "WARN" "Skipping pip dependencies - manual installation may be required"
    fi
    
    rm -f /tmp/axiom_requirements.txt
    echo
}

# Install Axiom
install_axiom() {
    log "STEP" "Installing Axiom Text Editor..."
    
    # For this example, we'll assume the current directory contains Axiom
    if [[ -f "axiom.py" ]]; then
        # Copy main files
        cp axiom.py "$INSTALL_DIR/axiom"
        chmod +x "$INSTALL_DIR/axiom"
        
        # Copy editor modules
        if [[ -d "editor" ]]; then
            cp -r editor "$AXIOM_HOME/"
            log "INFO" "Copied editor modules"
        fi
        
        # Copy configuration files
        if [[ -f "config.json" ]]; then
            cp config.json "$AXIOM_HOME/config/"
        fi
        
        # Create default config if not exists
        cat > "$AXIOM_HOME/config/axiom.conf" << EOF
# Axiom Text Editor Configuration
# Generated by installer on $(date)

[editor]
tab_size = 4
auto_indent = true
line_numbers = true
syntax_highlighting = true
theme = default

[keybindings]
save = "Ctrl+S"
quit = "Ctrl+Q"
help = "F1"

[appearance]
color_scheme = terminal
show_status_bar = true
show_ruler = false
EOF
        
        log "INFO" "Axiom installed to $INSTALL_DIR"
    else
        log "ERROR" "axiom.py not found in current directory"
        exit 1
    fi
    
    echo
}

# Setup shell integration
setup_shell() {
    log "STEP" "Setting up shell integration..."
    
    # Detect shell
    SHELL_NAME=$(basename "$SHELL")
    
    case $SHELL_NAME in
        bash)
            SHELL_RC="$HOME/.bashrc"
            ;;
        zsh)
            SHELL_RC="$HOME/.zshrc"
            ;;
        fish)
            SHELL_RC="$HOME/.config/fish/config.fish"
            ;;
        *)
            log "WARN" "Unknown shell: $SHELL_NAME"
            SHELL_RC=""
            ;;
    esac
    
    if [[ -n "$SHELL_RC" ]] && [[ -f "$SHELL_RC" ]]; then
        # Add to PATH if not already there
        if ! grep -q "$INSTALL_DIR" "$SHELL_RC"; then
            echo "" >> "$SHELL_RC"
            echo "# Added by Axiom Text Editor installer" >> "$SHELL_RC"
            echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$SHELL_RC"
            log "INFO" "Added $INSTALL_DIR to PATH in $SHELL_RC"
        else
            log "INFO" "PATH already configured"
        fi
        
        # Add alias
        if ! grep -q "alias ax=" "$SHELL_RC"; then
            echo "alias ax='axiom'" >> "$SHELL_RC"
            log "INFO" "Added 'ax' alias for quick access"
        fi
    fi
    
    echo
}

# Create desktop entry (Linux)
create_desktop_entry() {
    if [[ "$OSTYPE" == "linux-gnu"* ]] && command_exists desktop-file-install; then
        log "STEP" "Creating desktop entry..."
        
        mkdir -p "$HOME/.local/share/applications"
        
        cat > "$HOME/.local/share/applications/axiom.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Axiom Text Editor
Comment=Terminal-based text editor with unique command syntax
Exec=$INSTALL_DIR/axiom %F
Icon=text-editor
Terminal=true
MimeType=text/plain;text/x-chdr;text/x-csrc;text/x-c++hdr;text/x-c++src;text/x-java;text/x-python;
Categories=Development;TextEditor;
Keywords=text;editor;terminal;
EOF
        
        log "INFO" "Desktop entry created"
        echo
    fi
}

# Verify installation
verify_installation() {
    log "STEP" "Verifying installation..."
    
    if [[ -x "$INSTALL_DIR/axiom" ]]; then
        log "INFO" "Axiom executable found and is executable"
    else
        log "ERROR" "Axiom executable not found or not executable"
        return 1
    fi
    
    if [[ -d "$AXIOM_HOME" ]]; then
        log "INFO" "Axiom home directory exists"
    else
        log "ERROR" "Axiom home directory not found"
        return 1
    fi
    
    # Test run (basic syntax check)
    if "$INSTALL_DIR/axiom" --version >/dev/null 2>&1; then
        log "INFO" "Axiom runs successfully"
    else
        log "WARN" "Axiom may have issues running"
    fi
    
    echo
}

# Installation complete message
installation_complete() {
    echo -e "${GREEN}${BOLD}"
    cat << "EOF"
    ╔═══════════════════════════════════════════════╗
    ║                                               ║
    ║        🎉 INSTALLATION COMPLETE! 🎉          ║
    ║                                               ║
    ╚═══════════════════════════════════════════════╝
EOF
    echo -e "${RESET}"
    
    echo -e "${WHITE}${BOLD}Axiom Text Editor v${AXIOM_VERSION} has been successfully installed!${RESET}"
    echo
    echo -e "${CYAN}${BOLD}Quick Start:${RESET}"
    echo -e "  ${YELLOW}${BOLD}axiom${RESET}           ${DIM}# Start with empty buffer${RESET}"
    echo -e "  ${YELLOW}${BOLD}axiom file.txt${RESET}  ${DIM}# Open file.txt${RESET}"
    echo -e "  ${YELLOW}${BOLD}ax${RESET}              ${DIM}# Quick alias${RESET}"
    echo
    echo -e "${CYAN}${BOLD}Key Features:${RESET}"
    echo -e "  ${GREEN}${CHECKMARK}${RESET} Unique command syntax"
    echo -e "  ${GREEN}${CHECKMARK}${RESET} Terminal-based interface"
    echo -e "  ${GREEN}${CHECKMARK}${RESET} Lightweight and fast"
    echo -e "  ${GREEN}${CHECKMARK}${RESET} Customizable configuration"
    echo
    echo -e "${CYAN}${BOLD}Configuration:${RESET}"
    echo -e "  Config: ${BLUE}$AXIOM_HOME/config/${RESET}"
    echo -e "  Logs:   ${BLUE}$AXIOM_HOME/axiom.log${RESET}"
    echo
    echo -e "${YELLOW}${BOLD}Note:${RESET} Restart your terminal or run ${CYAN}source ~/.bashrc${RESET} to use the ${BOLD}axiom${RESET} command"
    echo
    echo -e "${DIM}For help and documentation, visit: $REPO_URL${RESET}"
    echo -e "${SPARKLE} ${PURPLE}Happy coding with Axiom!${RESET} ${SPARKLE}"
    echo
}

# Uninstall function
uninstall() {
    echo -e "${RED}${BOLD}Uninstalling Axiom Text Editor...${RESET}"
    
    # Remove executable
    if [[ -f "$INSTALL_DIR/axiom" ]]; then
        rm "$INSTALL_DIR/axiom"
        log "INFO" "Removed executable"
    fi
    
    # Remove home directory (with confirmation)
    if [[ -d "$AXIOM_HOME" ]]; then
        read -p "Remove Axiom configuration and data? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$AXIOM_HOME"
            log "INFO" "Removed Axiom home directory"
        fi
    fi
    
    # Remove desktop entry
    if [[ -f "$HOME/.local/share/applications/axiom.desktop" ]]; then
        rm "$HOME/.local/share/applications/axiom.desktop"
        log "INFO" "Removed desktop entry"
    fi
    
    echo -e "${GREEN}Uninstallation complete!${RESET}"
    echo -e "${YELLOW}Note: You may need to manually remove PATH entries from your shell configuration${RESET}"
}

# Main installation function
main() {
    show_banner
    
    # Check for uninstall flag
    if [[ "$1" == "--uninstall" ]]; then
        uninstall
        exit 0
    fi
    
    # Installation steps
    echo -e "${BOLD}Starting installation process...${RESET}"
    echo
    
    check_system
    setup_directories
    install_dependencies
    install_axiom
    setup_shell
    create_desktop_entry
    
    if verify_installation; then
        installation_complete
    else
        echo -e "${RED}${BOLD}Installation completed with warnings${RESET}"
        echo -e "${YELLOW}Please check the error messages above${RESET}"
        exit 1
    fi
}

# Help function
show_help() {
    echo "Axiom Text Editor Installer"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --help        Show this help message"
    echo "  --uninstall   Remove Axiom from system"
    echo
    echo "This installer will:"
    echo "  • Check system compatibility"
    echo "  • Install Python dependencies"
    echo "  • Copy Axiom files to ~/.local/bin"
    echo "  • Set up configuration directory"
    echo "  • Add to shell PATH"
    echo "  • Create desktop entry (Linux)"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --uninstall)
        main --uninstall
        ;;
    *)
        main "$@"
        ;;
esac

#!/usr/bin/env bash

# Prevent recursive execution
if [[ -n "${_INSTALL_SETUP_SCRIPT_RUNNING}" ]]; then
    echo "Script is already running. Exiting to prevent loops."
    exit 0
fi
export _INSTALL_SETUP_SCRIPT_RUNNING=1

# --- Helper Functions ---
log_success() { echo -e "\033[32m✓ $*\033[0m"; }
log_info() { echo -e "\033[34mℹ $*\033[0m"; }
log_error() { echo -e "\033[31m✗ Error: $*\033[0m"; exit 1; }

# --- Installation Functions ---
install_zsh() {
    if command -v zsh &>/dev/null; then
        log_info "zsh already installed"
        return
    fi

    log_info "Installing zsh..."
    sudo apt-get update && sudo apt-get install -y zsh || log_error "zsh installation failed"
    
    # Set as default shell only if not already set
    if [[ "$SHELL" != "$(command -v zsh)" ]]; then
        sudo chsh -s "$(command -v zsh)" "$USER" || log_error "Changing default shell failed"
    fi
    log_success "zsh installed and set as default shell"
}

install_ohmyzsh() {
    if [[ -d "${HOME}/.oh-my-zsh" ]]; then
        log_info "Oh My Zsh already installed"
        return
    fi

    log_info "Installing Oh My Zsh..."
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended || \
        log_error "Oh My Zsh installation failed"
    log_success "Oh My Zsh installed"
}

install_homebrew() {
    if command -v brew &>/dev/null; then
        log_info "Homebrew already installed"
        return
    fi

    log_info "Installing Homebrew..."
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || \
        log_error "Homebrew installation failed"
    log_success "Homebrew installed"
}

configure_brew_path() {
    local brew_path="/home/linuxbrew/.linuxbrew/bin/brew"
    local zshrc="${HOME}/.zshrc"
    local marker="# Homebrew PATH configuration"
    local config_lines=(
        "$marker"
        'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"'
    )

    # Check if configuration exists
    if grep -qF "$marker" "$zshrc"; then
        log_info "Homebrew PATH already configured"
        return
    fi

    log_info "Adding Homebrew to PATH in .zshrc"
    printf "\n%s\n" "${config_lines[@]}" >> "$zshrc"
    eval "$("$brew_path" shellenv)"  # Apply to current session
    log_success "Homebrew PATH configured"
}

install_gum() {
    if command -v gum &>/dev/null; then
        log_info "gum already installed"
        return
    fi

    log_info "Installing gum..."
    brew install gum || log_error "gum installation failed"
    log_success "gum installed"
}

# --- Main Execution ---
main() {
    install_zsh
    install_ohmyzsh
    install_homebrew
    configure_brew_path
    install_gum
    
    log_success "Pre-installation setup completed!"
    unset _INSTALL_SETUP_SCRIPT_RUNNING
}

main
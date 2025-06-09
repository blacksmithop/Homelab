#!/bin/zsh

# Step 1: Introduction
gum style \
    --foreground 212 --border-foreground 212 --border double \
    --align center --width 50 --margin "1 2" --padding "2 4" \
    "Homelab Setup Script" "Let's get your environment ready!"

gum confirm "Ready to start the setup process?" || { echo "Setup aborted."; exit 1; }

# Step 2: Install zsh if not present
if ! command -v zsh &> /dev/null; then
    gum confirm "Install zsh?" && {
        sudo apt-get update && sudo apt-get install -y zsh || {
            echo "Failed to install zsh."
            exit 1
        }
        # Set zsh as default shell
        chsh -s $(which zsh)
        gum style --foreground 2 "zsh installed successfully."
    } || echo "Skipping zsh installation."
else
    gum style --foreground 2 "zsh is already installed."
fi

# Step 3: Install Homebrew if not present
if ! command -v brew &> /dev/null; then
    gum confirm "Install Homebrew?" && {
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || {
            echo "Failed to install Homebrew."
            exit 1
        }
        gum style --foreground 2 "Homebrew installed successfully."
    } || echo "Skipping Homebrew installation."
else
    gum style --foreground 2 "Homebrew is already installed."
fi

# Step 4: Add Homebrew to PATH
BREW_SHELLENV='eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"'
BREW_COMMENT='# Add Homebrew to PATH'

if [ -f "$HOME/.zshrc" ]; then
    # Update .zshrc if it exists
    if ! grep -Fx "$BREW_SHELLENV" "$HOME/.zshrc" > /dev/null; then
        echo "$BREW_COMMENT" >> "$HOME/.zshrc"
        echo "$BREW_SHELLENV" >> "$HOME/.zshrc"
        gum style --foreground 2 "Added Homebrew to .zshrc"
    fi
    # Source .zshrc
    source "$HOME/.zshrc"
else
    # Create .zshrc if it doesn't exist
    touch "$HOME/.zshrc"
    echo "$BREW_COMMENT" >> "$HOME/.zshrc"
    echo "$BREW_SHELLENV" >> "$HOME/.zshrc"
    source "$HOME/.zshrc"
    gum style --foreground 2 "Created and updated .zshrc with Homebrew PATH"
fi

# Apply Homebrew to current session
eval "$BREW_SHELLENV"

# Step 5: Run Docker and Tailscale installation scripts
gum confirm "Install Docker?" && zsh ./scripts/docker_install.sh || echo "Skipping Docker installation."
gum confirm "Install Tailscale?" && zsh ./scripts/tailscale_install.sh || echo "Skipping Tailscale installation."

# Step 6: Check if .env file exists and is not empty
if [ -s ".env" ]; then
    gum style --foreground 2 "Found a non-empty .env file. Proceeding..."
else
    gum style --foreground 1 "Error: .env file is missing or empty."
    gum confirm "Continue anyway?" || { echo "Setup aborted."; exit 1; }
fi

# Step 7: Run docker-compose up -d
gum confirm "Start Docker Compose services?" && docker-compose up -d || echo "Skipping Docker Compose startup."

gum style --foreground 2 "Homelab setup completed!"
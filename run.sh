#!/bin/zsh

# Step 1: Ensure zsh is the current shell
if [ -z "$ZSH_VERSION" ]; then
    echo "Current shell is not zsh. Switching to zsh..."
    exec zsh -l || {
        echo "Failed to switch to zsh. Please run 'exec zsh' manually and retry."
        exit 1
    }
fi

# Step 2: Introduction
gum style \
    --foreground 212 --border-foreground 212 --border double \
    --align center --width 50 --margin "1 2" --padding "2 4" \
    "Homelab Setup Script" "Let's get your environment ready!"

if ! gum confirm "Ready to start the setup process?"; then
    echo "Setup aborted."
    exit 1
fi

# Step 3: Install curl if not present
if ! command -v curl &> /dev/null; then
    if gum confirm "Install curl?"; then
        sudo apt-get update && sudo apt-get install -y curl || {
            echo "Failed to install curl."
            exit 1
        }
        gum style --foreground 2 "curl installed successfully."
    else
        echo "Skipping curl installation."
    fi
else
    gum style --foreground 2 "curl is already installed."
fi

# Step 4: Install zsh if not present
if ! command -v zsh &> /dev/null; then
    if gum confirm "Install zsh?"; then
        sudo apt-get update && sudo apt-get install -y zsh || {
            echo "Failed to install zsh."
            exit 1
        }
        # Set zsh as default shell
        chsh -s $(which zsh)
        gum style --foreground 2 "zsh installed successfully."
    else
        echo "Skipping zsh installation."
    fi
else
    gum style --foreground 2 "zsh is already installed."
fi

# Step 5: Install Oh My Zsh if not present
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    if gum confirm "Install Oh My Zsh?"; then
        zsh -c 'source <(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh) --unattended' || {
            echo "Failed to install Oh My Zsh."
            exit 1
        }
        gum style --foreground 2 "Oh My Zsh installed successfully."
    else
        echo "Skipping Oh My Zsh installation."
    fi
else
    gum style --foreground 2 "Oh My Zsh is already installed."
fi

# Step 6: Install Homebrew if not present
if ! command -v brew &> /dev/null; then
    if gum confirm "Install Homebrew?"; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || {
            echo "Failed to install Homebrew."
            exit 1
        }
        gum style --foreground 2 "Homebrew installed successfully."
    else
        echo "Skipping Homebrew installation."
    fi
else
    gum style --foreground 2 "Homebrew is already installed."
fi

# Step 7: Add Homebrew to PATH
BREW_SHELLENV='eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"'
BREW_COMMENT='# Add Homebrew to PATH'

if [ -f "$HOME/.zshrc" ]; then
    # Update .zshrc if it exists
    if ! grep -Fx "$BREW_SHELLENV" "$HOME/.zshrc" > /dev/null; then
        echo "$BREW_COMMENT" >> "$HOME/.zshrc"
        echo "$BREW_SHELLENV" >> "$HOME/.zshrc"
        gum style --foreground 2 "Added Homebrew to .zshrc"
    fi
else
    # Create .zshrc if it doesn't exist
    touch "$HOME/.zshrc"
    echo "$BREW_COMMENT" >> "$HOME/.zshrc"
    echo "$BREW_SHELLENV" >> "$HOME/.zshrc"
    gum style --foreground 2 "Created and updated .zshrc with Homebrew PATH"
fi

# Source .zshrc
source "$HOME/.zshrc" || {
    echo "Warning: Failed to source .zshrc. Continuing..."
}

# Apply Homebrew to current session
eval "$BREW_SHELLENV"

# Step 8: Install gum if not present
if ! command -v gum &> /dev/null; then
    if gum confirm "Install gum?"; then
        brew install gum || {
            echo "Failed to install gum."
            exit 1
        }
        gum style --foreground 2 "gum installed successfully."
    else
        echo "Skipping gum installation."
    fi
else
    gum style --foreground 2 "gum is already installed."
fi

# Step 9: Check if Docker exists
if ! command -v docker &> /dev/null; then
    if gum confirm "Install Docker?"; then
        zsh ./scripts/docker_install.sh || {
            echo "Failed to install Docker."
            exit 1
        }
        gum style --foreground 2 "Docker installed successfully."
    else
        echo "Skipping Docker installation."
    fi
else
    gum style --foreground 2 "Docker is already installed."
fi

# Step 10: Install Tailscale if not present
if gum confirm "Install Tailscale?"; then
    zsh ./scripts/tailscale_install.sh || {
        echo "Failed to install Tailscale."
        exit 1
    }
    gum style --foreground 2 "Tailscale installed successfully."
else
    echo "Skipping Tailscale installation."
fi

# Step 11: Check if .env file exists and is not empty
if [ -s ".env" ]; then
    gum style --foreground 2 "Found a non-empty .env file. Proceeding..."
else
    gum style --foreground 1 "Error: .env file is missing or empty."
    if ! gum confirm "Continue anyway?"; then
        echo "Setup aborted."
        exit 1
    fi
fi

# Step 12: Run docker-compose up -d
if gum confirm "Start Docker Compose services?"; then
    docker-compose up -d || {
        echo "Failed to start Docker Compose services."
        exit 1
    }
    gum style --foreground 2 "Docker Compose services started."
else
    echo "Skipping Docker Compose startup."
fi

gum style --foreground 2 "Homelab setup completed!"
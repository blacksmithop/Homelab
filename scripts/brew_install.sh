#!/bin/zsh

# Step 1: Install zsh if not present
if ! command -v zsh &> /dev/null; then
    echo "Installing zsh..."
    sudo apt-get update && sudo apt-get install -y zsh || {
        echo "Failed to install zsh."
        exit 1
    }
    echo "zsh installed successfully."
else
    echo "zsh is already installed."
fi

# Step 2: Ensure zsh is the current shell
if [ -z "$ZSH_VERSION" ]; then
    echo "Current shell is not zsh. Switching to zsh..."
    exec zsh -l || {
        echo "Failed to switch to zsh. Please run 'exec zsh' manually and retry."
        exit 1
    }
fi

# Step 3: Install Oh My Zsh if not present
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo "Installing Oh My Zsh..."
    # Download and run Oh My Zsh installer in a new zsh process
    zsh -c 'source <(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh) --unattended' || {
        echo "Failed to install Oh My Zsh."
        exit 1
    }
    echo "Oh My Zsh installed successfully."
else
    echo "Oh My Zsh is already installed."
fi

# Step 4: Install Homebrew if not present
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    zsh ./scripts/brew_install.sh || {
        echo "Failed to install Homebrew."
        exit 1
    }
    echo "Homebrew installed successfully."
else
    echo "Homebrew is already installed."
fi

# Step 5: Add Homebrew to PATH
BREW_SHELLENV='eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"'
BREW_COMMENT='# Add Homebrew to PATH'

if [ -f "$HOME/.zshrc" ]; then
    # Update .zshrc if it exists
    if ! grep -Fx "$BREW_SHELLENV" "$HOME/.zshrc" > /dev/null; then
        echo "$BREW_COMMENT" >> "$HOME/.zshrc"
        echo "$BREW_SHELLENV" >> "$HOME/.zshrc"
        echo "Added Homebrew to .zshrc"
    fi
else
    # Create .zshrc if it doesn't exist
    touch "$HOME/.zshrc"
    echo "$BREW_COMMENT" >> "$HOME/.zshrc"
    echo "$BREW_SHELLENV" >> "$HOME/.zshrc"
    echo "Created and updated .zshrc with Homebrew PATH"
fi

# Source .zshrc in zsh environment
source "$HOME/.zshrc" || {
    echo "Warning: Failed to source .zshrc. Continuing..."
}

# Apply Homebrew to current session
eval "$BREW_SHELLENV"

echo "Pre-installation setup completed!"
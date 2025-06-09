#!/bin/zsh

# Step 1: Introduction
gum style \
    --foreground 212 --border-foreground 212 --border double \
    --align center --width 50 --margin "1 2" --padding "2 4" \
    "Homelab Setup Script" "Let's get your environment ready!"

gum confirm "Ready to start the setup process?" || { echo "Setup aborted."; exit 1; }

# Step 2: Run Docker and Tailscale installation scripts
gum confirm "Install Docker?" && ./scripts/docker_install.sh || echo "Skipping Docker installation."
gum confirm "Install Tailscale?" && ./scripts/tailscale_install.sh || echo "Skipping Tailscale installation."

# Step 3: Check if .env file exists and is not empty
if [ -s ".env" ]; then
    gum style --foreground 2 "Found a non-empty .env file. Proceeding..."
else
    gum style --foreground 1 "Error: .env file is missing or empty."
    gum confirm "Continue anyway?" || { echo "Setup aborted."; exit 1; }
fi

# Step 4: Run docker-compose up -d
gum confirm "Start Docker Compose services?" && docker-compose up -d || echo "Skipping Docker Compose startup."
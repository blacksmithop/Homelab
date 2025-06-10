# Homelab

---

My setup for running services on my homelab.

* Most if not all services run as Docker containers
* I use Tailscale for SSH and RDP access
* Cloudflare Tunnels + NPM is used to expose services under subdomains
* All development is done locally and deployed using docker images

You can find the different docker compose files [here](./compose-files/)

## Environment Setup

To setup the environment run the following commands

```bash
bash preinstall.sh
```

![Pre-install script](./data/assets/preinstall.svg)

Followed by

```
zsh run.sh
```

![Run script](./data/assets/run.svg)

## Video Guide

Run a homelab server using Cloudflared Tunnel and Nginx Proxy Manager

[![Self-hosted guide](https://img.youtube.com/vi/Udc6HeOqxCY/0.jpg)](https://www.youtube.com/watch?v=Udc6HeOqxCY&ab_channel=AbhinavKM)

## TODO:

* Dedicated wiki page
* Integrate dotfiles and zshrc
* CI/CD
* Bash script to automate setup
* Rust server https://github.com/samrocketman/docker-compose-lgsm-rust-dedicated-server/blob/main/docker-compose.yml

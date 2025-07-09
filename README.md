# Homelab

![Stack](https://skillicons.dev/icons?i=ubuntu,bash,py,cloudflare,nginx,vscode)

---

## FAQ

### How do I run my services?

I run them as Docker containers using `docker-compose`

### How do I connect to my homelab?

I use Tailscale for SSH & RDP connectivity

### How do I expose my services to the internet?

Cloudflare Tunnels behind an nginx reverse-proxy is used to expose services through subdomains

---

Expose your homelab server using Cloudflared Tunnels and Nginx

[![Cloudflare Tunnel and NPM Guide](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/watch?v=Udc6HeOqxCY&ab_channel=AbhinavKM) [![Medium Article](https://img.shields.io/badge/Medium-12100E?style=for-the-badge&logo=medium&logoColor=white)](https://medium.com/@angstycoder101/forget-the-cloud-run-your-own-server-with-cloudflare-tunnels-cb73cb5f18ab)

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


## Update Services

```bash
bash update.sh
```

![Update script](./data/assets/update.svg)


## TODO:

* Dedicated wiki page
* Integrate dotfiles and zshrc
* CI/CD
* Bash script to automate setup
* Rust server https://github.com/samrocketman/docker-compose-lgsm-rust-dedicated-server/blob/main/docker-compose.yml

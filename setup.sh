#!/bin/bash
# =============================================================================
# Otto Voice — Full Setup
# Bare machine to running Otto Voice client in one script.
# Run as a user with sudo access (e.g. vagrant).
#
# Usage:
#   git clone git@github.com:ozobmar/otto-coms.git /opt/otto/otto-coms
#   cd /opt/otto/otto-coms
#   chmod +x setup.sh && ./setup.sh
#
# Idempotent — safe to re-run. Skips anything already installed.
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[OTTO-VOICE]${NC} $1"; }
warn() { echo -e "${YELLOW}[OTTO-VOICE]${NC} $1"; }
err()  { echo -e "${RED}[OTTO-VOICE]${NC} $1"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_USER=$(whoami)
LAN_SUBNET="192.168.86.0/24"

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║       Otto Voice — Full Setup        ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# =============================================================================
# 1. System Packages
# =============================================================================
log "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

log "Installing base packages..."
sudo apt-get install -y \
    ca-certificates \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    python3-venv \
    htop \
    net-tools \
    avahi-daemon \
    avahi-utils

# =============================================================================
# 2. Thin GUI Layer (Xorg + LightDM, auto-login, no desktop apps)
# =============================================================================
if command -v lightdm &> /dev/null; then
    log "LightDM already installed"
else
    log "Installing thin GUI layer (Xorg + LightDM)..."
    sudo apt-get install -y \
        xorg \
        lightdm \
        openbox \
        xterm
    log "Thin GUI installed (Xorg + LightDM + Openbox)"
fi

# Configure auto-login
LIGHTDM_CONF="/etc/lightdm/lightdm.conf.d/50-otto-autologin.conf"
if [ -f "$LIGHTDM_CONF" ]; then
    log "LightDM auto-login already configured"
else
    log "Configuring LightDM auto-login..."
    sudo mkdir -p /etc/lightdm/lightdm.conf.d
    sudo tee "$LIGHTDM_CONF" > /dev/null <<LIGHTDM_EOF
[Seat:*]
autologin-user=$CURRENT_USER
autologin-user-timeout=0
LIGHTDM_EOF
    log "Auto-login configured for $CURRENT_USER"
fi

# =============================================================================
# 3. PipeWire Audio Stack
# =============================================================================
if command -v pipewire &> /dev/null; then
    log "PipeWire already installed"
else
    log "Installing PipeWire audio stack..."
    sudo apt-get install -y \
        pipewire \
        pipewire-audio \
        pipewire-pulse \
        wireplumber \
        alsa-utils
    log "PipeWire audio stack installed"
fi

# =============================================================================
# 4. Otto Service User
# =============================================================================
if id "otto" &>/dev/null; then
    log "otto user already exists"
else
    log "Creating otto service user..."
    sudo useradd -m -s /bin/bash otto
    if [ -f "$HOME/.ssh/authorized_keys" ]; then
        sudo mkdir -p /home/otto/.ssh
        sudo cp "$HOME/.ssh/authorized_keys" /home/otto/.ssh/authorized_keys
        sudo chown -R otto:otto /home/otto/.ssh
        sudo chmod 700 /home/otto/.ssh
        sudo chmod 600 /home/otto/.ssh/authorized_keys
    fi
fi

# Add otto to audio group for hardware access
sudo usermod -aG audio otto 2>/dev/null || true

# =============================================================================
# 5. Git Config (for otto user)
# =============================================================================
log "Configuring git for otto user..."
sudo -u otto sh -c "cd ~ && git config --global user.name otto"
sudo -u otto sh -c "cd ~ && git config --global user.email otto@otto"
sudo -u otto sh -c "cd ~ && git config --global init.defaultBranch main"

# =============================================================================
# 6. Avahi/mDNS
# =============================================================================
log "Configuring Avahi mDNS..."
sudo systemctl enable avahi-daemon 2>/dev/null || true
sudo systemctl start avahi-daemon 2>/dev/null || true
log "Avahi enabled — can discover otto-core via _otto._tcp.local"

# =============================================================================
# 7. Firewall (LAN-only)
# =============================================================================
log "Configuring firewall (LAN-only: $LAN_SUBNET)..."
sudo ufw --force reset > /dev/null 2>&1

sudo ufw default deny incoming > /dev/null
sudo ufw default allow outgoing > /dev/null

# SSH from anywhere
sudo ufw allow ssh > /dev/null

# LAN-only services
sudo ufw allow from "$LAN_SUBNET" to any port 8765 proto tcp > /dev/null   # WebSocket
sudo ufw allow from "$LAN_SUBNET" to any port 8766 proto tcp > /dev/null   # Async callback
sudo ufw allow from "$LAN_SUBNET" to any port 5353 proto udp > /dev/null   # mDNS/Avahi

sudo ufw --force enable > /dev/null
log "Firewall enabled — all service ports restricted to $LAN_SUBNET"

# =============================================================================
# 8. Python App Setup
# =============================================================================
log "Setting up Otto Voice Python application..."
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    log "Creating Python virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[all]"

# =============================================================================
# 9. Audio Hardware Verification
# =============================================================================
echo ""
log "============================================"
log "Audio hardware check..."
log "============================================"

echo ""
log "ALSA playback devices:"
aplay -l 2>/dev/null || warn "No playback devices found"

echo ""
log "ALSA capture devices:"
arecord -l 2>/dev/null || warn "No capture devices found"

echo ""
if command -v pw-cli &> /dev/null; then
    log "PipeWire status:"
    pw-cli info 0 2>/dev/null | head -5 || warn "PipeWire not running (may need reboot)"
fi

# =============================================================================
# Verification
# =============================================================================
echo ""
log "============================================"
log "Verifying installation..."
log "============================================"

echo ""
log "Python:      $(python3 --version 2>/dev/null || echo 'FAILED')"
log "Git:         $(git --version 2>/dev/null || echo 'FAILED')"
log "PipeWire:    $(pipewire --version 2>/dev/null || echo 'FAILED')"
log "LightDM:     $(lightdm --version 2>/dev/null || echo 'not installed')"
log "Avahi:       $(systemctl is-active avahi-daemon 2>/dev/null || echo 'FAILED')"

echo ""
log "Firewall:"
sudo ufw status | grep -E "Status|8765|8766|5353|22"

echo ""
log "mDNS discovery test (looking for otto-core):"
avahi-browse -t _otto._tcp 2>/dev/null || warn "No otto-core found (may not be running yet)"

echo ""
log "============================================"
log "Otto Voice setup complete!"
log "============================================"
echo ""
log "To start Otto Voice:"
log "  cd $SCRIPT_DIR && ./run.sh --outputs console"
echo ""
log "To test with echo server:"
log "  cd $SCRIPT_DIR && ./tools/run_echo_server.sh &"
log "  ./run.sh --outputs otto-api --otto-url http://localhost:8080"
echo ""
warn "NOTE: If PipeWire shows issues, reboot first — audio services start at login."

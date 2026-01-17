#!/bin/bash
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Role: Setup continuous validation system
# Reference: docs/architecture/contracts/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     CONTINUOUS VALIDATION SETUP                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Install Python dependencies
echo "▶ Installing Python dependencies..."
pip3 install watchdog -q 2>/dev/null || pip install watchdog -q
echo "  ✓ watchdog installed"

# Step 2: Make scripts executable
echo ""
echo "▶ Setting permissions..."
chmod +x "$SCRIPT_DIR"/*.py
chmod +x "$SCRIPT_DIR"/*.sh
echo "  ✓ Scripts are executable"

# Step 3: Install systemd service
echo ""
echo "▶ Installing systemd service..."
if [ -d /etc/systemd/system ]; then
    sudo cp "$SCRIPT_DIR/validator.service" /etc/systemd/system/agenticverz-validator.service
    sudo systemctl daemon-reload
    echo "  ✓ Service installed: agenticverz-validator"
else
    echo "  ⚠ systemd not available, skipping service install"
fi

# Step 4: Create convenience aliases
echo ""
echo "▶ Creating command aliases..."

ALIAS_FILE="$REPO_ROOT/scripts/preflight/validator"
cat > "$ALIAS_FILE" << 'EOF'
#!/bin/bash
# Validator convenience command
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$1" in
    start)
        echo "Starting continuous validator..."
        python3 "$SCRIPT_DIR/continuous_validator.py" &
        ;;
    stop)
        python3 "$SCRIPT_DIR/continuous_validator.py" --stop
        ;;
    status)
        python3 "$SCRIPT_DIR/continuous_validator.py" --status
        ;;
    dashboard|dash|d)
        python3 "$SCRIPT_DIR/validator_dashboard.py"
        ;;
    watch|w)
        python3 "$SCRIPT_DIR/validator_dashboard.py" --watch
        ;;
    notify|n)
        python3 "$SCRIPT_DIR/validator_dashboard.py" --notify
        ;;
    check|c)
        bash "$SCRIPT_DIR/run_all_checks.sh"
        ;;
    log|logs)
        tail -f "$SCRIPT_DIR/../../.validator.log"
        ;;
    service)
        case "$2" in
            start)
                sudo systemctl start agenticverz-validator
                ;;
            stop)
                sudo systemctl stop agenticverz-validator
                ;;
            status)
                sudo systemctl status agenticverz-validator
                ;;
            enable)
                sudo systemctl enable agenticverz-validator
                echo "Validator will start on boot"
                ;;
            disable)
                sudo systemctl disable agenticverz-validator
                ;;
            *)
                echo "Usage: validator service {start|stop|status|enable|disable}"
                ;;
        esac
        ;;
    help|--help|-h|"")
        echo "Continuous Validator Commands"
        echo ""
        echo "  validator start       Start validator in background"
        echo "  validator stop        Stop validator"
        echo "  validator status      Show current status"
        echo "  validator dashboard   Interactive dashboard (alias: dash, d)"
        echo "  validator watch       Compact watch mode (alias: w)"
        echo "  validator notify      Desktop notification mode (alias: n)"
        echo "  validator check       Run full preflight checks (alias: c)"
        echo "  validator log         Tail the validator log"
        echo ""
        echo "  validator service start    Start systemd service"
        echo "  validator service stop     Stop systemd service"
        echo "  validator service status   Service status"
        echo "  validator service enable   Enable on boot"
        echo "  validator service disable  Disable on boot"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run 'validator help' for usage"
        exit 1
        ;;
esac
EOF

chmod +x "$ALIAS_FILE"
echo "  ✓ Created: $ALIAS_FILE"

# Step 5: Add to PATH suggestion
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Setup complete!"
echo ""
echo "Quick start:"
echo "  $SCRIPT_DIR/validator start      # Start in background"
echo "  $SCRIPT_DIR/validator dashboard  # Interactive dashboard"
echo "  $SCRIPT_DIR/validator status     # Check status"
echo ""
echo "For system-wide 'validator' command, add to your shell config:"
echo ""
echo "  echo 'export PATH=\"$SCRIPT_DIR:\$PATH\"' >> ~/.bashrc"
echo "  source ~/.bashrc"
echo ""
echo "Or create a symlink:"
echo ""
echo "  sudo ln -sf $ALIAS_FILE /usr/local/bin/validator"
echo ""
echo "To start on boot:"
echo ""
echo "  sudo systemctl enable agenticverz-validator"
echo ""

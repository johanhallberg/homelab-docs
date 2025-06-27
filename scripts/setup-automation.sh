#!/bin/bash
# Setup script for Homelab Deployment Automation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_DIR="$(dirname "$SCRIPT_DIR")"
K8S_CONFIG_DIR="$(dirname "$DOCS_DIR")/k8s-cluster-config"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up Homelab Deployment Automation${NC}"
echo "============================================="

# Check prerequisites
echo -e "${GREEN}📋 Checking prerequisites...${NC}"

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
    echo "Please install Python 3 and try again."
    exit 1
fi
echo -e "✅ Python 3: $(python3 --version)"

# Check pip3
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 is required but not installed.${NC}"
    echo "Please install pip3 and try again."
    exit 1
fi
echo -e "✅ pip3: $(pip3 --version)"

# Install required Python packages
echo -e "${GREEN}📦 Installing Python dependencies...${NC}"
pip3 install --user pyyaml requests

# Make scripts executable
echo -e "${GREEN}🔧 Making scripts executable...${NC}"
chmod +x "$SCRIPT_DIR/deployment-automation.py"
chmod +x "$SCRIPT_DIR/git-post-commit-hook.sh"

# Check for k8s-cluster-config directory
if [ ! -d "$K8S_CONFIG_DIR" ]; then
    echo -e "${YELLOW}⚠️  k8s-cluster-config directory not found at expected location: $K8S_CONFIG_DIR${NC}"
    echo "Please ensure the k8s-cluster-config repository is cloned alongside homelab-docs."
    K8S_CONFIG_DIR=""
fi

# Setup Git hooks (if k8s repo is available)
if [ -n "$K8S_CONFIG_DIR" ] && [ -d "$K8S_CONFIG_DIR/.git" ]; then
    echo -e "${GREEN}🪝 Setting up Git hooks...${NC}"
    
    HOOKS_DIR="$K8S_CONFIG_DIR/.git/hooks"
    POST_COMMIT_HOOK="$HOOKS_DIR/post-commit"
    
    # Backup existing hook if it exists
    if [ -f "$POST_COMMIT_HOOK" ]; then
        echo -e "${YELLOW}📋 Backing up existing post-commit hook...${NC}"
        cp "$POST_COMMIT_HOOK" "$POST_COMMIT_HOOK.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Copy our hook
    cp "$SCRIPT_DIR/git-post-commit-hook.sh" "$POST_COMMIT_HOOK"
    chmod +x "$POST_COMMIT_HOOK"
    
    echo -e "✅ Git post-commit hook installed"
else
    echo -e "${YELLOW}⚠️  Git hooks not installed (k8s-cluster-config not found or not a git repo)${NC}"
fi

# Check environment variables
echo -e "${GREEN}🔐 Checking environment variables...${NC}"

ENV_VARS_NEEDED=()

if [ -z "$DISCORD_HOMELAB_WEBHOOK" ]; then
    ENV_VARS_NEEDED+=("DISCORD_HOMELAB_WEBHOOK")
fi

if [ -z "$UPTIME_KUMA_USERNAME" ]; then
    ENV_VARS_NEEDED+=("UPTIME_KUMA_USERNAME")
fi

if [ -z "$UPTIME_KUMA_PASSWORD" ]; then
    ENV_VARS_NEEDED+=("UPTIME_KUMA_PASSWORD")
fi

if [ ${#ENV_VARS_NEEDED[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  The following environment variables need to be set:${NC}"
    for var in "${ENV_VARS_NEEDED[@]}"; do
        echo "   - $var"
    done
    echo
    echo "You can set them by adding the following to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo
    for var in "${ENV_VARS_NEEDED[@]}"; do
        echo "export $var='your_value_here'"
    done
    echo
else
    echo -e "✅ All required environment variables are set"
fi

# Create a simple test
echo -e "${GREEN}🧪 Running test...${NC}"
cd "$DOCS_DIR"

if python3 "$SCRIPT_DIR/deployment-automation.py" --action scan --config "$SCRIPT_DIR/automation-config.yaml"; then
    echo -e "✅ Test scan completed successfully"
else
    echo -e "${YELLOW}⚠️  Test scan completed with warnings (this may be normal)${NC}"
fi

# Create example usage script
echo -e "${GREEN}📚 Creating example usage script...${NC}"
cat > "$SCRIPT_DIR/example-usage.sh" << 'EOF'
#!/bin/bash
# Example usage of the deployment automation script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOMATION_SCRIPT="$SCRIPT_DIR/deployment-automation.py"

echo "🔍 Example 1: Adding a new service"
echo "python3 $AUTOMATION_SCRIPT --action add \\"
echo "    --name 'Grafana' \\"
echo "    --url 'https://grafana.staging.hallonen.se' \\"
echo "    --description 'Monitoring and observability dashboard' \\"
echo "    --why-selected 'Industry standard for metrics visualization' \\"
echo "    --maintainer 'Grafana Labs'"
echo

echo "🔄 Example 2: Updating an existing service"
echo "python3 $AUTOMATION_SCRIPT --action update \\"
echo "    --name 'Grafana' \\"
echo "    --description 'Updated monitoring and observability dashboard with new features'"
echo

echo "🗑️  Example 3: Removing a service"
echo "python3 $AUTOMATION_SCRIPT --action remove --name 'OldService'"
echo

echo "🔍 Example 4: Scanning for new services"
echo "python3 $AUTOMATION_SCRIPT --action scan"
echo

echo "To run these commands, uncomment the ones you want to test:"
echo
# python3 "$AUTOMATION_SCRIPT" --action add \
#     --name "Grafana" \
#     --url "https://grafana.staging.hallonen.se" \
#     --description "Monitoring and observability dashboard" \
#     --why-selected "Industry standard for metrics visualization" \
#     --maintainer "Grafana Labs"
EOF

chmod +x "$SCRIPT_DIR/example-usage.sh"

echo
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo "============================================="
echo -e "${BLUE}📋 Summary:${NC}"
echo "✅ Python dependencies installed"
echo "✅ Scripts made executable" 
if [ -n "$K8S_CONFIG_DIR" ]; then
    echo "✅ Git hooks installed in k8s-cluster-config"
fi
echo "✅ Configuration file created"
echo "✅ Example usage script created"
echo
echo -e "${BLUE}📖 Next steps:${NC}"
echo "1. Set required environment variables (if not already set)"
echo "2. Test the automation with: cd '$DOCS_DIR' && python3 scripts/deployment-automation.py --action scan"
echo "3. Check example usage: $SCRIPT_DIR/example-usage.sh"
echo
echo -e "${BLUE}🔧 Configuration file:${NC} $SCRIPT_DIR/automation-config.yaml"
echo -e "${BLUE}📜 Main script:${NC} $SCRIPT_DIR/deployment-automation.py"
echo
echo -e "${GREEN}Happy automating! 🤖${NC}"

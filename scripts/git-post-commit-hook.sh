#!/bin/bash
# Git post-commit hook for automatic deployment detection
# This script should be placed in .git/hooks/post-commit in your k8s-cluster-config repo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
DOCS_DIR="$(dirname "$PROJECT_ROOT")/homelab-docs"
AUTOMATION_SCRIPT="$DOCS_DIR/scripts/deployment-automation.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔍 Checking for new or modified deployments...${NC}"

# Check if the commit contains changes to deployment files
CHANGED_FILES=$(git diff-tree --no-commit-id --name-only -r HEAD)

# Look for ingress routes, deployments, or service files
DEPLOYMENT_CHANGES=$(echo "$CHANGED_FILES" | grep -E "(ingressroute|deployment|service)\.ya?ml$" || true)

if [ -z "$DEPLOYMENT_CHANGES" ]; then
    echo -e "${YELLOW}No deployment changes detected in this commit.${NC}"
    exit 0
fi

echo -e "${GREEN}📦 Deployment changes detected:${NC}"
echo "$DEPLOYMENT_CHANGES"

# Check if automation script exists
if [ ! -f "$AUTOMATION_SCRIPT" ]; then
    echo -e "${YELLOW}⚠️  Automation script not found at $AUTOMATION_SCRIPT${NC}"
    echo -e "${YELLOW}   Please ensure homelab-docs repository is set up correctly.${NC}"
    exit 0
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
    exit 1
fi

# Check if required Python packages are available
python3 -c "import yaml, requests" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Required Python packages (pyyaml, requests) not found.${NC}"
    echo -e "${YELLOW}   Install with: pip3 install pyyaml requests${NC}"
    exit 0
}

# Run the automation script in scan mode
echo -e "${GREEN}🤖 Running deployment automation...${NC}"
cd "$DOCS_DIR"

if python3 "$AUTOMATION_SCRIPT" --action scan; then
    echo -e "${GREEN}✅ Deployment automation completed successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Deployment automation completed with warnings.${NC}"
fi

# Check if there are any changes to commit in docs repo
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${GREEN}📝 Documentation updates detected and committed.${NC}"
else
    echo -e "${YELLOW}📝 No documentation updates required.${NC}"
fi

echo -e "${GREEN}🎉 Post-commit automation complete!${NC}"

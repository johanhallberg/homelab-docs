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

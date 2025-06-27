#!/usr/bin/env python3
"""
Homelab Deployment Automation Script

This script automates:
1. Documentation updates in the service catalog
2. Discord notifications to #homelab-general
3. Uptime Kuma monitor creation for external services

Usage:
    python3 deployment-automation.py --action add --name "MyApp" --url "https://myapp.hallonen.se" --description "My awesome application"
    python3 deployment-automation.py --action update --name "MyApp" --description "Updated description"
    python3 deployment-automation.py --action remove --name "MyApp"
"""

import argparse
import json
import os
import re
import requests
import subprocess
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import urllib.parse

class DeploymentAutomator:
    def __init__(self, config_path: str = None):
        self.base_dir = Path(__file__).parent.parent
        self.k8s_config_dir = self.base_dir.parent / "k8s-cluster-config"
        self.docs_dir = self.base_dir / "docs"
        self.service_catalog_path = self.docs_dir / "applications" / "services.md"
        
        # Load configuration
        config_file = config_path or self.base_dir / "scripts" / "automation-config.yaml"
        self.config = self.load_config(config_file)
        
    def load_config(self, config_path: Path) -> Dict:
        """Load automation configuration"""
        default_config = {
            "discord": {
                "webhook_url": os.getenv("DISCORD_HOMELAB_WEBHOOK"),
                "channel": "#homelab-general"
            },
            "uptime_kuma": {
                "url": "https://uptime.staging.hallonen.se",
                "username": os.getenv("UPTIME_KUMA_USERNAME"),
                "password": os.getenv("UPTIME_KUMA_PASSWORD")
            },
            "documentation": {
                "auto_commit": True,
                "commit_message_template": "docs: Update service catalog for {service_name}"
            }
        }
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge with defaults
                default_config.update(user_config)
        
        return default_config

    def detect_service_changes(self) -> List[Dict]:
        """Detect new or changed services in k8s-cluster-config"""
        changes = []
        
        # Check for new ingress routes or services with external URLs
        for ingress_file in self.k8s_config_dir.glob("**/ingressroute.yaml"):
            try:
                with open(ingress_file, 'r') as f:
                    ingress_data = yaml.safe_load_all(f)
                    for doc in ingress_data:
                        if doc and doc.get('kind') == 'IngressRoute':
                            service_info = self.extract_service_info(doc, ingress_file)
                            if service_info:
                                changes.append(service_info)
            except Exception as e:
                print(f"Error processing {ingress_file}: {e}")
        
        return changes

    def extract_service_info(self, ingress_doc: Dict, file_path: Path) -> Optional[Dict]:
        """Extract service information from ingress route"""
        try:
            name = ingress_doc.get('metadata', {}).get('name', '')
            namespace = ingress_doc.get('metadata', {}).get('namespace', '')
            
            # Extract URL from rules
            url = None
            spec = ingress_doc.get('spec', {})
            routes = spec.get('routes', [])
            
            if routes and len(routes) > 0:
                match = routes[0].get('match', '')
                if 'Host(' in match:
                    # Extract host from match rule like "Host(`app.staging.hallonen.se`)"
                    host_match = re.search(r'Host\(`([^`]+)`\)', match)
                    if host_match:
                        url = f"https://{host_match.group(1)}"
            
            if not url:
                return None
                
            # Determine app directory for additional context
            app_dir = file_path.parent
            service_name = app_dir.name if app_dir.name != "staging" else app_dir.parent.name
            
            return {
                "name": service_name,
                "namespace": namespace,
                "url": url,
                "file_path": str(file_path),
                "ingress_name": name
            }
        except Exception as e:
            print(f"Error extracting service info: {e}")
            return None

    def update_service_catalog(self, service_name: str, service_info: Dict, action: str = "add"):
        """Update the service catalog documentation"""
        if not self.service_catalog_path.exists():
            print(f"Service catalog not found at {self.service_catalog_path}")
            return False
            
        with open(self.service_catalog_path, 'r') as f:
            content = f.read()
        
        if action == "add" or action == "update":
            # Check if service already exists
            service_pattern = f"### {service_name}"
            if service_pattern in content:
                if action == "add":
                    print(f"Service {service_name} already exists in catalog. Use --action update to modify.")
                    return False
                # Update existing service
                content = self.update_existing_service(content, service_name, service_info)
            else:
                # Add new service
                content = self.add_new_service(content, service_name, service_info)
                
        elif action == "remove":
            content = self.remove_service(content, service_name)
        
        # Write updated content
        with open(self.service_catalog_path, 'w') as f:
            f.write(content)
            
        return True

    def add_new_service(self, content: str, service_name: str, service_info: Dict) -> str:
        """Add a new service to the catalog"""
        new_service = f"""
### {service_name}
- **Use Case**: {service_info.get('description', 'Service description not provided')}
- **Why Selected**: {service_info.get('why_selected', 'Selection reason not provided')}
- **Maintainer**: {service_info.get('maintainer', 'Maintainer not specified')}
- **Links**: [Service URL]({service_info.get('url', '#')})
"""
        
        # Insert before the final "---" line
        if content.endswith("---\n"):
            content = content[:-4] + new_service + "\n---\n"
        else:
            content += new_service + "\n"
            
        return content

    def update_existing_service(self, content: str, service_name: str, service_info: Dict) -> str:
        """Update an existing service in the catalog"""
        # Find the service section
        service_pattern = f"### {service_name}"
        start_idx = content.find(service_pattern)
        
        if start_idx == -1:
            return content
            
        # Find the end of this service section (next ### or end of file)
        next_service_idx = content.find("### ", start_idx + len(service_pattern))
        if next_service_idx == -1:
            # This is the last service, find the "---" marker
            end_idx = content.find("---", start_idx)
            if end_idx == -1:
                end_idx = len(content)
        else:
            end_idx = next_service_idx
            
        # Replace the service section
        old_section = content[start_idx:end_idx]
        new_section = f"""### {service_name}
- **Use Case**: {service_info.get('description', 'Service description not provided')}
- **Why Selected**: {service_info.get('why_selected', 'Selection reason not provided')}
- **Maintainer**: {service_info.get('maintainer', 'Maintainer not specified')}
- **Links**: [Service URL]({service_info.get('url', '#')})

"""
        
        return content.replace(old_section, new_section)

    def remove_service(self, content: str, service_name: str) -> str:
        """Remove a service from the catalog"""
        service_pattern = f"### {service_name}"
        start_idx = content.find(service_pattern)
        
        if start_idx == -1:
            print(f"Service {service_name} not found in catalog")
            return content
            
        # Find the end of this service section
        next_service_idx = content.find("### ", start_idx + len(service_pattern))
        if next_service_idx == -1:
            # This is the last service, find the "---" marker
            end_idx = content.find("---", start_idx)
            if end_idx == -1:
                end_idx = len(content)
        else:
            end_idx = next_service_idx
            
        # Remove the service section
        return content[:start_idx] + content[end_idx:]

    def send_discord_notification(self, message: str, webhook_url: str = None):
        """Send notification to Discord"""
        webhook_url = webhook_url or self.config["discord"]["webhook_url"]
        
        if not webhook_url:
            print("Discord webhook URL not configured")
            return False
            
        payload = {
            "content": message,
            "username": "Homelab Bot",
            "avatar_url": "https://cdn.discordapp.com/attachments/123456789/bot-avatar.png"
        }
        
        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            print("Discord notification sent successfully")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to send Discord notification: {e}")
            return False

    def create_uptime_monitor(self, service_name: str, url: str, uptime_kuma_config: Dict = None):
        """Create an Uptime Kuma monitor for the service"""
        config = uptime_kuma_config or self.config["uptime_kuma"]
        
        if not all([config.get("url"), config.get("username"), config.get("password")]):
            print("Uptime Kuma configuration incomplete")
            return False
            
        # Note: This is a simplified implementation
        # In practice, you'd need to use the Uptime Kuma API
        print(f"Creating Uptime Kuma monitor for {service_name} at {url}")
        
        # For now, we'll create a reminder message
        monitor_config = {
            "name": service_name,
            "url": url,
            "type": "http",
            "interval": 60,
            "retryInterval": 60,
            "maxRetries": 3
        }
        
        print(f"Monitor configuration: {json.dumps(monitor_config, indent=2)}")
        
        # TODO: Implement actual Uptime Kuma API integration
        # This would require authentication and API calls to create the monitor
        
        return True

    def commit_and_push_docs(self, service_name: str):
        """Commit and push documentation changes"""
        if not self.config["documentation"]["auto_commit"]:
            print("Auto-commit disabled")
            return False
            
        try:
            # Change to docs directory
            os.chdir(self.base_dir)
            
            # Add changes
            subprocess.run(["git", "add", "."], check=True)
            
            # Check if there are changes to commit
            result = subprocess.run(["git", "diff", "--cached", "--exit-code"], 
                                  capture_output=True)
            if result.returncode == 0:
                print("No changes to commit")
                return True
                
            # Commit changes
            commit_message = self.config["documentation"]["commit_message_template"].format(
                service_name=service_name
            )
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            
            # Push changes
            subprocess.run(["git", "push"], check=True)
            
            print("Documentation changes committed and pushed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
            return False

    def process_service(self, action: str, service_name: str, **kwargs):
        """Process a service action (add/update/remove)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if action in ["add", "update"]:
            service_info = {
                "url": kwargs.get("url", ""),
                "description": kwargs.get("description", ""),
                "why_selected": kwargs.get("why_selected", ""),
                "maintainer": kwargs.get("maintainer", "")
            }
            
            # Update documentation
            if self.update_service_catalog(service_name, service_info, action):
                print(f"Service catalog updated for {service_name}")
                
                # Commit changes
                self.commit_and_push_docs(service_name)
                
                # Send Discord notification
                if action == "add":
                    message = f"""🚀 **New Service Deployed!**

**Service**: {service_name}
**URL**: {service_info['url']}
**Description**: {service_info['description']}
**Timestamp**: {timestamp}

Service catalog has been updated automatically! 📖"""
                else:
                    message = f"""🔄 **Service Updated!**

**Service**: {service_name}
**Description**: {service_info['description']}
**Timestamp**: {timestamp}

Documentation has been updated! 📖"""
                
                self.send_discord_notification(message)
                
                # Create Uptime Kuma monitor for external services
                if service_info['url'] and service_info['url'].startswith('http'):
                    self.create_uptime_monitor(service_name, service_info['url'])
                    
        elif action == "remove":
            if self.update_service_catalog(service_name, {}, action):
                print(f"Service {service_name} removed from catalog")
                
                # Commit changes
                self.commit_and_push_docs(service_name)
                
                # Send Discord notification
                message = f"""🗑️ **Service Removed**

**Service**: {service_name}
**Timestamp**: {timestamp}

Service has been removed from the catalog."""
                
                self.send_discord_notification(message)

def main():
    parser = argparse.ArgumentParser(description="Homelab Deployment Automation")
    parser.add_argument("--action", choices=["add", "update", "remove", "scan"], required=True,
                       help="Action to perform")
    parser.add_argument("--name", help="Service name")
    parser.add_argument("--url", help="Service URL")
    parser.add_argument("--description", help="Service description")
    parser.add_argument("--why-selected", help="Why this service was selected")
    parser.add_argument("--maintainer", help="Service maintainer")
    parser.add_argument("--config", help="Path to configuration file")
    
    args = parser.parse_args()
    
    automator = DeploymentAutomator(args.config)
    
    if args.action == "scan":
        # Scan for new services and process them
        changes = automator.detect_service_changes()
        for change in changes:
            print(f"Detected service: {change}")
            # Auto-process detected services
            automator.process_service(
                "add",
                change["name"],
                url=change.get("url", ""),
                description=f"Kubernetes service in {change['namespace']} namespace"
            )
    else:
        if not args.name:
            print("--name is required for add/update/remove actions")
            sys.exit(1)
            
        automator.process_service(
            args.action,
            args.name,
            url=args.url,
            description=args.description,
            why_selected=getattr(args, 'why_selected'),
            maintainer=args.maintainer
        )

if __name__ == "__main__":
    main()

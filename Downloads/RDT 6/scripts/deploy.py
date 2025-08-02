#!/usr/bin/env python3
"""
Deployment script for Digital Twin to Azure Container Apps.
"""
import os
import subprocess
import sys
from typing import Dict, Any

def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    print(f"🔄 Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(f"✅ Output: {result.stdout}")
    if result.stderr:
        print(f"⚠️  Errors: {result.stderr}")
    
    if check and result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(1)
    
    return result

def build_docker_image(tag: str = "latest") -> str:
    """Build Docker image."""
    print("🐳 Building Docker image...")
    
    image_name = f"digital-twin:{tag}"
    run_command(f"docker build -t {image_name} .")
    
    return image_name

def push_to_registry(image_name: str, registry: str) -> str:
    """Push image to container registry."""
    print(f"📤 Pushing to registry: {registry}")
    
    # Tag for registry
    registry_image = f"{registry}/digital-twin:latest"
    run_command(f"docker tag {image_name} {registry_image}")
    run_command(f"docker push {registry_image}")
    
    return registry_image

def deploy_to_aca(environment: str = "prod") -> None:
    """Deploy to Azure Container Apps."""
    print(f"🚀 Deploying to Azure Container Apps ({environment})...")
    
    # Check if Azure CLI is installed
    try:
        run_command("az --version", check=False)
    except FileNotFoundError:
        print("❌ Azure CLI not found. Please install it first.")
        sys.exit(1)
    
    # Check if logged in
    result = run_command("az account show", check=False)
    if result.returncode != 0:
        print("❌ Not logged into Azure. Please run 'az login' first.")
        sys.exit(1)
    
    # Deploy using Bicep
    resource_group = os.getenv("AZURE_RESOURCE_GROUP", "digital-twin-rg")
    location = os.getenv("AZURE_LOCATION", "eastus")
    
    # Create resource group if it doesn't exist
    run_command(f"az group create --name {resource_group} --location {location}", check=False)
    
    # Deploy with Bicep
    bicep_file = "infra/aca.bicep"
    deployment_name = f"digital-twin-deploy-{environment}"
    
    # Get required parameters
    openai_key = os.getenv("OPENAI_API_KEY")
    search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    search_key = os.getenv("AZURE_SEARCH_KEY")
    app_insights = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    if not all([openai_key, search_endpoint, search_key]):
        print("❌ Missing required environment variables:")
        print("   - OPENAI_API_KEY")
        print("   - AZURE_SEARCH_ENDPOINT")
        print("   - AZURE_SEARCH_KEY")
        sys.exit(1)
    
    # Deploy
    deploy_command = f"""
    az deployment group create \
        --resource-group {resource_group} \
        --template-file {bicep_file} \
        --name {deployment_name} \
        --parameters \
            environment={environment} \
            openaiApiKey="{openai_key}" \
            searchEndpoint="{search_endpoint}" \
            searchKey="{search_key}" \
            appInsightsConnectionString="{app_insights or ''}"
    """
    
    run_command(deploy_command)
    
    print("✅ Deployment completed successfully!")

def get_deployment_url() -> str:
    """Get the deployment URL."""
    resource_group = os.getenv("AZURE_RESOURCE_GROUP", "digital-twin-rg")
    environment = os.getenv("ENVIRONMENT", "prod")
    app_name = f"digital-twin-{environment}"
    
    result = run_command(f"az containerapp show --name {app_name} --resource-group {resource_group} --query properties.configuration.ingress.fqdn --output tsv")
    
    if result.stdout.strip():
        return f"https://{result.stdout.strip()}"
    else:
        return "URL not available"

def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy Digital Twin to Azure")
    parser.add_argument("--environment", default="prod", choices=["dev", "staging", "prod"], help="Deployment environment")
    parser.add_argument("--skip-build", action="store_true", help="Skip Docker build")
    parser.add_argument("--registry", help="Container registry URL")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting deployment to {args.environment}...")
    
    try:
        # Build Docker image
        if not args.skip_build:
            image_name = build_docker_image()
            
            # Push to registry if specified
            if args.registry:
                push_to_registry(image_name, args.registry)
        
        # Deploy to Azure
        deploy_to_aca(args.environment)
        
        # Get deployment URL
        url = get_deployment_url()
        print(f"\n🎉 Deployment successful!")
        print(f"📱 Application URL: {url}")
        print(f"📊 Monitor at: https://portal.azure.com")
        
        return 0
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 
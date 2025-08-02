#!/usr/bin/env python3
"""
Setup script for the Digital Twin System.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def create_directory(path: str) -> None:
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)
    print(f"📁 Created directory: {path}")


def create_env_file() -> None:
    """Create .env file from template."""
    env_template = """# Digital Twin System Configuration

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEFAULT_LLM_PROVIDER=openai
MAX_TOKENS=4000
TEMPERATURE=0.7

# Vector Database
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Database Configuration
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://user:password@localhost/dbname

# Search Configuration
SEMANTIC_SEARCH_MODEL=all-MiniLM-L6-v2
MAX_SEARCH_RESULTS=10
SIMILARITY_THRESHOLD=0.7

# Memory Configuration
SHORT_TERM_MEMORY_TTL=3600
LONG_TERM_MEMORY_TTL=2592000

# Logging
LOG_LEVEL=INFO

# Truth Policy
STRICT_TRUTH_ENFORCEMENT=true
REQUIRE_SOURCE_ATTRIBUTION=true

# Response Configuration
MAX_RESPONSE_LENGTH=2000
INCLUDE_FOLLOW_UP_QUESTIONS=true
RESPONSE_SECTIONS=["summary", "insights", "actions", "suggestions"]

# Meeting Scheduling
RAMKI_OFFICE_HOURS={"monday": "2:00 PM - 4:00 PM", "wednesday": "10:00 AM - 12:00 PM", "friday": "3:00 PM - 5:00 PM"}

# Jira Integration
JIRA_URL=your_jira_url_here
JIRA_USERNAME=your_jira_username_here
JIRA_API_TOKEN=your_jira_api_token_here

# Microsoft Graph Integration
GRAPH_CLIENT_ID=your_graph_client_id_here
GRAPH_CLIENT_SECRET=your_graph_client_secret_here
GRAPH_TENANT_ID=your_graph_tenant_id_here
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_template)
        print("📄 Created .env file - please update with your actual API keys")
    else:
        print("📄 .env file already exists")


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python 3.9+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def install_dependencies() -> bool:
    """Install Python dependencies."""
    return run_command("pip install -r requirements.txt", "Installing Python dependencies")


def create_directories() -> None:
    """Create necessary directories."""
    directories = [
        "logs",
        "data",
        "chroma_db",
        "tests",
        "digital_twin/core",
        "digital_twin/handlers",
        "digital_twin/processors",
        "digital_twin/integrations",
        "digital_twin/utils",
        "digital_twin/api"
    ]
    
    for directory in directories:
        create_directory(directory)


def create_init_files() -> None:
    """Create __init__.py files for Python packages."""
    init_files = [
        "digital_twin/__init__.py",
        "digital_twin/core/__init__.py",
        "digital_twin/handlers/__init__.py",
        "digital_twin/processors/__init__.py",
        "digital_twin/integrations/__init__.py",
        "digital_twin/utils/__init__.py",
        "digital_twin/api/__init__.py",
        "tests/__init__.py"
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            Path(init_file).touch()
            print(f"📄 Created {init_file}")


def run_tests() -> bool:
    """Run basic tests to verify installation."""
    return run_command("python -m pytest tests/ -v", "Running tests")


def main():
    """Main setup function."""
    print("🚀 Setting up Digital Twin System...")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    print("\n📁 Creating project structure...")
    create_directories()
    create_init_files()
    
    # Create environment file
    print("\n📄 Setting up configuration...")
    create_env_file()
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not install_dependencies():
        print("❌ Failed to install dependencies. Please check the error messages above.")
        sys.exit(1)
    
    # Run tests
    print("\n🧪 Running tests...")
    if not run_tests():
        print("⚠️  Some tests failed. This might be expected if you haven't configured API keys yet.")
    
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Update .env file with your actual API keys")
    print("2. Configure your database connections")
    print("3. Review TRUTH_POLICY.md and STANDARD_INSTRUCTIONS.md")
    print("4. Check TEST_CASES.md for usage examples")
    print("5. Start development with: python -m digital_twin.api.main")


if __name__ == "__main__":
    main() 
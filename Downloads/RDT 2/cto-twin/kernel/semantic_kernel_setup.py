"""
Semantic Kernel Setup for CTO Twin
This module provides utilities for setting up and configuring the Semantic Kernel.
"""
import os
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextEmbedding
# Updated import for SK 1.34.0
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchMemoryStore

class AzureAISearchMemory:
    """Memory implementation using Azure AI Search"""
    
    def __init__(self, index_name, collection_name=None):
        """
        Initialize Azure AI Search memory
        
        Args:
            index_name: The name of the Azure AI Search index
            collection_name: Optional collection name for partitioning
        """
        self.index_name = index_name
        self.collection_name = collection_name
        self.endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
        self.key = os.environ.get("AZURE_SEARCH_KEY")
        self.embedding_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self.embedding_key = os.environ.get("AZURE_OPENAI_API_KEY")
        self.embedding_deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
        
        # Initialize memory store
        self.memory_store = None
        if self.endpoint and self.key and self.embedding_endpoint and self.embedding_key:
            self.memory_store = AzureAISearchMemoryStore(
                vector_size=1536,
                search_endpoint=self.endpoint,
                admin_key=self.key,
                index_name=self.index_name
            )
        
        # Initialize embedding generator
        self.embedding_generator = None
        if self.embedding_endpoint and self.embedding_key:
            self.embedding_generator = AzureTextEmbedding(
                deployment_name=self.embedding_deployment,
                endpoint=self.embedding_endpoint,
                api_key=self.embedding_key
            )

def setup_kernel():
    """
    Set up and configure the Semantic Kernel with Azure OpenAI services
    
    Returns:
        Configured Semantic Kernel instance
    """
    # Initialize kernel
    kernel = sk.Kernel()
    
    # Set up Azure OpenAI chat service
    azure_openai_deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
    azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    
    if azure_openai_endpoint and azure_openai_api_key:
        chat_service = AzureChatCompletion(
            deployment_name=azure_openai_deployment_name,
            endpoint=azure_openai_endpoint,
            api_key=azure_openai_api_key
        )
        kernel.add_text_completion_service("gpt4o", chat_service)
    else:
        # For local development without credentials
        print("WARNING: Azure OpenAI credentials not found. Using local mock service.")
        kernel.add_text_completion_service("gpt4o", sk.ChatCompletion())
    
    # Import semantic skills from directory
    skills_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kernel", "skills")
    if os.path.exists(skills_directory):
        kernel.import_plugins_from_directory(skills_directory)
    
    # Import prompts from directory
    prompts_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kernel", "prompts")
    if os.path.exists(prompts_directory):
        kernel.import_plugins_from_directory(prompts_directory)
    
    # Set up memory
    memory = AzureAISearchMemory("cto-dt-index")
    if memory.memory_store and memory.embedding_generator:
        kernel.memory = memory
    
    return kernel

def register_native_skills(kernel):
    """
    Register native Python skills with the kernel
    
    Args:
        kernel: The Semantic Kernel instance
    """
    # Import native skills
    from kernel.skills.jira_skill import JiraSkill
    from kernel.skills.outlook_skill import OutlookSkill
    from kernel.skills.sharepoint_skill import SharePointSkill
    from kernel.skills.search_skill import SearchSkill
    
    # Initialize graph connector for skills
    from tools.graph_connector import GraphConnector
    graph_connector = GraphConnector()
    
    # Register skills
    kernel.add_plugin(JiraSkill(graph_connector), "jira")
    kernel.add_plugin(OutlookSkill(graph_connector), "outlook")
    kernel.add_plugin(SharePointSkill(graph_connector), "sharepoint")
    kernel.add_plugin(SearchSkill(), "search")
    
    return kernel

if __name__ == "__main__":
    # Example usage
    kernel = setup_kernel()
    kernel = register_native_skills(kernel)
    
    # Example: Use the vector_query function from kb_search skill
    result = kernel.plugins["kb_search"].vector_query("What are the latest project deadlines?", k=3)
    print(result)
    
    # Example: Create a Jira ticket
    result = kernel.plugins["jira"].create(
        title="Implement new feature",
        description="Add support for custom notifications",
        project="CTO-TWIN",
        type="Task",
        priority="Medium"
    )
    print(result)

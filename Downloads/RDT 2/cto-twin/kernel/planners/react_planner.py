"""
ReAct (Reasoning and Acting) planner for CTO Twin
Implements the Reasoning and Acting planning paradigm with Semantic Kernel 0.92
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
import semantic_kernel as sk
from semantic_kernel.planning import Plan
from semantic_kernel.planning.sequential_planner import SequentialPlanner
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

logger = logging.getLogger(__name__)

class ReActPlanner:
    """
    ReAct (Reasoning and Acting) planner implementation
    Uses a combination of reasoning and acting to solve complex tasks
    Integrates with Semantic Kernel 0.92
    """
    
    def __init__(self, max_iterations: int = 10):
        """
        Initialize the ReAct planner
        
        Args:
            max_iterations: Maximum number of planning iterations
        """
        self.max_iterations = max_iterations
        self.history = []
        self.kernel = None
        self.planner = None
        self._initialize_kernel()
    
    def _initialize_kernel(self):
        """Initialize the Semantic Kernel with Azure OpenAI"""
        try:
            # Create a new kernel
            self.kernel = sk.Kernel()
            
            # Get deployment configuration from environment variables
            deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
            endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
            api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
            
            # Add Azure OpenAI service to the kernel
            if endpoint and api_key:
                self.kernel.add_chat_service(
                    "azure_chat_completion",
                    AzureChatCompletion(
                        deployment_name=deployment,
                        endpoint=endpoint,
                        api_key=api_key
                    )
                )
                
                # Create a sequential planner
                self.planner = SequentialPlanner(self.kernel)
                logger.info("Semantic Kernel and planner initialized successfully")
            else:
                logger.warning("Azure OpenAI credentials not found, using mock implementation")
        except Exception as e:
            logger.error(f"Error initializing Semantic Kernel: {str(e)}")
            # Fall back to mock implementation for development
    
    def plan(self, task: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate a plan for the given task using ReAct paradigm
        
        Args:
            task: Task description
            context: Context information including available tools
            
        Returns:
            List of plan steps
        """
        plan_steps = []
        
        # If Semantic Kernel is properly initialized, use it
        if self.kernel and self.planner:
            try:
                # Create a plan using the sequential planner
                sk_plan = self.planner.create_plan(task)
                
                # Execute the plan step by step with reasoning
                for i, step in enumerate(sk_plan.steps):
                    if i >= self.max_iterations:
                        break
                    
                    # Execute the step
                    result = step.invoke(self.kernel)
                    
                    # Record the step with reasoning
                    plan_steps.append({
                        "step": i + 1,
                        "thought": f"Considering how to accomplish: {step.description}",
                        "action": step.skill_name + "." + step.name,
                        "action_input": str(step.parameters),
                        "observation": str(result)
                    })
            except Exception as e:
                logger.error(f"Error in planning: {str(e)}")
                # Fall back to mock implementation
        
        # If no plan steps were generated (or Semantic Kernel failed), use mock implementation
        if not plan_steps:
            logger.info("Using mock planning implementation")
            for i in range(min(3, self.max_iterations)):
                plan_steps.append({
                    "step": i + 1,
                    "thought": f"Thinking about how to accomplish {task}",
                    "action": f"Action {i + 1} for {task}",
                    "action_input": json.dumps({"context": str(context)[:100] + "..."}),
                    "observation": f"Result of action {i + 1}"
                })
        
        # Record the plan in history
        self.history.append({"task": task, "plan": plan_steps})
        return plan_steps
    
    def execute(self, plan: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Execute a plan
        
        Args:
            plan: Plan to execute
            
        Returns:
            Tuple of (success, result)
        """
        if not plan:
            return (False, "Empty plan")
        
        results = []
        success = True
        
        # In a real implementation, this would execute each step
        # using the appropriate tools and skills
        for step in plan:
            try:
                # Here we would actually execute the action
                # For now, just record that we processed the step
                results.append(f"Executed: {step.get('action', 'unknown')}")
            except Exception as e:
                success = False
                results.append(f"Error: {str(e)}")
                break
        
        return (success, "\n".join(results))
    
    def reflect(self, task: str, plan: List[Dict[str, Any]], result: Tuple[bool, str]) -> Dict[str, Any]:
        """
        Reflect on the execution of a plan
        
        Args:
            task: Original task
            plan: Executed plan
            result: Result of execution
            
        Returns:
            Reflection with insights and improvements
        """
        success, result_str = result
        
        # In a real implementation, this would use the LLM to reflect
        # on the plan execution and suggest improvements
        reflection = {
            "task": task,
            "success": success,
            "insights": [
                "This is a placeholder insight",
                "In a real implementation, this would use the LLM to generate insights"
            ],
            "improvements": [
                "This is a placeholder improvement suggestion",
                "In a real implementation, this would use the LLM to suggest improvements"
            ]
        }
        
        return reflection

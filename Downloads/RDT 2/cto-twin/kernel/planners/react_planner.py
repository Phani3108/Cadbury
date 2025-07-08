"""
ReAct (Reasoning and Acting) planner for CTO Twin
Implements the Reasoning and Acting planning paradigm with Semantic Kernel 0.92
"""
import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Callable
import semantic_kernel as sk
# Updated imports for Semantic Kernel 1.34.0
# StepwisePlanner is not available in SK 1.34.0, we'll implement our own planner
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments

logger = logging.getLogger(__name__)

class ReActPlanner:
    """
    ReAct (Reasoning and Acting) planner implementation
    Uses a combination of reasoning and acting to solve complex tasks
    Integrates with Semantic Kernel 0.92
    """
    
    def __init__(self, max_iterations: int = 10, max_tokens: int = 4000):
        """
        Initialize the ReAct planner
        
        Args:
            max_iterations: Maximum number of planning iterations
            max_tokens: Maximum tokens for LLM responses
        """
        self.max_iterations = max_iterations
        self.max_tokens = max_tokens
        self.history = []
        self.kernel = None
        self.registered_skills = {}
        self._initialize_kernel()
    
    def _initialize_kernel(self):
        """Initialize the Semantic Kernel with Azure OpenAI"""
        try:
            # Create a new kernel
            self.kernel = sk.Kernel()
            
            # Get deployment configuration from environment variables
            chat_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
            endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
            api_key = os.environ.get("AZURE_OPENAI_API_KEY", "")
            
            # Add Azure OpenAI services to the kernel
            if endpoint and api_key:
                # Add chat completion service for main reasoning
                chat_service = AzureChatCompletion(
                    deployment_name=chat_deployment,
                    endpoint=endpoint,
                    api_key=api_key,
                    api_version="2023-05-15"
                )
                self.kernel.add_service("azure_chat_completion", chat_service)
                
                # Register core skills
                self._register_core_skills()
                
                logger.info("Semantic Kernel and planners initialized successfully")
            else:
                logger.warning("Azure OpenAI credentials not found, using mock implementation")
        except Exception as e:
            logger.error(f"Error initializing Semantic Kernel: {str(e)}")
            # Fall back to mock implementation for development
    
    def _register_core_skills(self):
        """Register core skills with the kernel"""
        try:
            # Register the ReAct native skill
            react_skill = self.kernel.create_skill()
            
            # Add the reasoning function
            @sk_function(
                description="Reason about the current state and decide what to do next",
                name="reason"
            )
            def reason(context: sk.SKContext) -> str:
                # Extract the current state and task from context
                task = context.variables.get("task", "")
                observations = context.variables.get("observations", "")
                
                # Prompt for reasoning
                prompt = f"""
                Task: {task}
                
                Previous observations:
                {observations}
                
                Based on the above information, reason about the current state and decide what to do next.
                Think step by step and be specific about what action to take.
                """
                
                # Use the kernel to generate reasoning
                reasoning_function = self.kernel.create_function_from_prompt(
                    prompt,
                    max_tokens=self.max_tokens,
                    temperature=0.1,
                    top_p=0.5
                )
                arguments = KernelArguments(**context)
                reasoning_result = reasoning_function(arguments=arguments)
                
                return str(reasoning_result)
            
            # Add the action function
            @sk.kernel_function(
                description="Execute an action based on reasoning",
                name="act"
            )
            def act(arguments: KernelArguments) -> str:
                # Extract the action to take from arguments
                action = arguments.get("action", "")
                action_input = arguments.get("action_input", "")
                
                # Parse the action and input
                try:
                    # Format: skill_name.function_name
                    if "." in action:
                        skill_name, function_name = action.split(".", 1)
                        
                        # Check if the skill and function exist
                        if skill_name in self.registered_skills:
                            skill = self.registered_skills[skill_name]
                            if hasattr(skill, function_name):
                                # Execute the function
                                func = getattr(skill, function_name)
                                if callable(func):
                                    # Parse action input if it's JSON
                                    try:
                                        input_params = json.loads(action_input)
                                    except:
                                        input_params = {"input": action_input}
                                    
                                    # Call the function with parameters
                                    result = func(**input_params)
                                    return str(result)
                    
                    # If we get here, either the action format was invalid or the skill/function wasn't found
                    return f"Error: Could not execute action '{action}' with input '{action_input}'. Action not found or invalid format."
                except Exception as e:
                    return f"Error executing action: {str(e)}"
            
            # Add the observe function
            @sk_function(
                description="Observe the results of an action",
                name="observe"
            )
            def observe(context: sk.SKContext) -> str:
                # Extract the action result from context
                action_result = context.variables.get("action_result", "")
                
                # Process and return the observation
                return f"Observation: {action_result}"
            
            # Register the functions with the skill
            react_skill.add_function(reason)
            react_skill.add_function(act)
            react_skill.add_function(observe)
            
            # Register the skill with the kernel
            self.kernel.add_skill(react_skill, "react")
            self.registered_skills["react"] = react_skill
            
            logger.info("Core ReAct skills registered successfully")
        except Exception as e:
            logger.error(f"Error registering core skills: {str(e)}")
    
    def register_skill(self, skill_name: str, skill_instance: Any) -> bool:
        """
        Register an external skill with the planner
        
        Args:
            skill_name: Name of the skill
            skill_instance: Instance of the skill
            
        Returns:
            Success flag
        """
        try:
            if self.kernel:
                # Create a skill from the instance
                sk_skill = self.kernel.import_skill(skill_instance, skill_name)
                
                # Store in registered skills
                self.registered_skills[skill_name] = skill_instance
                
                logger.info(f"Skill '{skill_name}' registered successfully")
                return True
            else:
                logger.warning(f"Cannot register skill '{skill_name}', kernel not initialized")
                return False
        except Exception as e:
            logger.error(f"Error registering skill '{skill_name}': {str(e)}")
            return False
    
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
        if self.kernel and self.stepwise_planner:
            try:
                logger.info(f"Creating plan for task: {task}")
                
                # Create context variables
                variables = ContextVariables()
                variables["task"] = task
                
                # Add context information
                for key, value in context.items():
                    if isinstance(value, str):
                        variables[key] = value
                    else:
                        variables[key] = json.dumps(value)
                
                # Create a plan using the stepwise planner
                planner_config = {
                    "max_iterations": self.max_iterations,
                    "max_tokens": self.max_tokens
                }
                
                # Execute the plan
                result = self.stepwise_planner.execute(
                    goal=task,
                    variables=variables,
                    config=planner_config
                )
                
                # Extract the plan steps from the result
                execution_steps = result.execution_steps
                
                for i, step in enumerate(execution_steps):
                    # Record the step with reasoning
                    plan_steps.append({
                        "step": i + 1,
                        "thought": step.thinking if hasattr(step, "thinking") else f"Planning step {i+1}",
                        "action": step.skill_name + "." + step.name if hasattr(step, "skill_name") and hasattr(step, "name") else "unknown",
                        "action_input": str(step.parameters) if hasattr(step, "parameters") else "{}",
                        "observation": str(step.result) if hasattr(step, "result") else "No result"
                    })
                
                logger.info(f"Plan created with {len(plan_steps)} steps")
            except Exception as e:
                logger.error(f"Error in planning: {str(e)}")
                # Fall back to sequential planner
                try:
                    logger.info("Falling back to sequential planner")
                    sk_plan = self.sequential_planner.create_plan(task)
                    
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
                except Exception as inner_e:
                    logger.error(f"Error in sequential planning: {str(inner_e)}")
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
        
        # Execute each step in the plan
        for i, step in enumerate(plan):
            try:
                logger.info(f"Executing step {i+1}: {step.get('action', 'unknown')}")
                
                # Extract action details
                action = step.get('action', '')
                action_input = step.get('action_input', '{}')
                
                # Parse the action and input
                if '.' in action:
                    skill_name, function_name = action.split('.', 1)
                    
                    # Check if the skill is registered
                    if skill_name in self.registered_skills:
                        skill = self.registered_skills[skill_name]
                        
                        # Check if the function exists in the skill
                        if hasattr(skill, function_name):
                            func = getattr(skill, function_name)
                            
                            if callable(func):
                                # Parse action input
                                try:
                                    input_params = json.loads(action_input)
                                except:
                                    input_params = {"input": action_input}
                                
                                # Execute the function
                                start_time = time.time()
                                result = func(**input_params)
                                execution_time = time.time() - start_time
                                
                                # Record the result
                                results.append({
                                    "step": i + 1,
                                    "action": action,
                                    "result": str(result),
                                    "success": True,
                                    "execution_time": execution_time
                                })
                                
                                logger.info(f"Step {i+1} executed successfully in {execution_time:.2f}s")
                            else:
                                error_msg = f"Function '{function_name}' in skill '{skill_name}' is not callable"
                                results.append({
                                    "step": i + 1,
                                    "action": action,
                                    "result": error_msg,
                                    "success": False
                                })
                                logger.error(error_msg)
                                success = False
                        else:
                            error_msg = f"Function '{function_name}' not found in skill '{skill_name}'"
                            results.append({
                                "step": i + 1,
                                "action": action,
                                "result": error_msg,
                                "success": False
                            })
                            logger.error(error_msg)
                            success = False
                    else:
                        error_msg = f"Skill '{skill_name}' not registered"
                        results.append({
                            "step": i + 1,
                            "action": action,
                            "result": error_msg,
                            "success": False
                        })
                        logger.error(error_msg)
                        success = False
                else:
                    # Handle direct function calls or mock execution
                    mock_result = f"Executed: {action} with input {action_input}"
                    results.append({
                        "step": i + 1,
                        "action": action,
                        "result": mock_result,
                        "success": True
                    })
                    logger.info(f"Step {i+1} mock executed: {action}")
            except Exception as e:
                error_msg = f"Error executing step {i+1}: {str(e)}"
                results.append({
                    "step": i + 1,
                    "action": step.get('action', 'unknown'),
                    "result": error_msg,
                    "success": False
                })
                logger.error(error_msg)
                success = False
                # Continue execution despite errors
        
        # Compile the final result
        result_str = "\n".join([f"Step {r['step']}: {r['action']} -> {'✓' if r['success'] else '✗'} {r['result']}" for r in results])
        return (success, result_str)
    
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
        
        if self.kernel:
            try:
                # Create a prompt for reflection
                reflection_prompt = f"""
                Task: {task}
                
                Plan:
                {json.dumps(plan, indent=2)}
                
                Execution Result:
                {result_str}
                
                Success: {success}
                
                Please reflect on the execution of this plan and provide:
                1. Key insights about what worked well and what didn't
                2. Specific improvements that could be made to the plan
                3. Alternative approaches that could have been taken
                4. Lessons learned for future planning
                
                Format your response as JSON with the following structure:
                {{
                    "insights": ["insight 1", "insight 2", ...],
                    "improvements": ["improvement 1", "improvement 2", ...],
                    "alternatives": ["alternative 1", "alternative 2", ...],
                    "lessons_learned": ["lesson 1", "lesson 2", ...]
                }}
                """
                
                # Create a semantic function for reflection
                reflection_function = self.kernel.create_semantic_function(
                    reflection_prompt,
                    max_tokens=self.max_tokens,
                    temperature=0.2,
                    top_p=0.8
                )
                
                # Execute the reflection
                context = self.kernel.create_new_context()
                reflection_result = reflection_function(context)
                
                # Parse the reflection result
                try:
                    reflection_data = json.loads(str(reflection_result))
                    
                    # Add task and success to the reflection
                    reflection_data["task"] = task
                    reflection_data["success"] = success
                    
                    return reflection_data
                except json.JSONDecodeError:
                    logger.error("Failed to parse reflection result as JSON")
                    # Fall back to basic reflection
            except Exception as e:
                logger.error(f"Error in reflection: {str(e)}")
                # Fall back to basic reflection
        
        # Basic reflection if Semantic Kernel reflection fails
        return {
            "task": task,
            "success": success,
            "insights": [
                "Plan execution completed with status: " + ("success" if success else "failure"),
                "The plan had " + str(len(plan)) + " steps"
            ],
            "improvements": [
                "Consider breaking down complex tasks into smaller steps",
                "Add more error handling for robustness"
            ],
            "alternatives": [
                "A different approach could use more parallel processing",
                "Consider using different tools for some steps"
            ],
            "lessons_learned": [
                "Proper error handling is essential for plan execution",
                "Clear task definitions lead to better plans"
            ]
        }
    
    def execute_with_reasoning(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a task with reasoning (full ReAct loop)
        
        Args:
            task: Task to execute
            context: Optional context information
            
        Returns:
            Execution results including plan, execution, and reflection
        """
        if context is None:
            context = {}
        
        # 1. Plan
        logger.info(f"Planning for task: {task}")
        plan = self.plan(task, context)
        
        # 2. Execute
        logger.info("Executing plan")
        execution_result = self.execute(plan)
        
        # 3. Reflect
        logger.info("Reflecting on execution")
        reflection = self.reflect(task, plan, execution_result)
        
        # Return the complete result
        return {
            "task": task,
            "plan": plan,
            "execution": {
                "success": execution_result[0],
                "result": execution_result[1]
            },
            "reflection": reflection,
            "timestamp": time.time()
        }

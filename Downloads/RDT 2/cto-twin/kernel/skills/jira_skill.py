"""
Jira skill for CTO Twin
Provides functionality to interact with Jira via Microsoft Graph connectors
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class JiraSkill:
    """
    Skill for interacting with Jira via Microsoft Graph connectors
    Enables the CTO Twin to create, update, and query Jira issues
    """
    
    def __init__(self, graph_connector):
        """
        Initialize the Jira skill
        
        Args:
            graph_connector: Microsoft Graph connector instance
        """
        self.graph_connector = graph_connector
        logger.info("Jira skill initialized")
    
    def get_issues(self, project_key: str, max_results: int = 50, 
                  status: Optional[str] = None, assignee: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get issues from a Jira project
        
        Args:
            project_key: Jira project key
            max_results: Maximum number of results to return
            status: Filter by status (e.g., "In Progress", "Done")
            assignee: Filter by assignee
            
        Returns:
            List of issues
        """
        try:
            if self.graph_connector:
                # In a real implementation, this would use the Graph connector
                # to query Jira issues through Microsoft Graph
                logger.info(f"Getting issues for project {project_key}")
                
                # Build the query
                query = f"project = {project_key}"
                if status:
                    query += f" AND status = '{status}'"
                if assignee:
                    query += f" AND assignee = '{assignee}'"
                
                # This would be the actual call to the Graph connector
                # return self.graph_connector.query_jira(query, max_results)
            
            # Mock implementation for development
            return [
                {
                    "id": f"{project_key}-1",
                    "key": f"{project_key}-1",
                    "summary": "Implement feature X",
                    "description": "Detailed description of feature X",
                    "status": "In Progress",
                    "assignee": "John Doe",
                    "created": datetime.now().isoformat(),
                    "updated": datetime.now().isoformat(),
                    "priority": "High"
                },
                {
                    "id": f"{project_key}-2",
                    "key": f"{project_key}-2",
                    "summary": "Fix bug Y",
                    "description": "Detailed description of bug Y",
                    "status": "Done",
                    "assignee": "Jane Smith",
                    "created": datetime.now().isoformat(),
                    "updated": datetime.now().isoformat(),
                    "priority": "Medium"
                },
                {
                    "id": f"{project_key}-3",
                    "key": f"{project_key}-3",
                    "summary": "Research technology Z",
                    "description": "Detailed description of research task Z",
                    "status": "To Do",
                    "assignee": None,
                    "created": datetime.now().isoformat(),
                    "updated": datetime.now().isoformat(),
                    "priority": "Low"
                }
            ]
        except Exception as e:
            logger.error(f"Error getting Jira issues: {str(e)}")
            return []
    
    def create_issue(self, project_key: str, summary: str, description: str, 
                    issue_type: str = "Task", priority: Optional[str] = None, 
                    assignee: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new issue in Jira
        
        Args:
            project_key: Jira project key
            summary: Issue summary
            description: Issue description
            issue_type: Issue type (e.g., "Task", "Bug", "Story")
            priority: Issue priority (e.g., "High", "Medium", "Low")
            assignee: Issue assignee
            
        Returns:
            Created issue details
        """
        try:
            if self.graph_connector:
                # In a real implementation, this would use the Graph connector
                # to create a Jira issue through Microsoft Graph
                logger.info(f"Creating {issue_type} in project {project_key}: {summary}")
                
                # Prepare the issue data
                issue_data = {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": issue_type}
                }
                
                if priority:
                    issue_data["priority"] = {"name": priority}
                
                if assignee:
                    issue_data["assignee"] = {"name": assignee}
                
                # This would be the actual call to the Graph connector
                # return self.graph_connector.create_jira_issue(issue_data)
            
            # Mock implementation for development
            return {
                "id": f"{project_key}-123",
                "key": f"{project_key}-123",
                "summary": summary,
                "description": description,
                "status": "To Do",
                "assignee": assignee,
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "priority": priority or "Medium",
                "issue_type": issue_type,
                "url": f"https://your-jira-instance.atlassian.net/browse/{project_key}-123"
            }
        except Exception as e:
            logger.error(f"Error creating Jira issue: {str(e)}")
            return {"error": str(e)}
    
    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing Jira issue
        
        Args:
            issue_key: Jira issue key (e.g., "PROJ-123")
            fields: Fields to update
            
        Returns:
            Updated issue details
        """
        try:
            if self.graph_connector:
                # In a real implementation, this would use the Graph connector
                # to update a Jira issue through Microsoft Graph
                logger.info(f"Updating issue {issue_key}")
                
                # This would be the actual call to the Graph connector
                # return self.graph_connector.update_jira_issue(issue_key, fields)
            
            # Mock implementation for development
            project_key = issue_key.split("-")[0]
            return {
                "id": issue_key,
                "key": issue_key,
                "summary": fields.get("summary", "Updated issue"),
                "description": fields.get("description", "Updated description"),
                "status": fields.get("status", "In Progress"),
                "assignee": fields.get("assignee"),
                "updated": datetime.now().isoformat(),
                "priority": fields.get("priority", "Medium"),
                "url": f"https://your-jira-instance.atlassian.net/browse/{issue_key}"
            }
        except Exception as e:
            logger.error(f"Error updating Jira issue: {str(e)}")
            return {"error": str(e)}
    
    def get_issue_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get available transitions for a Jira issue
        
        Args:
            issue_key: Jira issue key (e.g., "PROJ-123")
            
        Returns:
            List of available transitions
        """
        try:
            if self.graph_connector:
                # In a real implementation, this would use the Graph connector
                # to get issue transitions through Microsoft Graph
                logger.info(f"Getting transitions for issue {issue_key}")
                
                # This would be the actual call to the Graph connector
                # return self.graph_connector.get_jira_issue_transitions(issue_key)
            
            # Mock implementation for development
            return [
                {"id": "11", "name": "To Do"},
                {"id": "21", "name": "In Progress"},
                {"id": "31", "name": "Done"}
            ]
        except Exception as e:
            logger.error(f"Error getting Jira issue transitions: {str(e)}")
            return []
    
    def transition_issue(self, issue_key: str, transition_id: str) -> Dict[str, Any]:
        """
        Transition a Jira issue to a new status
        
        Args:
            issue_key: Jira issue key (e.g., "PROJ-123")
            transition_id: ID of the transition to perform
            
        Returns:
            Updated issue details
        """
        try:
            if self.graph_connector:
                # In a real implementation, this would use the Graph connector
                # to transition a Jira issue through Microsoft Graph
                logger.info(f"Transitioning issue {issue_key} with transition {transition_id}")
                
                # This would be the actual call to the Graph connector
                # return self.graph_connector.transition_jira_issue(issue_key, transition_id)
            
            # Mock implementation for development
            status_map = {
                "11": "To Do",
                "21": "In Progress",
                "31": "Done"
            }
            
            return {
                "id": issue_key,
                "key": issue_key,
                "status": status_map.get(transition_id, "Unknown"),
                "updated": datetime.now().isoformat(),
                "url": f"https://your-jira-instance.atlassian.net/browse/{issue_key}"
            }
        except Exception as e:
            logger.error(f"Error transitioning Jira issue: {str(e)}")
            return {"error": str(e)}

"""
Mail integration for the Digital Twin system.
Currently a stub - to be implemented with Microsoft Graph API.
"""

async def send_email(to: str, subject: str, body: str) -> bool:
    """
    Send an email using Microsoft Graph API.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body
        
    Returns:
        True if email sent successfully, False otherwise
    """
    # TODO: Implement with Microsoft Graph API
    print(f"Mock email sent to {to}: {subject}")
    return True 
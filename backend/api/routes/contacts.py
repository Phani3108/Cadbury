"""
Contacts API — endpoints for viewing recruiter contacts and their trust scores.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/contacts", tags=["contacts"])


@router.get("")
async def list_contacts():
    """
    List all recruiter contacts with their trust scores.

    Queries the recruiter_contacts table via the memory graph.
    """
    from memory.graph import list_contacts
    return await list_contacts()


@router.get("/{contact_id}")
async def get_contact(contact_id: str):
    """
    Get a single recruiter contact by ID.

    Args:
        contact_id: The unique identifier of the contact.

    Raises:
        HTTPException 404: If the contact is not found.
    """
    from memory.graph import get_contact
    contact = await get_contact(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

from fastapi import APIRouter, HTTPException
from memory.graph import (
    list_approvals,
    get_approval,
    save_approval,
    update_approval_status,
    save_event,
    log_decision,
)
from memory.models import (
    ApprovalItem,
    ApprovalAction,
    ApprovalStatus,
    DelegateEvent,
    EventType,
    DecisionLog,
)
from runtime.event_bus import publish_event

router = APIRouter(prefix="/v1/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalItem])
async def list_approval_items(status: str | None = None):
    s = ApprovalStatus(status) if status else None
    return await list_approvals(s)


@router.get("/{approval_id}", response_model=ApprovalItem)
async def get_approval_item(approval_id: str):
    item = await get_approval(approval_id)
    if not item:
        raise HTTPException(404, "Approval not found")
    return item


@router.post("/{approval_id}/approve")
async def approve_item(approval_id: str, action: ApprovalAction = ApprovalAction()):
    item = await get_approval(approval_id)
    if not item:
        raise HTTPException(404, "Approval not found")
    if item.status != ApprovalStatus.PENDING:
        raise HTTPException(400, f"Approval is already {item.status}")

    # Update draft if edited
    if action.draft_content:
        item.draft_content = action.draft_content

    item.status = ApprovalStatus.APPROVED
    await save_approval(item)

    # Emit event
    event = DelegateEvent(
        delegate_id=item.delegate_id,
        event_type=EventType.HUMAN_APPROVED,
        summary=f"Human approved: {item.action_label}",
        payload={"approval_id": approval_id, "draft_content": item.draft_content},
        parent_event_id=item.event_id,
    )
    await save_event(event)
    await publish_event(event)

    # Log decision
    await log_decision(DecisionLog(
        delegate_id=item.delegate_id,
        event_id=event.event_id,
        action_taken=f"approved:{item.action}",
        reasoning="Human approved via inbox",
        human_approved=True,
        policy_check=item.policy_check,
    ))

    return {"status": "approved"}


@router.post("/{approval_id}/reject")
async def reject_item(approval_id: str, action: ApprovalAction = ApprovalAction()):
    item = await get_approval(approval_id)
    if not item:
        raise HTTPException(404, "Approval not found")
    if item.status != ApprovalStatus.PENDING:
        raise HTTPException(400, f"Approval is already {item.status}")

    item.status = ApprovalStatus.REJECTED
    await save_approval(item)

    event = DelegateEvent(
        delegate_id=item.delegate_id,
        event_type=EventType.HUMAN_REJECTED,
        summary=f"Human rejected: {item.action_label}",
        payload={"approval_id": approval_id, "reason": action.reason},
        parent_event_id=item.event_id,
    )
    await save_event(event)
    await publish_event(event)

    await log_decision(DecisionLog(
        delegate_id=item.delegate_id,
        event_id=event.event_id,
        action_taken=f"rejected:{item.action}",
        reasoning=action.reason or "Human rejected via inbox",
        human_approved=False,
        policy_check=item.policy_check,
    ))

    return {"status": "rejected"}


@router.post("/{approval_id}/edit")
async def edit_draft(approval_id: str, action: ApprovalAction):
    item = await get_approval(approval_id)
    if not item:
        raise HTTPException(404, "Approval not found")
    if action.draft_content:
        item.draft_content = action.draft_content
        await save_approval(item)
    return {"status": "updated"}

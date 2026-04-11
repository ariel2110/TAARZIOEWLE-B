from enum import Enum


class LeadStatus(str, Enum):
    imported = "imported"
    normalized = "normalized"
    duplicate_review = "duplicate_review"
    needs_review = "needs_review"
    qualified = "qualified"
    rejected = "rejected"
    converted_to_business = "converted_to_business"


class BusinessStatus(str, Enum):
    new = "new"
    reviewed = "reviewed"
    ready_for_draft = "ready_for_draft"
    draft_created = "draft_created"
    outreach_ready = "outreach_ready"
    contacted = "contacted"
    replied_positive = "replied_positive"
    replied_negative = "replied_negative"
    asked_human = "asked_human"
    payment_pending = "payment_pending"
    paid = "paid"
    active = "active"
    paused = "paused"
    expired = "expired"
    delete_requested = "delete_requested"
    deleted = "deleted"


class DraftSiteStatus(str, Enum):
    draft = "draft"
    preview_ready = "preview_ready"
    published_preview = "published_preview"
    pending_payment = "pending_payment"
    active = "active"
    suspended = "suspended"
    expired = "expired"
    delete_requested = "delete_requested"
    deleted = "deleted"

import enum

class OrderState(str, enum.Enum):
    """Unified lifecycle states for all types of orders."""
    PENDING = "pending"
    WAITING_FOR_MATERIALS = "waiting_for_materials"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

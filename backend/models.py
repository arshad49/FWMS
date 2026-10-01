from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from typing import List, Dict, Any
import uuid

# ==========================================
# CLIENT MODELS
# ==========================================
class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None

class ClientResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ==========================================
# PROJECT MODELS
# ==========================================
class ProjectCreate(BaseModel):
    client_id: uuid.UUID
    name: str
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    total_cost: float = 0.0
    status: str = "Pending"
    assigned_name: Optional[str] = None
    assigned_percentage: float = 0.0
    notes: Optional[str] = None

class ProjectUpdate(BaseModel):
    client_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    total_cost: Optional[float] = None
    status: Optional[str] = None
    assigned_name: Optional[str] = None
    assigned_percentage: Optional[float] = None
    notes: Optional[str] = None

class ProjectResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    name: str
    start_date: Optional[date]
    deadline: Optional[date]
    total_cost: float
    status: str
    assigned_name: Optional[str]
    assigned_percentage: float
    notes: Optional[str]
    created_at: datetime
    client_name: Optional[str] = None

    class Config:
        from_attributes = True

# ==========================================
# TASK MODELS
# ==========================================
# Find the TaskCreate class and update it:
class TaskCreate(BaseModel):
    project_id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: str = "To Do"
    deadline: Optional[date] = None
    # NEW FIELDS:
    assigned_to: Optional[str] = None  # Name of person doing the task
    task_cost: float = 0.0  # Cost/payment for this specific task
    notes: Optional[str] = None

# Find the TaskUpdate class and update it:
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[date] = None
    assigned_to: Optional[str] = None
    task_cost: Optional[float] = None
    notes: Optional[str] = None

# Find the TaskResponse class and update it:
class TaskResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: Optional[str]
    status: str
    deadline: Optional[date]
    created_at: datetime
    project_name: Optional[str] = None
    # NEW FIELDS:
    assigned_to: Optional[str] = None
    task_cost: float = 0.0
    notes: Optional[str] = None

    class Config:
        from_attributes = True  
# ==========================================
# QUOTE MODELS
# ==========================================
class QuoteCreate(BaseModel):
    client_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    quote_number: str
    status: str = "Draft"
    subtotal: float = 0.0
    tax_percentage: float = 0.0
    discount_percentage: float = 0.0
    total_amount: float = 0.0
    items: List[Dict[str, Any]]  # Now includes process and delivery_days
    requirements: Optional[str] = None  # NEW: Client requirements text
    terms: Optional[str] = None  # NEW: Additional terms text
    payment_schedule: Optional[str] = None  # NEW: Payment schedule text

# Find QuoteResponse and update it:
class QuoteResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    project_id: Optional[uuid.UUID]
    quote_number: str
    status: str
    subtotal: float
    tax_percentage: float
    discount_percentage: float
    total_amount: float
    items: List[Dict[str, Any]]  # Now includes process and delivery_days
    requirements: Optional[str] = None
    terms: Optional[str] = None
    payment_schedule: Optional[str] = None
    created_at: datetime
    client_name: Optional[str] = None
    project_name: Optional[str] = None

    class Config:
        from_attributes = True
    client_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    quote_number: str
    status: str = "Draft" # Draft, Sent, Accepted, Rejected
    subtotal: float = 0.0
    tax_percentage: float = 0.0
    discount_percentage: float = 0.0
    total_amount: float = 0.0
    items: List[Dict[str, Any]] # Stores JSON array of items


    id: uuid.UUID
    client_id: uuid.UUID
    project_id: Optional[uuid.UUID]
    quote_number: str
    status: str
    subtotal: float
    tax_percentage: float
    discount_percentage: float
    total_amount: float
    items: List[Dict[str, Any]]
    created_at: datetime
    client_name: Optional[str] = None
    project_name: Optional[str] = None

    class Config:
        from_attributes = True

# ==========================================
# INVOICE & PAYMENT MODELS
# ==========================================
class InvoiceCreate(BaseModel):
    client_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    invoice_number: str
    subtotal: float = 0.0
    tax_percentage: float = 0.0
    discount_percentage: float = 0.0
    total_amount: float = 0.0
    amount_paid: float = 0.0
    due_date: Optional[date] = None
    items: List[Dict[str, Any]]
    status: str = "Unpaid" # Unpaid, Partial, Paid, Overdue

class InvoiceResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    project_id: Optional[uuid.UUID]
    invoice_number: str
    subtotal: float
    tax_percentage: float
    discount_percentage: float
    total_amount: float
    amount_paid: float
    due_date: Optional[date]
    items: List[Dict[str, Any]]
    status: str
    created_at: datetime
    client_name: Optional[str] = None
    project_name: Optional[str] = None

    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    invoice_id: uuid.UUID
    amount: float
    payment_date: date
    payment_method: str # e.g., "UPI", "Bank Transfer", "Cash"
    notes: Optional[str] = None

class PaymentResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    amount: float
    payment_date: date
    payment_method: str
    notes: Optional[str]
    created_at: datetime
    invoice_number: Optional[str] = None

    class Config:
        from_attributes = True
class QuoteStatusUpdate(BaseModel):
    status: str
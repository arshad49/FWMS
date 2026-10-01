from fastapi import APIRouter, Depends
from database import get_db
from models import InvoiceCreate, InvoiceResponse
from typing import List, Dict, Any
import uuid
import json

router = APIRouter()

@router.get("/", response_model=list[InvoiceResponse])
def get_invoices(db = Depends(get_db)):
    cursor = db.cursor()
    query = """
        SELECT i.*, c.name as client_name, p.name as project_name 
        FROM invoices i 
        LEFT JOIN clients c ON i.client_id = c.id 
        LEFT JOIN projects p ON i.project_id = p.id 
        ORDER BY i.created_at DESC;
    """
    cursor.execute(query)
    invoices = cursor.fetchall()
    
    # FIX: Safely parse the JSONB items
    for inv in invoices:
        if inv['items'] is None:
            inv['items'] = []
        elif isinstance(inv['items'], str):
            # Only parse if it's still a string
            inv['items'] = json.loads(inv['items'])
        # If it's already a list (thanks to psycopg2 auto-parsing), do nothing!
            
    cursor.close()
    return invoices

@router.post("/", response_model=InvoiceResponse, status_code=201)
def create_invoice(invoice: InvoiceCreate, db = Depends(get_db)):
    cursor = db.cursor()
    query = """
        INSERT INTO invoices (client_id, project_id, invoice_number, subtotal, tax_percentage, discount_percentage, total_amount, amount_paid, due_date, items, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
    """
    cursor.execute(query, (
        str(invoice.client_id), str(invoice.project_id) if invoice.project_id else None,
        invoice.invoice_number, invoice.subtotal, invoice.tax_percentage, invoice.discount_percentage,
        invoice.total_amount, invoice.amount_paid, invoice.due_date, json.dumps(invoice.items), invoice.status
    ))
    new_inv = cursor.fetchone()
    db.commit()
    cursor.close()
    
    # Fetch names
    cursor = db.cursor()
    cursor.execute("SELECT name FROM clients WHERE id = %s;", (str(invoice.client_id),))
    client = cursor.fetchone()
    project_name = None
    if invoice.project_id:
        cursor.execute("SELECT name FROM projects WHERE id = %s;", (str(invoice.project_id),))
        proj = cursor.fetchone()
        project_name = proj['name'] if proj else None
    cursor.close()
    
    new_inv['client_name'] = client['name'] if client else None
    new_inv['project_name'] = project_name
    new_inv['items'] = invoice.items
    return new_inv
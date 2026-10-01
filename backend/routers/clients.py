from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import ClientCreate, ClientUpdate, ClientResponse
import uuid
import json
router = APIRouter()

# 1. GET all clients
@router.get("/", response_model=list[ClientResponse])
def get_clients(db = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM clients ORDER BY created_at DESC;")
    clients = cursor.fetchall()
    cursor.close()
    return clients

# 2. POST (Create) a new client
@router.post("/", response_model=ClientResponse, status_code=201)
def create_client(client: ClientCreate, db = Depends(get_db)):
    cursor = db.cursor()
    query = """
        INSERT INTO clients (name, email, phone, company, notes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *;
    """
    cursor.execute(query, (client.name, client.email, client.phone, client.company, client.notes))
    new_client = cursor.fetchone()
    db.commit() # Save to database!
    cursor.close()
    return new_client

# 3. PUT (Update) an existing client
@router.put("/{client_id}", response_model=ClientResponse)
def update_client(client_id: str, client: ClientUpdate, db = Depends(get_db)):
    cursor = db.cursor()
    
    # Build dynamic update query based on what fields are provided
    update_fields = []
    values = []
    if client.name is not None:
        update_fields.append("name = %s")
        values.append(client.name)
    if client.email is not None:
        update_fields.append("email = %s")
        values.append(client.email)
    if client.phone is not None:
        update_fields.append("phone = %s")
        values.append(client.phone)
    if client.company is not None:
        update_fields.append("company = %s")
        values.append(client.company)
    if client.notes is not None:
        update_fields.append("notes = %s")
        values.append(client.notes)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(client_id)
    query = f"UPDATE clients SET {', '.join(update_fields)} WHERE id = %s RETURNING *;"
    
    cursor.execute(query, tuple(values))
    updated_client = cursor.fetchone()
    db.commit()
    cursor.close()

    if not updated_client:
        raise HTTPException(status_code=404, detail="Client not found")
    return updated_client

# 4. DELETE a client
@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: str, db = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM clients WHERE id = %s;", (client_id,))
    db.commit()
    cursor.close()
    return {"message": "Client deleted successfully"}

# 5. GET client details with all related data
@router.get("/{client_id}/details")
def get_client_details(client_id: str, db = Depends(get_db)):
    cursor = db.cursor()
    
    # 1. Get client basic info
    cursor.execute("SELECT * FROM clients WHERE id = %s;", (client_id,))
    client = cursor.fetchone()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # 2. Get all projects for this client
    cursor.execute("""
        SELECT * FROM projects 
        WHERE client_id = %s 
        ORDER BY created_at DESC;
    """, (client_id,))
    projects = cursor.fetchall()
    
    # 3. Get all quotes for this client
    cursor.execute("""
        SELECT * FROM quotes 
        WHERE client_id = %s 
        ORDER BY created_at DESC;
    """, (client_id,))
    quotes = cursor.fetchall()
    
    # FIX: Safely parse JSONB items for quotes
    for q in quotes:
        if q.get('items') is None:
            q['items'] = []
        elif isinstance(q['items'], str):
            q['items'] = json.loads(q['items'])
    
    # 4. Get all invoices for this client
    cursor.execute("""
        SELECT * FROM invoices 
        WHERE client_id = %s 
        ORDER BY created_at DESC;
    """, (client_id,))
    invoices = cursor.fetchall()
    
    # FIX: Safely parse JSONB items for invoices
    for inv in invoices:
        if inv['items'] is None:
            inv['items'] = []
        elif isinstance(inv['items'], str):
            inv['items'] = json.loads(inv['items'])
    
    # 5. Calculate totals
    cursor.execute("""
        SELECT 
            COALESCE(SUM(total_amount), 0) as total_invoiced,
            COALESCE(SUM(amount_paid), 0) as total_paid
        FROM invoices 
        WHERE client_id = %s;
    """, (client_id,))
    financials = cursor.fetchone()
    
    cursor.close()
    
    return {
        "client": client,
        "projects": projects,
        "quotes": quotes,
        "invoices": invoices,
        "total_invoiced": float(financials['total_invoiced']),
        "total_paid": float(financials['total_paid']),
        "balance_due": float(financials['total_invoiced']) - float(financials['total_paid'])
    }
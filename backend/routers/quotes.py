from fastapi import APIRouter, Depends, HTTPException
from database import get_db
import uuid

router = APIRouter()

@router.put("/{quote_id}/status")
def update_quote_status(quote_id: str, data: dict, db = Depends(get_db)):
    new_status = data.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    cursor = db.cursor()
    
    # 1. Get the quote details
    cursor.execute("""
        SELECT q.*, c.name as client_name 
        FROM quotes q 
        JOIN clients c ON q.client_id = c.id 
        WHERE q.id = %s;
    """, (quote_id,))
    quote = cursor.fetchone()
    
    if not quote:
        cursor.close()
        raise HTTPException(status_code=404, detail="Quote not found")
    
    # 2. Check if project already exists for this quote (prevent duplicates)
    if new_status == "Accepted":
        cursor.execute("""
            SELECT id FROM projects 
            WHERE client_id = %s AND name LIKE %s;
        """, (quote['client_id'], f"%{quote['quote_number']}%"))
        
        existing_project = cursor.fetchone()
        
        if not existing_project:
            # 3. CREATE PROJECT AUTOMATICALLY
            project_id = str(uuid.uuid4())
            project_name = f"Project - {quote['quote_number']}"
            
            cursor.execute("""
                INSERT INTO projects (id, client_id, name, status, total_cost, notes)
                VALUES (%s, %s, %s, 'Pending', %s, %s)
                RETURNING id;
            """, (
                project_id, 
                quote['client_id'], 
                project_name, 
                quote['total_amount'],
                f"Auto-created from Quote {quote['quote_number']}\nClient: {quote['client_name']}"
            ))
            
            # 4. CREATE TASKS FROM QUOTE ITEMS
            if quote['items']:
                items = quote['items'] if isinstance(quote['items'], list) else []
                for item in items:
                    task_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO tasks (id, project_id, title, description, status, task_cost, assigned_to)
                        VALUES (%s, %s, %s, %s, 'To Do', %s, %s);
                    """, (
                        task_id,
                        project_id,
                        item.get('description', 'Task'),
                        item.get('process', ''),
                        item.get('rate', 0) * item.get('qty', 1),
                        'MD Saeed'  # Default assignee
                    ))
            
            db.commit()
            created_project_id = project_id
        else:
            created_project_id = existing_project['id']
    
    # 5. Update quote status
    cursor.execute("""
        UPDATE quotes SET status = %s WHERE id = %s;
    """, (new_status, quote_id))
    
    db.commit()
    cursor.close()
    
    response = {"message": f"Status updated to {new_status}"}
    
    # 6. Return project info if a new one was created
    if new_status == "Accepted" and not existing_project:
        response["project_created"] = True
        response["project_id"] = created_project_id
        response["project_name"] = project_name
    
    return response
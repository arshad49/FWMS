from fastapi import APIRouter, Depends
from database import get_db

router = APIRouter()

@router.get("/")
def get_notifications(db = Depends(get_db)):
    cursor = db.cursor()
    notifications = []

    # 1. Overdue Invoices (Unpaid and past due date)
    cursor.execute("""
        SELECT i.invoice_number, i.due_date, c.name as client_name, 
               (i.total_amount - i.amount_paid) as balance
        FROM invoices i
        JOIN clients c ON i.client_id = c.id
        WHERE i.due_date < CURRENT_DATE AND i.status != 'Paid';
    """)
    for row in cursor.fetchall():
        notifications.append({
            "id": f"inv_{row['invoice_number']}",
            "type": "overdue",
            "title": f"Invoice {row['invoice_number']} is overdue",
            "message": f"Balance of ₹{row['balance']:,.0f} due from {row['client_name']}",
            "date": row['due_date'].strftime('%d %b %Y') if hasattr(row['due_date'], 'strftime') else str(row['due_date']),
            "severity": "high"
        })

    # 2. Upcoming Task Deadlines (Due within the next 3 days)
    cursor.execute("""
        SELECT t.title, t.deadline, p.name as project_name, t.assigned_to
        FROM tasks t
        JOIN projects p ON t.project_id = p.id
        WHERE t.deadline BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '3 days' 
        AND t.status != 'Done';
    """)
    for row in cursor.fetchall():
        notifications.append({
            "id": f"task_{row['title']}_{row['deadline']}",
            "type": "upcoming",
            "title": f"Task '{row['title']}' due soon",
            "message": f"For {row['project_name']} • Assigned to {row['assigned_to'] or 'You'}",
            "date": row['deadline'].strftime('%d %b %Y') if hasattr(row['deadline'], 'strftime') else str(row['deadline']),
            "severity": "medium"
        })

    cursor.close()
    
    # Sort: High severity first, then by date
    return sorted(notifications, key=lambda x: (0 if x['severity'] == 'high' else 1, x['date']))
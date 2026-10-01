from fastapi import APIRouter, Depends, HTTPException
from database import get_db

router = APIRouter()

@router.get("/stats")
def get_dashboard_stats(db = Depends(get_db)):
    cursor = db.cursor()
    stats = {}

    # 1. Total Clients
    cursor.execute("SELECT COUNT(*) as count FROM clients;")
    result = cursor.fetchone()
    stats['total_clients'] = result['count'] if result else 0

    # 2. Active Projects (Pending or In Progress)
    cursor.execute("SELECT COUNT(*) as count FROM projects WHERE status IN ('Pending', 'In Progress');")
    result = cursor.fetchone()
    stats['active_projects'] = result['count'] if result else 0

    # 3. Financials (Invoiced vs Paid vs Due)
    cursor.execute("""
        SELECT 
            COALESCE(SUM(total_amount), 0) as total_invoiced,
            COALESCE(SUM(amount_paid), 0) as total_received
        FROM invoices;
    """)
    financials = cursor.fetchone()
    stats['total_invoiced'] = float(financials['total_invoiced'] or 0)
    stats['total_received'] = float(financials['total_received'] or 0)
    stats['balance_due'] = stats['total_invoiced'] - stats['total_received']

    # 4. Upcoming Deadlines (Next 5 projects that aren't completed)
    cursor.execute("""
        SELECT p.name as project_name, p.deadline, c.name as client_name 
        FROM projects p 
        JOIN clients c ON p.client_id = c.id 
        WHERE p.deadline >= CURRENT_DATE AND p.status != 'Completed'
        ORDER BY p.deadline ASC 
        LIMIT 5;
    """)
    stats['upcoming_deadlines'] = cursor.fetchall()

    cursor.close()
    return stats

@router.get("/charts")
def get_chart_data(db = Depends(get_db)):
    cursor = db.cursor()
    
    # 1. Project Status Breakdown (Most reliable across all SQL dialects)
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM projects
        GROUP BY status;
    """)
    project_status_data = cursor.fetchall()
    
    # 2. Revenue Over Time (Last 6 months) - Postgres syntax
    try:
        cursor.execute("""
            SELECT 
                TO_CHAR(created_at, 'YYYY-MM') as month,
                SUM(total_amount) as revenue
            FROM invoices
            WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY TO_CHAR(created_at, 'YYYY-MM')
            ORDER BY month ASC;
        """)
        revenue_data = cursor.fetchall()
    except Exception:
        revenue_data = [] # Fallback if DB is empty or syntax varies slightly

    # 3. Invoiced vs Received (Last 6 months)
    try:
        cursor.execute("""
            SELECT 
                TO_CHAR(created_at, 'YYYY-MM') as month,
                SUM(total_amount) as invoiced,
                SUM(amount_paid) as received
            FROM invoices
            WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
            GROUP BY TO_CHAR(created_at, 'YYYY-MM')
            ORDER BY month ASC;
        """)
        comparison_data = cursor.fetchall()
    except Exception:
        comparison_data = []

    cursor.close()
    
    return {
        "revenue": [{"month": str(row['month']), "revenue": float(row['revenue'] or 0)} for row in (revenue_data or [])],
        "project_status": [{"status": str(row['status']), "count": int(row['count'])} for row in (project_status_data or [])],
        "comparison": [{"month": str(row['month']), "invoiced": float(row['invoiced'] or 0), "received": float(row['received'] or 0)} for row in (comparison_data or [])]
    }
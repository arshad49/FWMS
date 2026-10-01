from langchain_core.tools import tool
import psycopg2
import json
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import your custom calendar function (safe fallback if not yet created)
try:
    from google_calendar import create_calendar_event
except ImportError:
    create_calendar_event = None

load_dotenv()

def get_db_connection():
    """Create a direct Supabase database connection."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL not found in .env file")
    return psycopg2.connect(db_url)

@tool
def get_all_clients() -> str:
    """Get a list of all clients with their contact information."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, company, phone, email FROM clients ORDER BY name;")
        clients = cursor.fetchall()
        
        if not clients:
            return "No clients found in the database."
        
        result = [{"id": str(c[0]), "name": c[1], "company": c[2] or "", "phone": c[3] or "", "email": c[4] or ""} for c in clients]
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error fetching clients: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def get_client_balance(client_name: str) -> str:
    """Get the balance due for a specific client."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM clients WHERE LOWER(name) LIKE LOWER(%s);", (f"%{client_name}%",))
        client = cursor.fetchone()
        
        if not client:
            return f"Client '{client_name}' not found."
        
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0), COALESCE(SUM(amount_paid), 0) FROM invoices WHERE client_id = %s;", (client[0],))
        result = cursor.fetchone()
        
        total_invoiced = float(result[0] or 0)
        total_paid = float(result[1] or 0)
        
        return json.dumps({
            "client_name": client[1], 
            "total_invoiced": total_invoiced, 
            "total_paid": total_paid, 
            "balance_due": total_invoiced - total_paid
        }, indent=2)
    except Exception as e:
        return f"Error fetching balance: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def get_all_projects(status: str = None) -> str:
    """Get a list of all projects. Optionally filter by status (Pending, In Progress, Completed, On Hold)."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT p.id, p.name, p.status, p.total_cost, p.deadline, c.name as client_name FROM projects p LEFT JOIN clients c ON p.client_id = c.id"
        
        if status:
            query += " WHERE p.status = %s"
            cursor.execute(query, (status,))
        else:
            query += " ORDER BY p.created_at DESC;"
            cursor.execute(query)
        
        projects = cursor.fetchall()
        if not projects:
            return "No projects found."
        
        result = [{
            "id": str(p[0]), "name": p[1], "status": p[2], 
            "client_name": p[5] or "Unknown", "total_cost": float(p[3] or 0), 
            "deadline": str(p[4]) if p[4] else "Not set"
        } for p in projects]
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error fetching projects: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def get_dashboard_summary() -> str:
    """Get a summary of the business: total revenue, clients, active projects, and upcoming deadlines."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COALESCE(SUM(total_amount), 0), COALESCE(SUM(amount_paid), 0) FROM invoices;")
        financials = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM clients;")
        total_clients = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projects WHERE status IN ('Pending', 'In Progress');")
        active_projects = cursor.fetchone()[0]
        
        cursor.execute("SELECT name, deadline FROM projects WHERE deadline >= CURRENT_DATE AND status != 'Completed' ORDER BY deadline ASC LIMIT 5;")
        deadlines = cursor.fetchall()
        
        summary = {
            "total_invoiced": float(financials[0] or 0),
            "total_received": float(financials[1] or 0),
            "balance_due": float(financials[0] or 0) - float(financials[1] or 0),
            "total_clients": total_clients,
            "active_projects": active_projects,
            "upcoming_deadlines": [{"project": d[0], "deadline": str(d[1])} for d in deadlines]
        }
        return json.dumps(summary, indent=2)
    except Exception as e:
        return f"Error fetching summary: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def mark_project_complete(project_name: str) -> str:
    """Mark a specific project as 'Completed' in the database."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, status FROM projects WHERE LOWER(name) LIKE LOWER(%s);", (f"%{project_name}%",))
        project = cursor.fetchone()
        
        if not project:
            return f"Project '{project_name}' not found."
        if project[2] == 'Completed':
            return f"Project '{project[1]}' is already marked as completed."
        
        cursor.execute("UPDATE projects SET status = 'Completed' WHERE id = %s;", (project[0],))
        conn.commit()
        return f"✅ Successfully marked project '{project[1]}' as Completed."
    except Exception as e:
        return f"Error updating project: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def get_client_details(client_name: str) -> str:
    """Get complete details for a specific client including all their projects and invoices."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, company, phone, email FROM clients WHERE LOWER(name) LIKE LOWER(%s);", (f"%{client_name}%",))
        client = cursor.fetchone()
        
        if not client:
            return f"Client '{client_name}' not found."
        
        cursor.execute("SELECT name, status, total_cost, deadline FROM projects WHERE client_id = %s ORDER BY created_at DESC;", (client[0],))
        projects = cursor.fetchall()
        
        cursor.execute("SELECT id, total_amount, amount_paid, status, created_at FROM invoices WHERE client_id = %s ORDER BY created_at DESC;", (client[0],))
        invoices = cursor.fetchall()
        
        result = {
            "client": {"id": str(client[0]), "name": client[1], "company": client[2] or "", "phone": client[3] or "", "email": client[4] or ""},
            "projects": [{"name": p[0], "status": p[1], "total_cost": float(p[2] or 0), "deadline": str(p[3]) if p[3] else "Not set"} for p in projects],
            "invoices": [{"id": str(inv[0]), "total_amount": float(inv[1] or 0), "amount_paid": float(inv[2] or 0), "status": inv[3], "created_at": str(inv[4])} for inv in invoices]
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error fetching client details: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def get_invoices(client_name: str = None, status: str = None) -> str:
    """Get a list of invoices. Optionally filter by client name or status (Pending, Paid, Overdue)."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT i.id, i.total_amount, i.amount_paid, i.status, i.created_at, c.name as client_name FROM invoices i LEFT JOIN clients c ON i.client_id = c.id"
        conditions, params = [], []
        
        if client_name:
            conditions.append("LOWER(c.name) LIKE LOWER(%s)")
            params.append(f"%{client_name}%")
        if status:
            conditions.append("i.status = %s")
            params.append(status)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY i.created_at DESC;"
        
        cursor.execute(query, params)
        invoices = cursor.fetchall()
        if not invoices:
            return "No invoices found."
        
        result = [{
            "id": str(inv[0]), "client_name": inv[5] or "Unknown", 
            "total_amount": float(inv[1] or 0), "amount_paid": float(inv[2] or 0), 
            "balance_due": float(inv[1] or 0) - float(inv[2] or 0), 
            "status": inv[3], "created_at": str(inv[4])
        } for inv in invoices]
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error fetching invoices: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def create_client(name: str, company: str = None, email: str = None, phone: str = None) -> str:
    """Create a new client. REQUIRED: name. OPTIONAL: company, email, phone."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if client already exists by name or company
        cursor.execute("""
            SELECT id, name, company FROM clients 
            WHERE LOWER(name) = LOWER(%s) OR LOWER(company) = LOWER(%s) 
            LIMIT 1;
        """, (name, name))
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            # 🤖 AGENT-FRIENDLY: Factual, no questions
            return f"✅ Client '{existing[1]}' already exists (ID: {existing[0]}). Proceeding with existing client."
        
        # Create new client
        cursor.execute("""
            INSERT INTO clients (name, company, email, phone)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (name, company, email, phone))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # 🤖 AGENT-FRIENDLY: Factual, no questions about missing fields
        return f"✅ Successfully created new client '{name}' (ID: {new_id})."
        
    except Exception as e:
        if cursor: cursor.close()
        if conn: conn.close()
        return f"❌ Error creating client: {str(e)}"
    """Create a new client. REQUIRED: name. OPTIONAL: company, email, phone."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM clients WHERE LOWER(name) = LOWER(%s);", (name,))
        existing = cursor.fetchone()
        
        if existing:
            return f"⚠️ A client named '{existing[1]}' already exists (ID: {existing[0]}). Would you like to view their details or create a client with a different name?"
        
        cursor.execute("""
            INSERT INTO clients (name, company, email, phone)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (name, company, email, phone))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        
        response = f"✅ Successfully created client '{name}' (ID: {new_id})."
        missing = [field for field, val in [("company", company), ("email", email), ("phone", phone)] if not val]
        if missing:
            response += f"\n\nWould you like to add their {', '.join(missing)}?"
        
        return response
    except Exception as e:
        return f"❌ Error creating client: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def create_project(client_name: str, project_name: str, total_cost: float = 0, deadline: str = None) -> str:
    """Create a new project. Auto-creates client if needed. REQUIRED: client_name, project_name. OPTIONAL: total_cost (defaults to 0), deadline."""
    conn = None
    cursor = None
    try:
        from datetime import datetime, timedelta
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 🎯 PROACTIVE: Auto-create client if it doesn't exist
        cursor.execute("SELECT id FROM clients WHERE LOWER(name) LIKE LOWER(%s) OR LOWER(company) LIKE LOWER(%s) LIMIT 1;", 
                       (f"%{client_name}%", f"%{client_name}%"))
        client = cursor.fetchone()
        
        if not client:
            # Create the client automatically
            cursor.execute("""
                INSERT INTO clients (name, company)
                VALUES (%s, %s)
                RETURNING id;
            """, (client_name, client_name))
            client_id = cursor.fetchone()[0]
        else:
            client_id = client[0]
        
        # Check if project already exists
        cursor.execute("SELECT id FROM projects WHERE LOWER(name) = LOWER(%s) AND client_id = %s;", 
                       (project_name, client_id))
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return f"✅ Project '{project_name}' already exists (ID: {existing[0]}). Proceeding with existing project."
        
        # Parse deadline
        parsed_deadline = None
        if deadline:
            try:
                deadline_lower = deadline.lower()
                if "day" in deadline_lower:
                    days = int(''.join(filter(str.isdigit, deadline)))
                    parsed_deadline = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
                elif "week" in deadline_lower:
                    weeks = int(''.join(filter(str.isdigit, deadline)))
                    parsed_deadline = (datetime.now() + timedelta(weeks=weeks)).strftime('%Y-%m-%d')
                elif "month" in deadline_lower:
                    months = int(''.join(filter(str.isdigit, deadline)))
                    parsed_deadline = (datetime.now() + timedelta(days=months*30)).strftime('%Y-%m-%d')
                else:
                    parsed_deadline = deadline
            except:
                parsed_deadline = deadline
        
        # Insert project
        cursor.execute("""
            INSERT INTO projects (client_id, name, status, total_cost, deadline)
            VALUES (%s, %s, 'Pending', %s, %s)
            RETURNING id;
        """, (client_id, project_name, total_cost, parsed_deadline))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        
        # 🤖 CLEAN RESPONSE: No questions, just facts
        response = f"✅ Project '{project_name}' created for '{client_name}' (ID: {new_id})."
        if total_cost > 0:
            response += f" Total cost: ₹{total_cost:,.2f}."
        if parsed_deadline:
            response += f" Deadline: {parsed_deadline}."
        
        return response
        
    except Exception as e:
        return f"❌ Error creating project: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

    """Create a new project. REQUIRED: client_name, project_name. OPTIONAL: total_cost (defaults to 0), deadline."""
    conn = None
    cursor = None
    try:
        from datetime import datetime, timedelta
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 🎯 PROACTIVE: Auto-create client if it doesn't exist
        cursor.execute("SELECT id FROM clients WHERE LOWER(name) LIKE LOWER(%s) OR LOWER(company) LIKE LOWER(%s) LIMIT 1;", 
                       (f"%{client_name}%", f"%{client_name}%"))
        client = cursor.fetchone()
        
        if not client:
            # Create the client automatically
            cursor.execute("""
                INSERT INTO clients (name, company)
                VALUES (%s, %s)
                RETURNING id;
            """, (client_name, client_name))
            client_id = cursor.fetchone()[0]
        else:
            client_id = client[0]
        
        # Check if project already exists
        cursor.execute("SELECT id FROM projects WHERE LOWER(name) = LOWER(%s) AND client_id = %s;", 
                       (project_name, client_id))
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return f"✅ Project '{project_name}' already exists (ID: {existing[0]}). Proceeding with existing project."
        
        # Parse deadline
        parsed_deadline = None
        if deadline:
            try:
                deadline_lower = deadline.lower()
                if "day" in deadline_lower:
                    days = int(''.join(filter(str.isdigit, deadline)))
                    parsed_deadline = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
                elif "week" in deadline_lower:
                    weeks = int(''.join(filter(str.isdigit, deadline)))
                    parsed_deadline = (datetime.now() + timedelta(weeks=weeks)).strftime('%Y-%m-%d')
                elif "month" in deadline_lower:
                    months = int(''.join(filter(str.isdigit, deadline)))
                    parsed_deadline = (datetime.now() + timedelta(days=months*30)).strftime('%Y-%m-%d')
                else:
                    parsed_deadline = deadline
            except:
                parsed_deadline = deadline
        
        # Insert project
        cursor.execute("""
            INSERT INTO projects (client_id, name, status, total_cost, deadline)
            VALUES (%s, %s, 'Pending', %s, %s)
            RETURNING id;
        """, (client_id, project_name, total_cost, parsed_deadline))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        
        # 🤖 CLEAN RESPONSE: No questions, just facts
        response = f"✅ Project '{project_name}' created for '{client_name}' (ID: {new_id})."
        if total_cost > 0:
            response += f" Total cost: ₹{total_cost:,.2f}."
        if parsed_deadline:
            response += f" Deadline: {parsed_deadline}."
        
        return response
        
    except Exception as e:
        return f"❌ Error creating project: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
@tool
def create_invoice(client_name: str, invoice_number: str, items: list, due_date: str = None) -> str:
    """Create a new invoice for a client with multiple line items."""
    try:
        import json
        from datetime import datetime, timedelta
        
        conn = get_db_connection()
        cursor = conn.cursor()
        

        # Check if invoice already exists
        cursor.execute("SELECT id FROM invoices WHERE invoice_number = %s;", (invoice_number,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            # 🤖 AGENT-FRIENDLY: Factual error, no questions
            return f"❌ Invoice '{invoice_number}' already exists. Cannot create duplicate."
            
        # 1. Find the client
        cursor.execute("SELECT id FROM clients WHERE LOWER(name) LIKE LOWER(%s) OR LOWER(company) LIKE LOWER(%s) LIMIT 1;", 
                       (f"%{client_name}%", f"%{client_name}%"))
        client = cursor.fetchone()
        
        if not client:
            cursor.close()
            conn.close()
            return f"❌ Client '{client_name}' not found. Please create the client first."
        
        client_id = client[0]
        
        # 2. Calculate totals from items
        total_amount = sum(float(item.get('amount', 0)) for item in items)
        
        # 3. Set default due date if not provided (30 days from now)
        if not due_date:
            due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # 4. Insert invoice
        cursor.execute("""
            INSERT INTO invoices (client_id, invoice_number, status, total_amount, due_date, items, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            RETURNING id;
        """, (client_id, invoice_number, 'Draft', total_amount, due_date, json.dumps(items)))
        
        invoice_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        return f"✅ Successfully created invoice '{invoice_number}' for {client_name}. Total: ₹{total_amount:,.2f}. Due: {due_date}."
        
    except Exception as e:
        return f"❌ Error creating invoice: {str(e)}"
    """Create an invoice for a project. REQUIRED: client_name, project_name, amount. OPTIONAL: invoice_number."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM clients WHERE LOWER(name) LIKE LOWER(%s);", (f"%{client_name}%",))
        client = cursor.fetchone()
        if not client:
            return f"❌ Client '{client_name}' not found."
        
        cursor.execute("SELECT id FROM projects WHERE LOWER(name) LIKE LOWER(%s) AND client_id = %s;", (f"%{project_name}%", client[0]))
        project = cursor.fetchone()
        if not project:
            return f"❌ Project '{project_name}' not found for client '{client_name}'."
        
        if not invoice_number:
            cursor.execute("SELECT COUNT(*) FROM invoices;")
            count = cursor.fetchone()[0] + 1
            invoice_number = f"INV-{count:04d}"
        
        cursor.execute("""
            INSERT INTO invoices (client_id, project_id, invoice_number, total_amount, amount_paid, status)
            VALUES (%s, %s, %s, %s, 0, 'Pending')
            RETURNING id;
        """, (client[0], project[0], invoice_number, amount))
        
        new_id = cursor.fetchone()[0]
        conn.commit()
        
        return f"✅ Invoice {invoice_number} created for project '{project_name}' (Client: {client_name}). Amount: ₹{amount:,.2f}. Status: Pending."
    except Exception as e:
        return f"❌ Error creating invoice: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def record_payment(client_name: str, amount: float, payment_method: str = "Unknown", invoice_number: str = None) -> str:
    """Record a payment received from a client, optionally linked to an invoice number."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Find the client
        cursor.execute("""
            SELECT id FROM clients 
            WHERE LOWER(name) LIKE LOWER(%s) OR LOWER(company) LIKE LOWER(%s) 
            LIMIT 1;
        """, (f"%{client_name}%", f"%{client_name}%"))
        client = cursor.fetchone()
        
        if not client:
            cursor.close()
            conn.close()
            return f"❌ Client '{client_name}' not found."
        
        client_id = client[0]
        invoice_id = None
        
        # 2. If invoice_number is provided, find the invoice ID
        if invoice_number:
            cursor.execute("""
                SELECT id FROM invoices 
                WHERE invoice_number = %s AND client_id = %s;
            """, (invoice_number, client_id))
            inv = cursor.fetchone()
            
            if inv:
                invoice_id = inv[0]
            else:
                cursor.close()
                conn.close()
                return f"❌ Invoice '{invoice_number}' not found for client '{client_name}'."
        
        # 3. Insert the payment
        cursor.execute("""
            INSERT INTO payments (client_id, invoice_id, amount, payment_method, payment_date)
            VALUES (%s, %s, %s, %s, NOW())
        """, (client_id, invoice_id, amount, payment_method))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        inv_msg = f" for invoice {invoice_number}" if invoice_number else ""
        return f"✅ Successfully recorded payment of ₹{amount:,.2f} from {client_name}{inv_msg} via {payment_method}."
        
    except Exception as e:
        return f"❌ Error recording payment: {str(e)}"
    """Record a payment. REQUIRED: invoice_id, amount."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, total_amount, amount_paid, status FROM invoices WHERE id = %s;", (invoice_id,))
        invoice = cursor.fetchone()
        
        if not invoice:
            return f"❌ Invoice #{invoice_id} not found."
        
        current_paid = float(invoice[2] or 0)
        total_amount = float(invoice[1] or 0)
        new_paid = current_paid + amount
        
        if new_paid > total_amount:
            return f"⚠️ Payment of ₹{amount:,.2f} would exceed the invoice total of ₹{total_amount:,.2f}. Current paid: ₹{current_paid:,.2f}. Please confirm the correct amount."
        
        new_status = 'Paid' if new_paid >= total_amount else 'Pending'
        
        cursor.execute("UPDATE invoices SET amount_paid = %s, status = %s WHERE id = %s;", (new_paid, new_status, invoice_id))
        conn.commit()
        
        remaining = total_amount - new_paid
        if remaining == 0:
            return f"✅ Full payment of ₹{amount:,.2f} recorded for invoice #{invoice_id}. Invoice is now fully paid!"
        else:
            return f"✅ Payment of ₹{amount:,.2f} recorded for invoice #{invoice_id}. Remaining balance: ₹{remaining:,.2f}"
    except Exception as e:
        return f"❌ Error recording payment: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def add_deadline_to_calendar(project_name: str, deadline: str, client_name: str = "") -> str:
    """Add a project deadline to Google Calendar. REQUIRED: project_name, deadline (YYYY-MM-DD). OPTIONAL: client_name."""
    if not create_calendar_event:
        return "⚠️ Google Calendar integration is not set up yet."
    try:
        return create_calendar_event(project_name, deadline, client_name)
    except Exception as e:
        return f"❌ Error adding to calendar: {str(e)}"

@tool
def create_quote(
    client_name: str,
    quote_number: str,
    to_name: str,
    items: list,
    requirements: str = None,
    timeline: list = None,
    terms: str = None,
    payment_schedule: str = "Project advance 50% on total work amount, and 50% final project submitting",
    from_name: str = "MD SAEED",
    from_email: str = "muhammadsaeed999@gmail.com",
    from_phone: str = "+91 7559978561",
    tax_rate: float = 0,
    discount: float = 0,
    valid_days: int = 30,
    notes: str = None
) -> str:
    """Create a complete quotation. REQUIRED: client_name, quote_number, to_name, items (list of dicts with 'description' and 'amount'). Does NOT auto-generate PDF."""
    from datetime import datetime, timedelta
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Find client
        cursor.execute("SELECT id FROM clients WHERE LOWER(name) LIKE LOWER(%s) OR LOWER(company) LIKE LOWER(%s);", (f"%{client_name}%", f"%{client_name}%"))
        client = cursor.fetchone()
        if not client:
            return f"❌ Client '{client_name}' not found. Please create the client first."
        
        client_id = client[0]
        
        # 2. Check if quote already exists
        cursor.execute("SELECT id FROM quotes WHERE quote_number = %s;", (quote_number,))
        if cursor.fetchone():
            return f"❌ Quote '{quote_number}' already exists. Cannot create duplicate."
        
        # 3. Calculate totals
        subtotal = sum(float(item.get('amount', 0)) for item in items)
        tax_amount = (subtotal * tax_rate) / 100
        total_amount = subtotal + tax_amount - discount
        valid_until = (datetime.now() + timedelta(days=valid_days)).strftime('%Y-%m-%d')
        
        # 4. Insert quote
        cursor.execute("""
            INSERT INTO quotes (
                client_id, quote_number, quotation_date, valid_until,
                from_name, from_email, from_phone, to_name,
                requirements, subtotal, tax_rate, tax_amount, discount, total_amount,
                terms, payment_schedule, notes, status
            ) VALUES (%s, %s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Draft')
            RETURNING id;
        """, (
            client_id, quote_number, valid_until,
            from_name, from_email, from_phone, to_name,
            requirements, subtotal, tax_rate, tax_amount, discount, total_amount,
            terms, payment_schedule, notes
        ))
        
        quote_id = cursor.fetchone()[0]
        
        # 5. Insert items
        for i, item in enumerate(items):
            cursor.execute("""
                INSERT INTO quote_items (quote_id, description, note, quantity, rate, amount, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (quote_id, item.get('description', ''), item.get('note', ''), item.get('quantity', 1), item.get('amount', 0), item.get('amount', 0), i))
        
        # 6. Insert timeline (if provided)
        if timeline:
            for i, tl in enumerate(timeline):
                cursor.execute("""
                    INSERT INTO quote_timeline (quote_id, process, note, delivery, sort_order)
                    VALUES (%s, %s, %s, %s, %s);
                """, (quote_id, tl.get('process', ''), tl.get('note', ''), tl.get('delivery', ''), i))
        
        conn.commit()
        
        # 🤖 CLEAN RESPONSE: No PDF generation, just facts for the AI to use
        return f"✅ Quotation '{quote_number}' created successfully for {to_name}. Total: ₹{total_amount:,.2f}."
        
    except Exception as e:
        return f"❌ Error creating quote: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def convert_quote_to_project(quote_number: str) -> str:
    """Convert an accepted quotation into a project. Auto-updates quote status to 'Accepted'."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Find the quote
        cursor.execute("""
            SELECT q.id, q.quote_number, q.to_name, q.total_amount, q.client_id,
                   c.name as client_name
            FROM quotes q
            LEFT JOIN clients c ON q.client_id = c.id
            WHERE q.quote_number = %s;
        """, (quote_number,))
        quote = cursor.fetchone()
        
        if not quote:
            return f"❌ Quote '{quote_number}' not found."
        
        quote_id, q_number, to_name, total_amount, client_id, client_name = quote
        
        # 2. Check if project already exists for this quote
        cursor.execute("SELECT id FROM projects WHERE quote_id = %s;", (quote_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return f"✅ Project for quote '{quote_number}' already exists (ID: {existing[0]})."
        
        # 3. Create project name from quote
        project_name = f"Project - {q_number}"
        
        # 4. Insert project linked to quote
        cursor.execute("""
            INSERT INTO projects (client_id, name, status, total_cost, quote_id, source)
            VALUES (%s, %s, 'Pending', %s, %s, 'quote')
            RETURNING id;
        """, (client_id, project_name, total_amount, quote_id))
        
        project_id = cursor.fetchone()[0]
        
        # 5. Update quote status to 'Accepted'
        cursor.execute("""
            UPDATE quotes SET status = 'Accepted' WHERE id = %s;
        """, (quote_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return (f"✅ Quote '{quote_number}' converted to project!\n"
                f"📋 Project: '{project_name}' (ID: {project_id})\n"
                f"💰 Budget: ₹{float(total_amount):,.2f}\n"
                f"👤 Client: {client_name}\n"
                f"📄 Quote status updated to 'Accepted'")
        
    except Exception as e:
        return f"❌ Error converting quote to project: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def generate_quote_pdf(quote_number: str) -> str:
    """Generate a professional PDF for a quote and send it to Telegram."""
    conn = None
    cursor = None
    try:
        print(f"\n🔍 [PDF GEN] Starting PDF generation for: {quote_number}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch quote data
        cursor.execute("""
            SELECT q.id, q.quote_number, q.quotation_date, q.valid_until,
                   q.from_name, q.from_email, q.from_phone, q.to_name,
                   q.requirements, q.subtotal, q.tax_rate, q.tax_amount, 
                   q.discount, q.total_amount, q.currency,
                   q.terms, q.payment_schedule, q.notes,
                   c.name as client_name, c.email as client_email, c.phone as client_phone
            FROM quotes q
            LEFT JOIN clients c ON q.client_id = c.id
            WHERE q.quote_number = %s;
        """, (quote_number,))
        quote = cursor.fetchone()
        
        if not quote:
            print(f"❌ [PDF GEN] Quote {quote_number} not found in database")
            return f"❌ Quote {quote_number} not found."
        
        print(f"✅ [PDF GEN] Quote found: {quote[1]}")
        
        # Fetch items and timeline
        cursor.execute("SELECT description, note, quantity, rate, amount FROM quote_items WHERE quote_id = %s ORDER BY sort_order;", (quote[0],))
        items = cursor.fetchall()
        
        cursor.execute("SELECT process, note, delivery FROM quote_timeline WHERE quote_id = %s ORDER BY sort_order;", (quote[0],))
        timeline = cursor.fetchall()
        
        print(f"✅ [PDF GEN] Found {len(items)} items and {len(timeline)} timeline entries")
        
        # Build HTML (same as before, abbreviated for space)
        quote_date = quote[2].strftime("%d-%m-%Y") if quote[2] else datetime.now().strftime("%d-%m-%Y")
        valid_until = quote[3].strftime("%d-%m-%Y") if quote[3] else "Upon Acceptance"
        
        items_html = "".join([
            f"<tr><td>{item[0]}{' <span class=\"small\">(' + item[1] + ')</span>' if item[1] else ''}</td><td>₹{item[4]:,.2f}</td></tr>"
            for item in items
        ])
        
        timeline_html = "".join([
            f"<tr><td>{tl[0]}{' <span class=\"small\">- ' + tl[1] + '</span>' if tl[1] else ''}</td><td>{tl[2]}</td></tr>"
            for tl in timeline
        ])
        
        requirements_html = f"<ol class='req-list'>{ ''.join([f'<li>{req}</li>' for req in quote[8].split('\n') if req.strip()]) }</ol>" if quote[8] else ""
        terms_html = f"<ul class='terms-list'>{ ''.join([f'<li>{term}</li>' for term in quote[15].split('\n') if term.strip()]) }</ul>" if quote[15] else ""
        currency = quote[14] or '₹'
        
        # Simplified HTML for testing
        html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Quote {quote_number}</title></head>
<body style="font-family: Arial, sans-serif; padding: 40px;">
<h1 style="color: #6100FF;">Quotation {quote[1]}</h1>
<p><strong>To:</strong> {quote[7]}</p>
<p><strong>Date:</strong> {quote_date}</p>
<p><strong>Valid Until:</strong> {valid_until}</p>
<h2>Services</h2>
<table border="1" cellpadding="10" style="border-collapse: collapse;">
<thead><tr><th>Description</th><th>Amount</th></tr></thead>
<tbody>{items_html}</tbody>
</table>
<p style="margin-top: 20px; font-size: 18px; font-weight: bold; color: #6100FF;">
Total: {currency} {float(quote[13] or 0):,.2f}
</p>
</body>
</html>"""
        
        print(f"✅ [PDF GEN] HTML generated ({len(html_content)} chars)")
        
        # Generate PDF using PDFShift
        pdf_path = f"/tmp/quote_{quote_number}.pdf"
        api_key = os.getenv("PDFSHIFT_API_KEY")
        
        if not api_key:
            print(f"❌ [PDF GEN] PDFSHIFT_API_KEY missing in .env")
            return "❌ PDFSHIFT_API_KEY is missing in .env file"
        
        print(f"📤 [PDF GEN] Calling PDFShift API...")
        response = requests.post(
            "https://api.pdfshift.io/v3/convert/pdf",
            auth=("api", api_key),
            json={
                "source": html_content,
                "landscape": False,
                "format": "A4"
            }
        )
        
        print(f"📊 [PDF GEN] PDFShift response status: {response.status_code}")
        
        if response.status_code == 200:
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ [PDF GEN] PDF saved to {pdf_path} ({len(response.content)} bytes)")
        else:
            print(f"❌ [PDF GEN] PDFShift failed: {response.text}")
            return f"❌ PDFShift API Error: {response.text}"
        
        # Send to Telegram
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("ADMIN_CHAT_ID")
        
        print(f"🤖 [TELEGRAM] Bot token: {bot_token[:10]}..." if bot_token else "❌ [TELEGRAM] No bot token")
        print(f"🤖 [TELEGRAM] Chat ID: {chat_id}")
        
        if not bot_token or not chat_id:
            print(f"❌ [TELEGRAM] Missing credentials")
            return f"✅ PDF generated at {pdf_path}, but TELEGRAM_BOT_TOKEN or ADMIN_CHAT_ID missing in .env"
        
        print(f"📤 [TELEGRAM] Sending PDF to Telegram...")
        
        with open(pdf_path, 'rb') as pdf_file:
            files = {'document': (f"Quote_{quote_number}.pdf", pdf_file, 'application/pdf')}
            data = {
                'chat_id': chat_id,
                'caption': f"📄 Quotation {quote_number}\nTotal: ₹{float(quote[13] or 0):,.2f}"
            }
            
            telegram_response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendDocument",
                data=data,
                files=files
            )
        
        print(f"📊 [TELEGRAM] Response status: {telegram_response.status_code}")
        print(f"📊 [TELEGRAM] Response: {telegram_response.text}")
        
        if telegram_response.status_code == 200:
            print(f"✅ [TELEGRAM] PDF sent successfully!")
            return f"✅ Quotation {quote_number} PDF generated and sent to Telegram!"
        else:
            print(f"❌ [TELEGRAM] Failed to send: {telegram_response.text}")
            return f"❌ Failed to send to Telegram: {telegram_response.text}"
            
    except Exception as e:
        print(f"❌ [PDF GEN] CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"❌ Error generating quote PDF: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
@tool
def get_quotes(client_name: str = None, quote_number: str = None) -> str:
    """
    Fetch quotations. USE THIS when the user asks to 'fetch', 'show', 'get', 'send', or 'generate PDF' for a quote or quotation. 
    Returns a list of quotes with their quote_number, which is required to generate the PDF.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT q.id, q.quote_number, q.quotation_date, q.valid_until,
                   q.to_name, q.total_amount, q.status, q.created_at,
                   c.name as client_name
            FROM quotes q
            LEFT JOIN clients c ON q.client_id = c.id
        """
        
        conditions = []
        params = []
        
        if quote_number:
            conditions.append("q.quote_number ILIKE %s")
            params.append(f"%{quote_number}%")
        elif client_name:
            conditions.append("LOWER(c.name) LIKE LOWER(%s)")
            params.append(f"%{client_name}%")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY q.created_at DESC;"
        
        cursor.execute(query, params)
        quotes = cursor.fetchall()
        
        if not quotes:
            return f"No quotations found{' for ' + client_name if client_name else ''}."
        
        result = [{
            "quote_number": q[1],
            "client_name": q[8] or "Unknown",
            "to_name": q[4] or "N/A",
            "total_amount": float(q[5] or 0),
            "status": q[6],
            "quotation_date": str(q[2].strftime('%d-%b-%Y')) if q[2] else "N/A",
            "valid_until": str(q[3].strftime('%d-%b-%Y')) if q[3] else "N/A"
        } for q in quotes]
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error fetching quotes: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def fetch_and_send_quote_pdf(search_term: str) -> str:
    """
    Fetches a quotation by ANY search term (client name, company, quote number, project, etc.) 
    and IMMEDIATELY sends the PDF to Telegram.
    
    USE THIS when the user says "fetch quote", "send quote", "get PDF", or "send me the quotation".
    
    Examples:
    - "Send quote for TechCorp" (searches client name)
    - "Send Q-123" (searches quote number)
    - "Send quote for ABC Company" (searches company name)
    - "Send the website project quote" (searches to_name or requirements)
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Flexible search across multiple fields
        query = """
            SELECT q.quote_number, q.to_name, q.total_amount, q.requirements,
                   c.name as client_name, c.company
            FROM quotes q
            LEFT JOIN clients c ON q.client_id = c.id
            WHERE 
                LOWER(q.quote_number) LIKE LOWER(%s)
                OR LOWER(q.to_name) LIKE LOWER(%s)
                OR LOWER(c.name) LIKE LOWER(%s)
                OR LOWER(c.company) LIKE LOWER(%s)
                OR LOWER(q.requirements) LIKE LOWER(%s)
            ORDER BY q.created_at DESC
            LIMIT 1;
        """
        
        search_pattern = f"%{search_term}%"
        params = [search_pattern] * 5  # Repeat for each LIKE clause
        
        cursor.execute(query, params)
        quote = cursor.fetchone()
        
        if not quote:
            return f"❌ No quotation found matching '{search_term}'. Try a different search term."
        
        found_quote_number = quote[0]
        to_name = quote[1] or "Client"
        total_amount = float(quote[2] or 0)
        client_name = quote[4] or "Unknown"
        company = quote[5] or ""
        
        # IMMEDIATELY trigger the PDF generation and Telegram send
        pdf_result = generate_quote_pdf.invoke({"quote_number": found_quote_number})
        
        if "✅" in pdf_result:
            identifier = f"{client_name}" + (f" ({company})" if company else "")
            return f"✅ PDF for {identifier} (Quote: {found_quote_number}, Total: ₹{total_amount:,.2f}) has been sent to your Telegram!"
        else:
            return f"❌ Found the quote, but failed to send PDF: {pdf_result}"
            
    except Exception as e:
        return f"❌ Error fetching and sending quote: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
    """
    Fetches a quotation by client name or quote number and IMMEDIATELY sends the PDF to Telegram. 
    USE THIS when the user says "fetch quote", "send quote", "get PDF", or "send me the quotation".
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Find the quote
        query = """
            SELECT q.quote_number, q.to_name, q.total_amount 
            FROM quotes q
            LEFT JOIN clients c ON q.client_id = c.id
        """
        conditions = []
        params = []
        
        if quote_number:
            conditions.append("q.quote_number ILIKE %s")
            params.append(f"%{quote_number}%")
        elif client_name:
            conditions.append("LOWER(c.name) LIKE LOWER(%s)")
            params.append(f"%{client_name}%")
        else:
            return "❌ Please provide either a client name or a quote number."
            
        query += " WHERE " + " AND ".join(conditions) + " ORDER BY q.created_at DESC LIMIT 1;"
        
        cursor.execute(query, params)
        quote = cursor.fetchone()
        
        if not quote:
            return f"❌ No quotation found for '{client_name or quote_number}'."
        
        found_quote_number = quote[0]
        to_name = quote[1] or "Client"
        total_amount = float(quote[2] or 0)
        
        # 2. IMMEDIATELY trigger the PDF generation and Telegram send
        pdf_result = generate_quote_pdf.invoke({"quote_number": found_quote_number})
        
        if "✅" in pdf_result:
            return f"✅ PDF for {to_name} (Quote: {found_quote_number}, Total: ₹{total_amount:,.2f}) has been sent to your Telegram!"
        else:
            return f"❌ Found the quote, but failed to send PDF: {pdf_result}"
            
    except Exception as e:
        return f"❌ Error fetching and sending quote: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@tool
def convert_quote_to_project(quote_number: str) -> str:
    """Convert an accepted quotation into a project. Auto-updates quote status to 'Accepted'."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Find the quote
        cursor.execute("""
            SELECT q.id, q.quote_number, q.to_name, q.total_amount, q.client_id,
                   c.name as client_name
            FROM quotes q
            LEFT JOIN clients c ON q.client_id = c.id
            WHERE q.quote_number = %s;
        """, (quote_number,))
        quote = cursor.fetchone()
        
        if not quote:
            cursor.close()
            conn.close()
            return f"❌ Quote '{quote_number}' not found."
        
        quote_id, q_number, to_name, total_amount, client_id, client_name = quote
        
        # 2. Check if project already exists for this quote
        cursor.execute("SELECT id FROM projects WHERE quote_id = %s;", (quote_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return f"✅ Project for quote '{quote_number}' already exists (ID: {existing[0]})."
        
        # 3. Create project name from quote
        project_name = f"Project - {q_number}"
        
        # 4. Insert project linked to quote
        cursor.execute("""
            INSERT INTO projects (client_id, name, status, total_cost, quote_id, source)
            VALUES (%s, %s, 'Pending', %s, %s, 'quote')
            RETURNING id;
        """, (client_id, project_name, total_amount, quote_id))
        
        project_id = cursor.fetchone()[0]
        
        # 5. Update quote status to 'Accepted'
        cursor.execute("""
            UPDATE quotes SET status = 'Accepted' WHERE id = %s;
        """, (quote_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return (f"✅ Quote '{quote_number}' converted to project!\n"
                f"📋 Project: '{project_name}' (ID: {project_id})\n"
                f"💰 Budget: ₹{float(total_amount):,.2f}\n"
                f"👤 Client: {client_name}\n"
                f"📄 Quote status updated to 'Accepted'")
        
    except Exception as e:
        return f"❌ Error converting quote to project: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def mvp_send_quote_pdf(quote_number: str) -> str:
    """
    STATIC MVP FUNCTION: Generates a PDF for a quote and sends it to Telegram.
    No AI, no LLM, 100% reliable.
    """
    conn = None
    cursor = None
    try:
        print(f"\n🚀 [MVP] Starting static PDF generation for: {quote_number}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Fetch Quote Data
        cursor.execute("""
            SELECT q.quote_number, q.quotation_date, q.valid_until, q.to_name,
                   q.subtotal, q.tax_rate, q.tax_amount, q.discount, q.total_amount, q.currency,
                   q.terms, q.payment_schedule, q.notes, q.requirements,
                   c.name as client_name, c.email as client_email, c.phone as client_phone
            FROM quotes q
            LEFT JOIN clients c ON q.client_id = c.id
            WHERE q.quote_number = %s;
        """, (quote_number,))
        quote = cursor.fetchone()
        
        if not quote:
            return f"❌ Quote {quote_number} not found in database."
        
        # 2. Fetch Items & Timeline
        cursor.execute("SELECT description, note, quantity, rate, amount FROM quote_items WHERE quote_id = (SELECT id FROM quotes WHERE quote_number = %s) ORDER BY sort_order;", (quote_number,))
        items = cursor.fetchall()
        
        cursor.execute("SELECT process, note, delivery FROM quote_timeline WHERE quote_id = (SELECT id FROM quotes WHERE quote_number = %s) ORDER BY sort_order;", (quote_number,))
        timeline = cursor.fetchall()
        
        # 3. Build Simple, Clean HTML
        quote_date = quote[1].strftime("%d-%m-%Y") if quote[1] else datetime.now().strftime("%d-%m-%Y")
        valid_until = quote[2].strftime("%d-%m-%Y") if quote[2] else "Upon Acceptance"
        currency = quote[9] or '₹'
        
        items_html = "".join([f"<tr><td>{item[0]} {'('+item[1]+')' if item[1] else ''}</td><td>₹{item[4]:,.2f}</td></tr>" for item in items])
        
        html_content = f"""<!DOCTYPE html>
        <html><head><meta charset="UTF-8"><title>Quotation {quote[0]}</title>
        <style>body{{font-family:Arial,sans-serif;padding:40px;color:#333;}}
        h1{{color:#6100FF;}} table{{width:100%;border-collapse:collapse;margin:20px 0;}}
        th{{background:#6100FF;color:white;padding:10px;text-align:left;}}
        td{{padding:10px;border-bottom:1px solid #ddd;}}
        .total{{font-size:1.2em;font-weight:bold;color:#6100FF;}}</style></head>
        <body>
            <h1>Quotation {quote[0]}</h1>
            <p><strong>To:</strong> {quote[3] or 'Valued Client'} ({quote[14] or 'Client'})</p>
            <p><strong>Date:</strong> {quote_date} | <strong>Valid Until:</strong> {valid_until}</p>
            {f'<p><strong>Requirements:</strong><br>{quote[13].replace(chr(10), "<br>")}</p>' if quote[13] else ''}
            <table><thead><tr><th>Service</th><th>Amount</th></tr></thead>
            <tbody>{items_html}</tbody>
            <tfoot><tr><td class="total">Total</td><td class="total">{currency} {float(quote[8] or 0):,.2f}</td></tr></tfoot></table>
            {f'<p><strong>Payment Schedule:</strong><br>{quote[11].replace(chr(10), "<br>")}</p>' if quote[11] else ''}
        </body></html>"""
        
        # 4. Generate PDF via PDFShift
        pdf_path = f"/tmp/mvp_quote_{quote_number}.pdf"
        api_key = os.getenv("PDFSHIFT_API_KEY")
        
        response = requests.post(
            "https://api.pdfshift.io/v3/convert/pdf",
            auth=("api", api_key),
            json={"source": html_content, "landscape": False, "format": "A4"}
        )
        
        if response.status_code != 200:
            return f"❌ PDFShift failed: {response.text}"
            
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
            
        # 5. Send to Telegram
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("ADMIN_CHAT_ID")
        
        if not bot_token or not chat_id:
            return f"✅ PDF saved to {pdf_path}, but Telegram credentials missing in .env"
            
        with open(pdf_path, 'rb') as pdf_file:
            files = {'document': (f"Quote_{quote_number}.pdf", pdf_file, 'application/pdf')}
            data = {'chat_id': chat_id, 'caption': f"📄 Quotation {quote_number}\nTotal: {currency} {float(quote[8] or 0):,.2f}"}
            tg_response = requests.post(f"https://api.telegram.org/bot{bot_token}/sendDocument", data=data, files=files)
            
        if tg_response.status_code == 200:
            print(f"✅ [MVP] PDF successfully sent to Telegram!")
            return f"✅ Quotation {quote_number} PDF generated and sent to Telegram!"
        else:
            return f"❌ Telegram failed: {tg_response.text}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def mvp_smart_quote_handler(user_message: str) -> str:
    """
    SMART MVP HANDLER: Analyzes user message and automatically:
    - If it's a FETCH request: searches flexibly and sends PDF
    - If it's a CREATE request: extracts data, creates quote, sends PDF
    
    No LLM, 100% deterministic, handles any input format.
    """
    msg_lower = user_message.lower()
    
    # ========================================
    # SCENARIO 1: FETCH/SEND EXISTING QUOTE
    # ========================================
    fetch_keywords = ["send quote", "fetch quote", "get pdf", "send me the quote", 
                      "send the quote", "pdf for", "send quotation"]
    
    if any(keyword in msg_lower for keyword in fetch_keywords):
        # Extract search term (everything after "for" or the whole message)
        search_term = user_message
        if "for" in msg_lower:
            search_term = user_message.split("for", 1)[1].strip()
        elif "quote" in msg_lower:
            # Remove common prefixes
            search_term = user_message.replace("Send quote", "").replace("Send the quote", "").replace("Send me the quote", "").strip()
        
        print(f"🔍 [MVP SMART] FETCH MODE - Searching for: '{search_term}'")
        
        # Flexible search across multiple fields
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT q.quote_number, q.to_name, q.total_amount,
                       c.name as client_name, c.company
                FROM quotes q
                LEFT JOIN clients c ON q.client_id = c.id
                WHERE 
                    LOWER(q.quote_number) LIKE LOWER(%s)
                    OR LOWER(q.to_name) LIKE LOWER(%s)
                    OR LOWER(c.name) LIKE LOWER(%s)
                    OR LOWER(c.company) LIKE LOWER(%s)
                    OR LOWER(q.requirements) LIKE LOWER(%s)
                ORDER BY q.created_at DESC
                LIMIT 1;
            """
            
            search_pattern = f"%{search_term}%"
            params = [search_pattern] * 5
            
            cursor.execute(query, params)
            quote = cursor.fetchone()
            
            if not quote:
                return f"❌ No quotation found matching '{search_term}'."
            
            found_quote_number = quote[0]
            print(f"✅ [MVP SMART] Found quote: {found_quote_number}")
            
            # Now call the static PDF sender
            return mvp_send_quote_pdf(found_quote_number)
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
    
    # ========================================
    # SCENARIO 2: CREATE NEW QUOTE
    # ========================================
    create_keywords = ["create quote", "make quote", "new quote", "generate quote"]
    
    if any(keyword in msg_lower for keyword in create_keywords):
        print(f"🔨 [MVP SMART] CREATE MODE - Parsing: '{user_message}'")
        
        # Simple parser to extract quote details
        # Format: "Create quote Q-123 for ClientName with Item1 10000 and Item2 20000"
        
        try:
            # Extract quote number (look for Q-XXX pattern)
            import re
            quote_match = re.search(r'Q-[A-Z0-9-]+', user_message, re.IGNORECASE)
            quote_number = quote_match.group(0) if quote_match else f"Q-AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Extract client name (after "for" and before "with")
            client_name = "Unknown Client"
            if "for" in msg_lower and "with" in msg_lower:
                client_part = user_message.split("for", 1)[1].split("with", 1)[0].strip()
                client_name = client_part
            elif "for" in msg_lower:
                client_part = user_message.split("for", 1)[1].strip()
                # Remove any trailing words that might be items
                client_name = client_part.split()[0] if client_part else "Unknown Client"
            
            # Extract items (after "with")
            items = []
            if "with" in msg_lower:
                items_part = user_message.split("with", 1)[1].strip()
                # Simple parsing: look for "ItemName Amount" patterns
                # Example: "Logo Design 10000 and Branding 5000"
                item_matches = re.findall(r'([A-Za-z\s]+?)\s+(\d+)', items_part)
                for match in item_matches:
                    description = match[0].strip()
                    amount = float(match[1])
                    if description and amount > 0:
                        items.append({
                            "description": description,
                            "note": "",
                            "quantity": 1,
                            "amount": amount
                        })
            
            if not items:
                # Fallback: create a single item with the whole message
                items = [{
                    "description": "Custom Service",
                    "note": user_message,
                    "quantity": 1,
                    "amount": 0
                }]
            
            print(f"✅ [MVP SMART] Parsed - Quote: {quote_number}, Client: {client_name}, Items: {len(items)}")
            
            # Create the quote
            create_result = create_quote.invoke({
                "client_name": client_name,
                "quote_number": quote_number,
                "to_name": client_name,
                "items": items,
                "requirements": user_message,
                "terms": "Standard terms apply",
                "payment_schedule": "50% advance, 50% on completion"
            })
            
            if "❌" in create_result:
                return create_result
            
            # Immediately send the PDF
            print(f"✅ [MVP SMART] Quote created, now sending PDF...")
            return mvp_send_quote_pdf(quote_number)
            
        except Exception as e:
            return f"❌ Error creating quote: {str(e)}"
    
    # ========================================
    # SCENARIO 3: UNKNOWN INTENT
    # ========================================
    return "❓ I can help you with:\n• 'Send quote for [client/quote number]'\n• 'Create quote Q-XXX for [client] with [items]'"


# ==========================================
# INVOICE CRUD OPERATIONS
# ==========================================

@tool
def get_invoice_details(invoice_number: str) -> str:
    """Get detailed information about a specific invoice."""
    try:
        import json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT i.invoice_number, i.created_at, i.due_date, i.status,
                   i.subtotal, i.tax_percentage, i.total_amount, i.notes,
                   c.name as client_name, c.company, i.items
            FROM invoices i
            LEFT JOIN clients c ON i.client_id = c.id
            WHERE i.invoice_number = %s;
        """, (invoice_number,))
        invoice = cursor.fetchone()
        
        if not invoice:
            cursor.close()
            conn.close()
            return f"❌ Invoice {invoice_number} not found."
        
        # Parse JSONB items
        items_data = invoice[10] # The 'items' column
        items_list_str = "No items"
        if items_data:
            try:
                if isinstance(items_data, str):
                    items_data = json.loads(items_data)
                
                if isinstance(items_data, list):
                    items_list_str = "\n".join([f"  - {item.get('description', 'Item')}: ₹{float(item.get('amount', 0)):.2f}" for item in items_data])
            except Exception:
                items_list_str = "Could not parse items"
        
        cursor.close()
        conn.close()
        
        date_str = invoice[1].strftime("%Y-%m-%d") if hasattr(invoice[1], 'strftime') else str(invoice[1])
        
        return (f"📄 Invoice {invoice[0]}\n"
                f"Client: {invoice[8]} ({invoice[9] or 'N/A'})\n"
                f"Date: {date_str} | Due: {invoice[2]}\n"
                f"Status: {invoice[3]}\n"
                f"Items:\n{items_list_str}\n"
                f"Total: ₹{float(invoice[6] or 0):,.2f}")
                
    except Exception as e:
        return f"❌ Error: {str(e)}"
    """Get detailed information about a specific invoice."""
    try:
        import json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT i.invoice_number, i.created_at, i.due_date, i.status,
                   i.subtotal, i.tax_percentage, i.total_amount, i.notes,
                   c.name as client_name, c.company, i.items
            FROM invoices i
            LEFT JOIN clients c ON i.client_id = c.id
            WHERE i.invoice_number = %s;
        """, (invoice_number,))
        invoice = cursor.fetchone()
        
        if not invoice:
            cursor.close()
            conn.close()
            return f"❌ Invoice {invoice_number} not found."
        
        # Parse JSONB items
        items_data = invoice[10] # The 'items' column
        items_list_str = "No items"
        if items_data:
            try:
                if isinstance(items_data, str):
                    items_data = json.loads(items_data)
                
                if isinstance(items_data, list):
                    items_list_str = "\n".join([f"  - {item.get('description', 'Item')}: ₹{float(item.get('amount', 0)):.2f}" for item in items_data])
            except Exception:
                items_list_str = "Could not parse items"
        
        cursor.close()
        conn.close()
        
        date_str = invoice[1].strftime("%Y-%m-%d") if hasattr(invoice[1], 'strftime') else str(invoice[1])
        
        return (f"📄 Invoice {invoice[0]}\n"
                f"Client: {invoice[8]} ({invoice[9] or 'N/A'})\n"
                f"Date: {date_str} | Due: {invoice[2]}\n"
                f"Status: {invoice[3]}\n"
                f"Items:\n{items_list_str}\n"
                f"Total: ₹{float(invoice[6] or 0):,.2f}")
                
    except Exception as e:
        return f"❌ Error: {str(e)}"
    """Get detailed information about a specific invoice."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT i.invoice_number, i.created_at, i.due_date, i.status,
                   i.subtotal, i.tax_amount, i.total_amount, i.notes,
                   c.name as client_name, c.company
            FROM invoices i
            LEFT JOIN clients c ON i.client_id = c.id
            WHERE i.invoice_number = %s;
        """, (invoice_number,))
        invoice = cursor.fetchone()
        
        if not invoice:
            cursor.close()
            conn.close()
            return f"❌ Invoice {invoice_number} not found."
        
        # Get items
        cursor.execute("""
            SELECT description, quantity, rate, amount 
            FROM invoice_items 
            WHERE invoice_id = (SELECT id FROM invoices WHERE invoice_number = %s)
            ORDER BY sort_order;
        """, (invoice_number,))
        items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        items_list = "\n".join([f"  - {item[0]}: ₹{item[3]:,.2f}" for item in items])
        date_str = invoice[1].strftime("%Y-%m-%d") if hasattr(invoice[1], 'strftime') else str(invoice[1])
        
        return (f"📄 Invoice {invoice[0]}\n"
                f"Client: {invoice[8]} ({invoice[9] or 'N/A'})\n"
                f"Date: {date_str} | Due: {invoice[2]}\n"
                f"Status: {invoice[3]}\n"
                f"Items:\n{items_list}\n"
                f"Total: ₹{float(invoice[6] or 0):,.2f}")
                
    except Exception as e:
        return f"❌ Error: {str(e)}"
    """Get detailed information about a specific invoice."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT i.invoice_number, i.invoice_date, i.due_date, i.status,
                   i.subtotal, i.tax_amount, i.total_amount, i.notes,
                   c.name as client_name, c.company
            FROM invoices i
            LEFT JOIN clients c ON i.client_id = c.id
            WHERE i.invoice_number = %s;
        """, (invoice_number,))
        invoice = cursor.fetchone()
        
        if not invoice:
            cursor.close()
            conn.close()
            return f"❌ Invoice {invoice_number} not found."
        
        # Get items
        cursor.execute("""
            SELECT description, quantity, rate, amount 
            FROM invoice_items 
            WHERE invoice_id = (SELECT id FROM invoices WHERE invoice_number = %s)
            ORDER BY sort_order;
        """, (invoice_number,))
        items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        items_list = "\n".join([f"  - {item[0]}: ₹{item[3]:,.2f}" for item in items])
        
        return (f"📄 Invoice {invoice[0]}\n"
                f"Client: {invoice[8]} ({invoice[9] or 'N/A'})\n"
                f"Date: {invoice[1]} | Due: {invoice[2]}\n"
                f"Status: {invoice[3]}\n"
                f"Items:\n{items_list}\n"
                f"Total: ₹{float(invoice[6] or 0):,.2f}")
                
    except Exception as e:
        return f"❌ Error: {str(e)}"


@tool
def update_invoice(invoice_number: str, status: str = None, due_date: str = None, notes: str = None) -> str:
    """Update an existing invoice's status, due date, or notes."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if invoice exists
        cursor.execute("SELECT id FROM invoices WHERE invoice_number = %s;", (invoice_number,))
        invoice = cursor.fetchone()
        
        if not invoice:
            cursor.close()
            conn.close()
            return f"❌ Invoice {invoice_number} not found."
        
        updates = []
        params = []
        
        if status:
            updates.append("status = %s")
            params.append(status)
        if due_date:
            updates.append("due_date = %s")
            params.append(due_date)
        if notes:
            updates.append("notes = %s")
            params.append(notes)
        
        if not updates:
            cursor.close()
            conn.close()
            return f"❌ No fields to update. Provide status, due_date, or notes."
        
        params.append(invoice_number)
        query = f"UPDATE invoices SET {', '.join(updates)} WHERE invoice_number = %s;"
        cursor.execute(query, params)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        updated_fields = []
        if status: updated_fields.append(f"status='{status}'")
        if due_date: updated_fields.append(f"due_date='{due_date}'")
        if notes: updated_fields.append(f"notes='{notes}'")
        
        return f"✅ Invoice {invoice_number} updated: {', '.join(updated_fields)}"
        
    except Exception as e:
        return f"❌ Error: {str(e)}"


@tool
def delete_invoice(invoice_number: str) -> str:
    """Delete/cancel an invoice from the system."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if invoice exists
        cursor.execute("DELETE FROM invoice_items WHERE invoice_id = %s;", (invoice_id,))
        invoice = cursor.fetchone()
        
        if not invoice:
            cursor.close()
            conn.close()
            return f"❌ Invoice {invoice_number} not found."
        
        invoice_id = invoice[0]
        
        # Delete items first
        cursor.execute("DELETE FROM invoice_items WHERE invoice_id = %s;", (invoice_id,))
        # Delete payments linked to this invoice
        cursor.execute("DELETE FROM payments WHERE invoice_id = %s;", (invoice_id,))
        # Delete the invoice
        cursor.execute("DELETE FROM invoices WHERE id = %s;", (invoice_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return f"✅ Invoice {invoice_number} and all related items/payments deleted."
        
    except Exception as e:
        return f"❌ Error: {str(e)}"


@tool
def send_invoice_pdf(search_term: str) -> str:
    """Generate and send an invoice PDF to Telegram."""
    print(f"\n🔥 [DEBUG INVOICE PDF] STARTED for: '{search_term}'")
    try:
        import json
        import requests
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Search for invoice
        print(f"🔥 [DEBUG INVOICE PDF] Searching DB...")
        cursor.execute("""
            SELECT i.invoice_number, i.created_at, i.due_date, i.status,
                   i.total_amount, c.name, c.company, c.email, i.items
            FROM invoices i
            LEFT JOIN clients c ON i.client_id = c.id
            WHERE LOWER(i.invoice_number) LIKE LOWER(%s)
               OR LOWER(c.name) LIKE LOWER(%s)
            ORDER BY i.created_at DESC
            LIMIT 1;
        """, (f"%{search_term}%", f"%{search_term}%"))
        invoice = cursor.fetchone()
        
        if not invoice:
            print("❌ [DEBUG INVOICE PDF] Not found in DB")
            cursor.close()
            conn.close()
            return f"❌ No invoice found matching '{search_term}'."
            
        print(f"✅ [DEBUG INVOICE PDF] Found: {invoice[0]}")
        inv_number = invoice[0]
        
        # 2. Get detailed info
        cursor.execute("""
            SELECT i.invoice_number, i.created_at, i.due_date, i.status,
                   i.total_amount, c.name, c.company, c.email, i.items
            FROM invoices i
            LEFT JOIN clients c ON i.client_id = c.id
            WHERE i.invoice_number = %s;
        """, (inv_number,))
        inv = cursor.fetchone()
        
        # 3. Parse Items
        items_html = "<tr><td colspan='2'>No items listed</td></tr>"
        if inv[8]: 
            items_data = inv[8]
            if isinstance(items_data, str):
                try:
                    items_data = json.loads(items_data)
                except:
                    pass
            if isinstance(items_data, list):
                items_html = "".join([f"<tr><td>{item.get('description', 'Item')}</td><td>₹{float(item.get('amount', 0)):,.2f}</td></tr>" for item in items_data])
        
        # 4. Generate HTML
        date_str = inv[1].strftime("%Y-%m-%d") if hasattr(inv[1], 'strftime') else str(inv[1])
        html_content = f"""<!DOCTYPE html>
        <html><head><meta charset="UTF-8"><title>Invoice {inv[0]}</title>
        <style>body{{font-family:Arial,sans-serif;padding:40px;color:#333;}}
        h1{{color:#FF6100;}} table{{width:100%;border-collapse:collapse;margin:20px 0;}}
        th{{background:#FF6100;color:white;padding:10px;text-align:left;}}
        td{{padding:10px;border-bottom:1px solid #ddd;}}
        .total{{font-size:1.2em;font-weight:bold;color:#FF6100;}}</style></head>
        <body>
            <h1>Invoice {inv[0]}</h1>
            <p><strong>To:</strong> {inv[5]} ({inv[6] or 'N/A'})</p>
            <p><strong>Date:</strong> {date_str} | <strong>Due:</strong> {inv[2]}</p>
            <p><strong>Status:</strong> {inv[3]}</p>
            <table><thead><tr><th>Service</th><th>Amount</th></tr></thead>
            <tbody>{items_html}</tbody>
            <tfoot><tr><td class="total">Total</td><td class="total">₹ {float(inv[4] or 0):,.2f}</td></tr></tfoot></table>
        </body></html>"""
        
        # 5. Call PDFShift
        pdf_path = f"/tmp/invoice_{inv_number}.pdf"
        api_key = os.getenv("PDFSHIFT_API_KEY")
        
        if not api_key:
            print("❌ [DEBUG INVOICE PDF] PDFSHIFT_API_KEY is MISSING in .env!")
            cursor.close()
            conn.close()
            return "❌ PDFSHIFT_API_KEY is missing in .env file."
            
        print(f"🔥 [DEBUG INVOICE PDF] Calling PDFShift API...")
        response = requests.post(
            "https://api.pdfshift.io/v3/convert/pdf",
            auth=("api", api_key),
            json={"source": html_content, "landscape": False, "format": "A4"}
        )
        
        if response.status_code != 200:
            print(f"❌ [DEBUG INVOICE PDF] PDFShift Failed: {response.status_code} - {response.text}")
            cursor.close()
            conn.close()
            return f"❌ PDF generation failed: {response.text[:100]}"
            
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ [DEBUG INVOICE PDF] PDF saved to {pdf_path}")
        
        # 6. Send to Telegram
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("ADMIN_CHAT_ID")
        
        if not bot_token or not chat_id:
            print(f"❌ [DEBUG INVOICE PDF] Telegram missing: Token={bool(bot_token)}, Chat={bool(chat_id)}")
            cursor.close()
            conn.close()
            return f"✅ Invoice {inv_number} PDF saved locally. (Telegram config missing)"
            
        print(f"🔥 [DEBUG INVOICE PDF] Sending to Telegram...")
        with open(pdf_path, 'rb') as pdf_file:
            files = {'document': (f"Invoice_{inv_number}.pdf", pdf_file, 'application/pdf')}
            data = {'chat_id': chat_id, 'caption': f"📄 Invoice {inv_number}\nTotal: ₹ {float(inv[4] or 0):,.2f}"}
            tg_response = requests.post(f"https://api.telegram.org/bot{bot_token}/sendDocument", data=data, files=files)
        
        cursor.close()
        conn.close()
        
        if tg_response.status_code == 200:
            print("✅ [DEBUG INVOICE PDF] Successfully sent to Telegram!")
            return f"✅ Invoice {inv_number} PDF sent to Telegram!"
        else:
            print(f"❌ [DEBUG INVOICE PDF] Telegram send failed: {tg_response.text}")
            return f"❌ Telegram send failed: {tg_response.text[:100]}"
            
    except Exception as e:
        import traceback
        print(f"❌ [DEBUG INVOICE PDF] Exception: {str(e)}")
        traceback.print_exc()
        return f"❌ Error: {str(e)}"
    """Generate and send an invoice PDF to Telegram."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search for invoice
                # Get invoice details including JSONB items
        cursor.execute("""
            SELECT i.invoice_number, i.created_at, i.due_date, i.status,
                   i.total_amount, c.name, c.company, c.email, i.items
            FROM invoices i
            LEFT JOIN clients c ON i.client_id = c.id
            WHERE i.invoice_number = %s;
        """, (inv_number,))
        inv = cursor.fetchone()
        
        if not inv:
            cursor.close()
            conn.close()
            return f"❌ Invoice {inv_number} not found."
        
        # Parse JSONB items for HTML
        import json
        items_html = ""
        if inv[8]: # inv[8] is the 'items' column
            items_data = inv[8]
            if isinstance(items_data, str):
                items_data = json.loads(items_data)
            
            if isinstance(items_data, list):
                items_html = "".join([f"<tr><td>{item.get('description', 'Item')}</td><td>₹{float(item.get('amount', 0)):.2f}</td></tr>" for item in items_data])
        
        html_content = f"""<!DOCTYPE html>
        <html><head><meta charset="UTF-8"><title>Invoice {inv[0]}</title>
        <style>body{{font-family:Arial,sans-serif;padding:40px;color:#333;}}
        h1{{color:#FF6100;}} table{{width:100%;border-collapse:collapse;margin:20px 0;}}
        th{{background:#FF6100;color:white;padding:10px;text-align:left;}}
        td{{padding:10px;border-bottom:1px solid #ddd;}}
        .total{{font-size:1.2em;font-weight:bold;color:#FF6100;}}</style></head>
        <body>
            <h1>Invoice {inv[0]}</h1>
            <p><strong>To:</strong> {inv[5]} ({inv[6] or 'N/A'})</p>
            <p><strong>Date:</strong> {inv[1]} | <strong>Due:</strong> {inv[2]}</p>
            <p><strong>Status:</strong> {inv[3]}</p>
            <table><thead><tr><th>Service</th><th>Amount</th></tr></thead>
            <tbody>{items_html}</tbody>
            <tfoot><tr><td class="total">Total</td><td class="total">₹ {float(inv[4] or 0):,.2f}</td></tr></tfoot></table>
        </body></html>"""
        
        # Generate PDF via PDFShift
        pdf_path = f"/tmp/invoice_{inv_number}.pdf"
        api_key = os.getenv("PDFSHIFT_API_KEY")
        
        import requests
        response = requests.post(
            "https://api.pdfshift.io/v3/convert/pdf",
            auth=("api", api_key),
            json={"source": html_content, "landscape": False, "format": "A4"}
        )
        
        if response.status_code != 200:
            cursor.close()
            conn.close()
            return f"❌ PDF generation failed: {response.text}"
        
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
        
        # Send to Telegram
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("ADMIN_CHAT_ID")
        
        if bot_token and chat_id:
            with open(pdf_path, 'rb') as pdf_file:
                files = {'document': (f"Invoice_{inv_number}.pdf", pdf_file, 'application/pdf')}
                data = {'chat_id': chat_id, 'caption': f"📄 Invoice {inv_number}\nTotal: ₹ {float(inv[4] or 0):,.2f}"}
                tg_response = requests.post(f"https://api.telegram.org/bot{bot_token}/sendDocument", data=data, files=files)
            
            cursor.close()
            conn.close()
            
            if tg_response.status_code == 200:
                return f"✅ Invoice {inv_number} PDF sent to Telegram!"
            else:
                return f"❌ Telegram send failed: {tg_response.text}"
        else:
            cursor.close()
            conn.close()
            return f"✅ Invoice {inv_number} PDF saved to {pdf_path} (Telegram not configured)"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"


@tool
def get_all_invoices(status: str = None) -> str:
    """Get all invoices, optionally filtered by status (paid, unpaid, overdue)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT i.invoice_number, i.created_at, i.due_date, i.status,
                       i.total_amount, c.name as client_name
                FROM invoices i
                LEFT JOIN clients c ON i.client_id = c.id
                WHERE LOWER(i.status) = LOWER(%s)
                ORDER BY i.created_at DESC
                LIMIT 10;
            """, (status,))
        else:
            cursor.execute("""
                SELECT i.invoice_number, i.created_at, i.due_date, i.status,
                       i.total_amount, c.name as client_name
                FROM invoices i
                LEFT JOIN clients c ON i.client_id = c.id
                ORDER BY i.created_at DESC
                LIMIT 10;
            """)
        
        invoices = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not invoices:
            return f"📋 No invoices found{' with status ' + status if status else ''}."
        
        lines = [f"📋 Invoices{' (' + status + ')' if status else ''}:"]
        for inv in invoices:
            # Format date nicely if it's a datetime object
            date_str = inv[1].strftime("%Y-%m-%d") if hasattr(inv[1], 'strftime') else str(inv[1])
            lines.append(f"  • {inv[0]} | {inv[5]} | ₹{float(inv[4] or 0):,.2f} | {inv[3]}")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ Error: {str(e)}"
    """Get all invoices, optionally filtered by status (paid, unpaid, overdue)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT i.invoice_number, i.invoice_date, i.due_date, i.status,
                       i.total_amount, c.name as client_name
                FROM invoices i
                LEFT JOIN clients c ON i.client_id = c.id
                WHERE LOWER(i.status) = LOWER(%s)
                ORDER BY i.created_at DESC
                LIMIT 10;
            """, (status,))
        else:
            cursor.execute("""
                SELECT i.invoice_number, i.invoice_date, i.due_date, i.status,
                       i.total_amount, c.name as client_name
                FROM invoices i
                LEFT JOIN clients c ON i.client_id = c.id
                ORDER BY i.created_at DESC
                LIMIT 10;
            """)
        
        invoices = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not invoices:
            return f"📋 No invoices found{' with status ' + status if status else ''}."
        
        lines = [f"📋 Invoices{' (' + status + ')' if status else ''}:"]
        for inv in invoices:
            lines.append(f"  • {inv[0]} | {inv[5]} | ₹{float(inv[4] or 0):,.2f} | {inv[3]}")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

@tool
def get_client_total_invoices(client_name: str) -> str:
    """Calculate total invoice amount for a specific client."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Search for client and get all their invoices
        cursor.execute("""
            SELECT i.invoice_number, i.total_amount, i.status, i.created_at,
                   c.name as client_name, c.company
            FROM invoices i
            LEFT JOIN clients c ON i.client_id = c.id
            WHERE LOWER(c.name) LIKE LOWER(%s)
               OR LOWER(c.company) LIKE LOWER(%s)
            ORDER BY i.created_at DESC;
        """, (f"%{client_name}%", f"%{client_name}%"))
        
        invoices = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not invoices:
            return f"❌ No invoices found for client '{client_name}'."
        
        # Calculate totals
        total_amount = sum(float(inv[1] or 0) for inv in invoices)
        paid_amount = sum(float(inv[1] or 0) for inv in invoices if inv[2] == 'Paid')
        unpaid_amount = total_amount - paid_amount
        
        # Format invoice list
        invoice_list = "\n".join([
            f"  • {inv[0]} | ₹{float(inv[1] or 0):,.2f} | {inv[2]}" 
            for inv in invoices
        ])
        
        client_display = f"{invoices[0][4]} ({invoices[0][5] or 'N/A'})"
        
        return (f"📊 Invoice Summary for {client_display}:\n"
                f"{invoice_list}\n\n"
                f"💰 Total Invoiced: ₹{total_amount:,.2f}\n"
                f"✅ Paid: ₹{paid_amount:,.2f}\n"
                f"⏳ Outstanding: ₹{unpaid_amount:,.2f}")
        
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ==========================================
# TASK ASSIGNMENT & TRACKING TOOLS
# ==========================================

@tool
def create_task(title: str, project_name: str = None, assigned_to: str = None, task_cost: float = None, deadline: str = None, description: str = None, notes: str = None) -> str:
    """Create a new task and optionally assign it to a person with a budget."""
    try:
        from datetime import datetime, timedelta
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Find project_id if project_name is provided
        project_id = None
        if project_name:
            cursor.execute("""
                SELECT id FROM projects 
                WHERE LOWER(name) LIKE LOWER(%s) 
                LIMIT 1;
            """, (f"%{project_name}%",))
            project = cursor.fetchone()
            if project:
                project_id = project[0]
            else:
                cursor.close()
                conn.close()
                return f"❌ Project '{project_name}' not found. Please create the project first."
        
        # 2. Parse deadline if provided
        deadline_date = None
        if deadline:
            try:
                # Try to parse common formats
                if deadline.lower() in ['today']:
                    deadline_date = datetime.now().date()
                elif deadline.lower() in ['tomorrow']:
                    deadline_date = (datetime.now() + timedelta(days=1)).date()
                elif deadline.lower() in ['next week', 'in a week']:
                    deadline_date = (datetime.now() + timedelta(days=7)).date()
                else:
                    # Try YYYY-MM-DD format
                    deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
            except:
                cursor.close()
                conn.close()
                return f"❌ Invalid deadline format. Use YYYY-MM-DD or 'today', 'tomorrow', 'next week'."
        
        # 3. Insert task
        cursor.execute("""
            INSERT INTO tasks (project_id, title, description, status, deadline, assigned_to, task_cost, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (project_id, title, description, 'pending', deadline_date, assigned_to, task_cost, notes))
        
        task_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Build response
        response = f"✅ Task '{title}' created successfully."
        if assigned_to:
            response += f" Assigned to: {assigned_to}."
        if task_cost:
            response += f" Budget: ₹{task_cost:,.2f}."
        if deadline_date:
            response += f" Due: {deadline_date}."
        if project_name:
            response += f" Project: {project_name}."
        
        return response
        
    except Exception as e:
        return f"❌ Error creating task: {str(e)}"


@tool
def update_task(title: str, status: str = None, assigned_to: str = None, task_cost: float = None, deadline: str = None, notes: str = None) -> str:
    """Update an existing task's status, assignee, cost, deadline, or notes."""
    try:
        from datetime import datetime
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find the task
        cursor.execute("SELECT id FROM tasks WHERE LOWER(title) LIKE LOWER(%s) LIMIT 1;", (f"%{title}%",))
        task = cursor.fetchone()
        
        if not task:
            cursor.close()
            conn.close()
            return f"❌ Task '{title}' not found."
        
        task_id = task[0]
        
        # Build update query
        updates = []
        params = []
        
        if status:
            updates.append("status = %s")
            params.append(status)
        if assigned_to:
            updates.append("assigned_to = %s")
            params.append(assigned_to)
        if task_cost is not None:
            updates.append("task_cost = %s")
            params.append(task_cost)
        if deadline:
            try:
                deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
                updates.append("deadline = %s")
                params.append(deadline_date)
            except:
                cursor.close()
                conn.close()
                return f"❌ Invalid deadline format. Use YYYY-MM-DD."
        if notes:
            updates.append("notes = %s")
            params.append(notes)
        
        if not updates:
            cursor.close()
            conn.close()
            return f"❌ No fields to update. Provide status, assigned_to, task_cost, deadline, or notes."
        
        params.append(task_id)
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = %s;"
        cursor.execute(query, params)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        updated_fields = []
        if status: updated_fields.append(f"status='{status}'")
        if assigned_to: updated_fields.append(f"assigned_to='{assigned_to}'")
        if task_cost is not None: updated_fields.append(f"task_cost=₹{task_cost:,.2f}")
        if deadline: updated_fields.append(f"deadline={deadline}")
        if notes: updated_fields.append("notes updated")
        
        return f"✅ Task '{title}' updated: {', '.join(updated_fields)}"
        
    except Exception as e:
        return f"❌ Error updating task: {str(e)}"


@tool
def get_tasks(assigned_to: str = None, project_name: str = None, status: str = None, deadline_before: str = None) -> str:
    """Get tasks filtered by assignee, project, status, or deadline."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT t.title, t.status, t.deadline, t.assigned_to, t.task_cost, 
                   p.name as project_name
            FROM tasks t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE 1=1
        """
        params = []
        
        if assigned_to:
            query += " AND LOWER(t.assigned_to) LIKE LOWER(%s)"
            params.append(f"%{assigned_to}%")
        
        if project_name:
            query += " AND LOWER(p.name) LIKE LOWER(%s)"
            params.append(f"%{project_name}%")
        
        if status:
            query += " AND LOWER(t.status) = LOWER(%s)"
            params.append(status)
        
        if deadline_before:
            from datetime import datetime
            try:
                deadline_date = datetime.strptime(deadline_before, '%Y-%m-%d').date()
                query += " AND t.deadline <= %s"
                params.append(deadline_date)
            except:
                pass
        
        query += " ORDER BY t.deadline ASC NULLS LAST LIMIT 20;"
        
        cursor.execute(query, params)
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not tasks:
            return "📋 No tasks found matching your criteria."
        
        lines = ["📋 Tasks:"]
        for task in tasks:
            title, status, deadline, assigned_to, cost, project = task
            line = f"  • {title}"
            if assigned_to:
                line += f" → {assigned_to}"
            if cost:
                line += f" | ₹{float(cost):,.2f}"
            if deadline:
                line += f" | Due: {deadline}"
            line += f" | {status}"
            if project:
                line += f" | Project: {project}"
            lines.append(line)
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"❌ Error fetching tasks: {str(e)}"


@tool
def get_task_summary(project_name: str = None, assigned_to: str = None) -> str:
    """Get budget summary for a project or person."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if project_name:
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(task_cost), 0) as total_budget,
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE LOWER(p.name) LIKE LOWER(%s);
            """, (f"%{project_name}%",))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result[1] > 0:
                return f"📊 Task Summary for Project '{project_name}':\n" \
                       f"  • Total Tasks: {result[1]}\n" \
                       f"  • Completed: {result[2]}\n" \
                       f"  • Total Budget: ₹{float(result[0]):,.2f}"
            else:
                return f"❌ No tasks found for project '{project_name}'."
        
        elif assigned_to:
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(task_cost), 0) as total_budget,
                    COUNT(*) as total_tasks,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_tasks
                FROM tasks
                WHERE LOWER(assigned_to) LIKE LOWER(%s);
            """, (f"%{assigned_to}%",))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result and result[1] > 0:
                return f"📊 Task Summary for '{assigned_to}':\n" \
                       f"  • Total Tasks: {result[1]}\n" \
                       f"  • Completed: {result[2]}\n" \
                       f"  • Total Budget: ₹{float(result[0]):,.2f}"
            else:
                return f"❌ No tasks found for '{assigned_to}'."
        
        else:
            return "❌ Please provide either project_name or assigned_to."
        
    except Exception as e:
        return f"❌ Error getting task summary: {str(e)}"


@tool
def delete_task(title: str) -> str:
    """Delete a task by title."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM tasks WHERE LOWER(title) LIKE LOWER(%s) RETURNING id;", (f"%{title}%",))
        deleted = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if deleted:
            return f"✅ Task '{title}' deleted successfully."
        else:
            return f"❌ Task '{title}' not found."
        
    except Exception as e:
        return f"❌ Error deleting task: {str(e)}"


# ==========================================
# SMART TASK HANDLER (Zero-Token Static Route)
# ==========================================

def mvp_smart_task_handler(user_message: str) -> str:
    """
    SMART MVP HANDLER FOR TASKS: Analyzes user message and routes to the right function.
    Zero AI tokens for common queries.
    """
    cleaned_message = user_message.strip().strip('"').strip("'").strip()
    msg_lower = cleaned_message.lower()
    
    print(f"🔍 [MVP TASK] Original: '{user_message}' → Cleaned: '{cleaned_message}'")
    
    # ========================================
    # SCENARIO 1: SHOW MY TASKS / TODAY'S TASKS
    # ========================================
    show_keywords = ["show my tasks", "my tasks", "tasks for today", "today's tasks", "what tasks do i have"]
    
    if any(keyword in msg_lower for keyword in show_keywords):
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"🔍 [MVP TASK] SHOW TODAY MODE")
        return get_tasks.invoke({"deadline_before": today})
    
    # ========================================
    # SCENARIO 2: SHOW TASKS BY PERSON
    # ========================================
    person_keywords = ["tasks for", "tasks assigned to", "show tasks of"]
    
    if any(keyword in msg_lower for keyword in person_keywords):
        # Extract person name
        person_name = cleaned_message
        for prefix in ["tasks for", "tasks assigned to", "show tasks of", "show my tasks for"]:
            if person_name.lower().startswith(prefix):
                person_name = person_name[len(prefix):].strip()
                break
        
        person_name = person_name.strip().strip('"').strip("'").strip()
        print(f"🔍 [MVP TASK] SHOW BY PERSON MODE: '{person_name}'")
        
        if person_name:
            return get_tasks.invoke({"assigned_to": person_name})
        else:
            return "❌ Please specify whose tasks to show (e.g., 'Tasks for John')"
    
    # ========================================
    # SCENARIO 3: SHOW TASKS BY PROJECT
    # ========================================
    project_keywords = ["tasks for project", "project tasks"]
    
    if any(keyword in msg_lower for keyword in project_keywords):
        project_name = cleaned_message
        for prefix in ["tasks for project", "project tasks for", "show project tasks"]:
            if project_name.lower().startswith(prefix):
                project_name = project_name[len(prefix):].strip()
                break
        
        project_name = project_name.strip().strip('"').strip("'").strip()
        print(f"🔍 [MVP TASK] SHOW BY PROJECT MODE: '{project_name}'")
        
        if project_name:
            return get_tasks.invoke({"project_name": project_name})
        else:
            return "❌ Please specify which project (e.g., 'Tasks for project KD Companies')"
    
    # ========================================
    # SCENARIO 4: SHOW OVERDUE TASKS
    # ========================================
    overdue_keywords = ["overdue tasks", "tasks overdue", "late tasks"]
    
    if any(keyword in msg_lower for keyword in overdue_keywords):
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"🔍 [MVP TASK] SHOW OVERDUE MODE")
        return get_tasks.invoke({"deadline_before": today, "status": "pending"})
    
    # ========================================
    # SCENARIO 5: TASK SUMMARY
    # ========================================
    summary_keywords = ["task summary", "budget summary", "total budget for"]
    
    if any(keyword in msg_lower for keyword in summary_keywords):
        # Try to extract project or person name
        name = cleaned_message
        for prefix in ["task summary for", "budget summary for", "total budget for"]:
            if name.lower().startswith(prefix):
                name = name[len(prefix):].strip()
                break
        
        name = name.strip().strip('"').strip("'").strip()
        print(f"🔍 [MVP TASK] SUMMARY MODE: '{name}'")
        
        if name:
            # Try as project first, then as person
            result = get_task_summary.invoke({"project_name": name})
            if "No tasks found" in result:
                result = get_task_summary.invoke({"assigned_to": name})
            return result
        else:
            return "❌ Please specify project or person (e.g., 'Task summary for KD Companies')"
    
    # ========================================
    # SCENARIO 6: COMPLEX OPERATIONS (Let AI handle)
    # ========================================
    complex_keywords = ["create task", "assign task", "update task", "mark task", "delete task", "complete task"]
    
    if any(keyword in msg_lower for keyword in complex_keywords):
        print(f"🤖 [MVP TASK] COMPLEX MODE - Routing to AI")
        return None
    
    # ========================================
    # SCENARIO 7: UNKNOWN INTENT
    # ========================================
    return None


def mvp_smart_invoice_handler(user_message: str) -> str:
    """
    SMART MVP HANDLER FOR INVOICES: Clean input and route to the right function.
    """
    # 🧹 CLEAN THE INPUT: Remove quotes, extra spaces, and common prefixes
    cleaned_message = user_message.strip().strip('"').strip("'").strip()
    msg_lower = cleaned_message.lower()
    
    print(f"🔍 [MVP INVOICE] Original: '{user_message}' → Cleaned: '{cleaned_message}'")
    
    # ========================================
    # SCENARIO 1: SEND INVOICE PDF
    # ========================================
    send_keywords = ["send invoice", "send pdf", "get invoice pdf", "send me the invoice", "send the pdf of invoice"]
    
    if any(keyword in msg_lower for keyword in send_keywords):
        # Extract search term intelligently
        search_term = cleaned_message
        
        # Remove common prefixes
        for prefix in ["send invoice", "send the invoice", "send pdf of invoice", 
                       "send the pdf of invoice", "send me the invoice", "get invoice pdf"]:
            if search_term.lower().startswith(prefix):
                search_term = search_term[len(prefix):].strip()
                break
        
        # Remove "for" if present
        if search_term.lower().startswith("for"):
            search_term = search_term[3:].strip()
        
        # Final cleanup: remove any remaining quotes, extra spaces
        search_term = search_term.strip().strip('"').strip("'").strip()
        
        print(f"🔍 [MVP INVOICE] SEND MODE - Final search term: '{search_term}'")
        
        if not search_term:
            return "❌ Please specify which invoice to send (e.g., 'Send invoice INV-001')"
        
        return send_invoice_pdf.invoke({"search_term": search_term})
    
    # ========================================
    # SCENARIO 2: SHOW INVOICE DETAILS
    # ========================================
    show_keywords = ["show invoice", "get invoice", "view invoice", "display invoice"]
    
    if any(keyword in msg_lower for keyword in show_keywords):
        search_term = cleaned_message
        
        for prefix in ["show invoice", "get invoice", "view invoice", "display invoice"]:
            if search_term.lower().startswith(prefix):
                search_term = search_term[len(prefix):].strip()
                break
        
        search_term = search_term.strip().strip('"').strip("'").strip()
        
        print(f"🔍 [MVP INVOICE] SHOW MODE - Final search term: '{search_term}'")
        
        if not search_term:
            return "❌ Please specify which invoice to show (e.g., 'Show invoice INV-001')"
        
        return get_invoice_details.invoke({"invoice_number": search_term})
    
    # ========================================
    # SCENARIO 3: LIST ALL INVOICES
    # ========================================
    list_keywords = ["list invoices", "show all invoices", "get invoices", "list all invoices", "show invoices"]
    
    if any(keyword in msg_lower for keyword in list_keywords):
        status = None
        if "paid" in msg_lower:
            status = "paid"
        elif "unpaid" in msg_lower:
            status = "unpaid"
        elif "overdue" in msg_lower:
            status = "overdue"
        
        print(f"🔍 [MVP INVOICE] LIST MODE - Status filter: {status}")
        
        if status:
            return get_all_invoices.invoke({"status": status})
        else:
            return get_all_invoices.invoke({})


    # ========================================
    # SCENARIO 3.5: TOTAL INVOICES FOR CLIENT
    # ========================================
    
    total_keywords = ["total invoice", "total amount", "invoice total", "sum of invoices", "all invoices for"]
    
    if any(keyword in msg_lower for keyword in total_keywords):
        # 🧹 SMART EXTRACTION: Get client name from natural language
        client_name = cleaned_message
        
        # Step 1: If "for" exists, take everything after it
        if " for " in client_name.lower():
            parts = client_name.split(" for ", 1)
            client_name = parts[1].strip()
        
        # Step 2: Remove common question prefixes
        question_prefixes = [
            "what is the", "what's the", "how much is the", "show me the",
            "get the", "tell me the", "calculate the", "find the"
        ]
        for prefix in question_prefixes:
            if client_name.lower().startswith(prefix):
                client_name = client_name[len(prefix):].strip()
                break
        
        # Step 3: Remove "total invoice/amount" if still present
        if client_name.lower().startswith("total invoice"):
            client_name = client_name[13:].strip()
        elif client_name.lower().startswith("total amount"):
            client_name = client_name[12:].strip()
        elif client_name.lower().startswith("invoice total"):
            client_name = client_name[13:].strip()
        
        # Step 4: Remove "for" if still at the start
        if client_name.lower().startswith("for "):
            client_name = client_name[4:].strip()
        
        # Step 5: Remove "client" if present
        if client_name.lower().startswith("client "):
            client_name = client_name[7:].strip()
        
        # Step 6: Remove question marks and final cleanup
        client_name = client_name.replace("?", "").strip().strip('"').strip("'").strip()
        
        print(f"🔍 [MVP INVOICE] TOTAL MODE - Extracted client: '{client_name}'")
        
        if not client_name:
            return "❌ Please specify which client (e.g., 'Total invoice for Arshad')"
        
        return get_client_total_invoices.invoke({"client_name": client_name})
    # ========================================
    # SCENARIO 4: COMPLEX OPERATIONS (Let AI handle)
    # ========================================
    complex_keywords = ["create invoice", "make invoice", "new invoice", "update invoice", 
                        "delete invoice", "mark as", "record payment"]
    
    if any(keyword in msg_lower for keyword in complex_keywords):
        print(f"🤖 [MVP INVOICE] COMPLEX MODE - Routing to AI")
        return None
    
    # ========================================
    # SCENARIO 5: UNKNOWN INTENT
    # ========================================
    return None
    """
    SMART MVP HANDLER FOR INVOICES: Analyzes user message and automatically:
    - If it's a SEND request: searches flexibly and sends PDF
    - If it's a SHOW request: displays invoice details
    - If it's a LIST request: shows all invoices
    - If it's a CREATE/UPDATE/DELETE: returns None (let AI handle it)
    
    No LLM, 100% deterministic, handles any input format.
    """
    import json
    msg_lower = user_message.lower()
    
    # ========================================
    # SCENARIO 1: SEND INVOICE PDF
    # ========================================
    send_keywords = ["send invoice", "send pdf", "get invoice pdf", "send me the invoice"]
    
    if any(keyword in msg_lower for keyword in send_keywords):
        # Extract search term
        search_term = user_message
        if "for" in msg_lower:
            search_term = user_message.split("for", 1)[1].strip()
        elif "invoice" in msg_lower:
            search_term = user_message.replace("Send invoice", "").replace("Send the invoice", "").strip()
        
        print(f"🔍 [MVP INVOICE] SEND MODE - Searching for: '{search_term}'")
        
        # Call the PDF sender
        return send_invoice_pdf.invoke({"search_term": search_term})
    
    # ========================================
    # SCENARIO 2: SHOW INVOICE DETAILS
    # ========================================
    show_keywords = ["show invoice", "get invoice", "view invoice", "display invoice"]
    
    if any(keyword in msg_lower for keyword in show_keywords):
        # Extract invoice number
        search_term = user_message
        if "invoice" in msg_lower:
            search_term = user_message.replace("Show invoice", "").replace("Get invoice", "").replace("View invoice", "").strip()
        
        print(f"🔍 [MVP INVOICE] SHOW MODE - Searching for: '{search_term}'")
        
        # Call the details getter
        return get_invoice_details.invoke({"invoice_number": search_term})
    
    # ========================================
    # SCENARIO 3: LIST ALL INVOICES
    # ========================================
    list_keywords = ["list invoices", "show all invoices", "get invoices", "list all invoices"]
    
    if any(keyword in msg_lower for keyword in list_keywords):
        # Check if filtering by status
        status = None
        if "paid" in msg_lower:
            status = "paid"
        elif "unpaid" in msg_lower:
            status = "unpaid"
        elif "overdue" in msg_lower:
            status = "overdue"
        
        print(f"🔍 [MVP INVOICE] LIST MODE - Status filter: {status}")
        
        # Call the list function
        if status:
            return get_all_invoices.invoke({"status": status})
        else:
            return get_all_invoices.invoke({})
    
    # ========================================
    # SCENARIO 4: COMPLEX OPERATIONS (Let AI handle)
    # ========================================
    # If it's a create, update, delete, or multi-step operation, return None
    complex_keywords = ["create invoice", "make invoice", "new invoice", "update invoice", "delete invoice", "mark as", "record payment"]
    
    if any(keyword in msg_lower for keyword in complex_keywords):
        print(f"🤖 [MVP INVOICE] COMPLEX MODE - Routing to AI")
        return None
    
    # ========================================
    # SCENARIO 5: UNKNOWN INTENT
    # ========================================
    return None

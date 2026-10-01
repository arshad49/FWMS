from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from models import ProjectCreate, ProjectUpdate, ProjectResponse
import uuid
from urllib.parse import quote
from datetime import datetime
from google_calendar import create_event, delete_event

router = APIRouter()

# 1. GET all projects (with Client Name)
@router.get("/", response_model=list[ProjectResponse])
def get_projects(db = Depends(get_db)):
    cursor = db.cursor()
    # We JOIN the clients table to get the client's name
    query = """
        SELECT p.*, c.name as client_name 
        FROM projects p 
        LEFT JOIN clients c ON p.client_id = c.id 
        ORDER BY p.created_at DESC;
    """
    cursor.execute(query)
    projects = cursor.fetchall()
    cursor.close()
    return projects

# 2. POST (Create) a new project
@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(project: ProjectCreate, db = Depends(get_db)):
    cursor = db.cursor()
    query = """
        INSERT INTO projects (client_id, name, start_date, deadline, total_cost, status, assigned_name, assigned_percentage, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
    """
    # FIX: Convert UUID to string using str()
    cursor.execute(query, (
        str(project.client_id), 
        project.name, 
        project.start_date, 
        project.deadline, 
        project.total_cost, 
        project.status, 
        project.assigned_name, 
        project.assigned_percentage, 
        project.notes
    ))
    new_project = cursor.fetchone()
    db.commit()
    cursor.close()
    
    # Fetch the client name for the response
    cursor = db.cursor()
    cursor.execute("SELECT name FROM clients WHERE id = %s;", (str(project.client_id),))
    client = cursor.fetchone()
    cursor.close()
    
    new_project['client_name'] = client['name'] if client else None
    return new_project

# 3. DELETE a project
@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM projects WHERE id = %s;", (project_id,))
    db.commit()
    cursor.close()
    return {"message": "Project deleted"}

@router.get("/{project_id}/details")
def get_project_details(project_id: str, db = Depends(get_db)):
    cursor = db.cursor()
    
    # 1. Get Project Info
    cursor.execute("SELECT * FROM projects WHERE id = %s;", (project_id,))
    project = cursor.fetchone()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # 2. Get Client Name for the project
    cursor.execute("SELECT name FROM clients WHERE id = %s;", (str(project['client_id']),))
    client = cursor.fetchone()
    project['client_name'] = client['name'] if client else 'Unknown Client'
    
    # 3. Get All Tasks for this project
    cursor.execute("""
        SELECT * FROM tasks 
        WHERE project_id = %s 
        ORDER BY deadline ASC;
    """, (project_id,))
    tasks = cursor.fetchall()
    
    # 4. Calculate Total Task Costa
    total_task_cost = sum(float(t['task_cost'] or 0) for t in tasks)
    
    cursor.close()
    
    return {
        "project": project,
        "tasks": tasks,
        "total_task_cost": total_task_cost
    }

from pydantic import BaseModel
from typing import Optional
from fastapi import HTTPException

# 1. Define the schema for updates
class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    deadline: Optional[str] = None
    total_cost: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

# 2. Add the PUT endpoint

from pydantic import BaseModel
from typing import Optional
from fastapi import HTTPException

# 1. Define the schema for updates
class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    deadline: Optional[str] = None
    total_cost: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

# 2. The clean PUT endpoint (No calendar imports)
@router.put("/{project_id}")

@router.put("/{project_id}")
def update_project(project_id: str, updates: ProjectUpdate, db = Depends(get_db)):
    cursor = db.cursor()
    
    try:
        # Get current state to check for changes
        cursor.execute("SELECT deadline, status, google_event_id, client_id FROM projects WHERE id = %s;", (project_id,))
        current_project = cursor.fetchone()
    except Exception as e:
        cursor.close()
        raise HTTPException(status_code=500, detail=f"Database error: Please ensure 'google_event_id' column exists in projects table. ({str(e)})")
    
    if not current_project:
        raise HTTPException(status_code=404, detail="Project not found")

    fields_to_update = []
    values = []
    
    if updates.name is not None: fields_to_update.append("name = %s"); values.append(updates.name)
    if updates.deadline is not None: fields_to_update.append("deadline = %s"); values.append(updates.deadline)
    if updates.total_cost is not None: fields_to_update.append("total_cost = %s"); values.append(updates.total_cost)
    if updates.status is not None: fields_to_update.append("status = %s"); values.append(updates.status)
    if updates.notes is not None: fields_to_update.append("notes = %s"); values.append(updates.notes)

    if not fields_to_update:
        raise HTTPException(status_code=400, detail="No valid fields provided")

    values.append(project_id)
    query = f"UPDATE projects SET {', '.join(fields_to_update)} WHERE id = %s RETURNING *;"
    
    try:
        cursor.execute(query, tuple(values))
        updated_project = cursor.fetchone()
        
        # 🤖 AUTOMATIC CALENDAR LOGIC (Wrapped in try-except so it doesn't break the save)
        try:
            # 1. If marked Completed, DELETE the calendar event
            if updates.status == 'Completed' and current_project.get('google_event_id'):
                delete_event(current_project['google_event_id'])
                cursor.execute("UPDATE projects SET google_event_id = NULL WHERE id = %s;", (project_id,))

            # 2. If a new deadline is set/changed, CREATE a new calendar event
            elif updates.deadline and updates.deadline != current_project.get('deadline'):
                if current_project.get('google_event_id'):
                    delete_event(current_project['google_event_id']) # Clean up old event
                
                cursor.execute("SELECT name FROM clients WHERE id = %s;", (str(current_project['client_id']),))
                client = cursor.fetchone()
                client_name = client['name'] if client else 'Unknown'
                
                event_id = create_event(updated_project['name'], client_name, updates.deadline, project_id)
                cursor.execute("UPDATE projects SET google_event_id = %s WHERE id = %s;", (event_id, project_id))
        except Exception as cal_error:
            # If calendar fails, we still want the project to save! Just log it.
            print(f"Calendar sync warning: {cal_error}")

        db.commit()
        cursor.close()
        return {"message": "Project updated successfully"}
        
    except Exception as e:
        db.rollback()
        cursor.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}/calendar-link")
def get_google_calendar_link(project_id: str, db = Depends(get_db)):
    cursor = db.cursor()
    
    # Get project details
    cursor.execute("""
        SELECT p.*, c.name as client_name 
        FROM projects p 
        JOIN clients c ON p.client_id = c.id 
        WHERE p.id = %s;
    """, (project_id,))
    project = cursor.fetchone()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    cursor.close()
    
    # Format dates for Google Calendar (YYYYMMDDTHHMMSS format)
    deadline = project['deadline']
    if isinstance(deadline, str):
        deadline_dt = datetime.strptime(deadline, '%Y-%m-%d')
    else:
        deadline_dt = deadline
    
    # Event end time (1 hour after deadline)
    end_dt = deadline_dt.replace(hour=deadline_dt.hour + 1)
    
    start_str = deadline_dt.strftime('%Y%m%dT090000')  # 9 AM on deadline date
    end_str = end_dt.strftime('%Y%m%dT100000')  # 10 AM on deadline date
    
    # Event details
    title = f"📅 Project Deadline: {project['name']}"
    description = f"""
Project: {project['name']}
Client: {project['client_name']}
Status: {project['status']}
Budget: ₹{project['total_cost']:,.0f}

Notes:
{project['notes'] or 'No additional notes'}
    """.strip()
    
    # Google Calendar reminders (in minutes before event)
    # 1 week = 10080 minutes, 3 days = 4320, 2 days = 2880, 1 day = 1440
    reminders = [
        ("email", 10080),   # 1 week before - email
        ("popup", 4320),    # 3 days before - popup
        ("popup", 2880),    # 2 days before - popup
        ("popup", 1440),    # 1 day before - popup
        ("popup", 60),      # 1 hour before - popup
    ]
    
    # Build reminders string
    reminders_str = "&".join([f"reminders=type:{r[0]},minutes:{r[1]}" for r in reminders])
    
    # Build Google Calendar URL
    base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
    calendar_url = f"""{base_url}
&text={quote(title)}
&dates={start_str}/{end_str}
&details={quote(description)}
&location=Freelancer%20CRM
&{reminders_str}
""".replace('\n', '')
    
    return {"calendar_url": calendar_url, "project_name": project['name']}
from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_db
from models import TaskCreate, TaskUpdate, TaskResponse
import uuid

router = APIRouter()

# 1. GET tasks (optionally filtered by project_id)
@router.get("/", response_model=list[TaskResponse])
def get_tasks(project_id: str = Query(None), db = Depends(get_db)):
    cursor = db.cursor()
    
    if project_id:
        query = """
            SELECT t.*, p.name as project_name 
            FROM tasks t 
            LEFT JOIN projects p ON t.project_id = p.id 
            WHERE t.project_id = %s
            ORDER BY t.created_at DESC;
        """
        cursor.execute(query, (project_id,))
    else:
        query = """
            SELECT t.*, p.name as project_name 
            FROM tasks t 
            LEFT JOIN projects p ON t.project_id = p.id 
            ORDER BY t.created_at DESC;
        """
        cursor.execute(query)
        
    tasks = cursor.fetchall()
    cursor.close()
    return tasks

# 2. POST (Create) a new task
# Update the POST route (create_task function):
@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, db = Depends(get_db)):
    cursor = db.cursor()
    query = """
        INSERT INTO tasks (project_id, title, description, status, deadline, assigned_to, task_cost, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
    """
    cursor.execute(query, (
        str(task.project_id), 
        task.title, 
        task.description, 
        task.status, 
        task.deadline,
        task.assigned_to,
        task.task_cost,
        task.notes
    ))
    new_task = cursor.fetchone()
    db.commit()
    cursor.close()
    
    # Fetch project name for response
    cursor = db.cursor()
    cursor.execute("SELECT name FROM projects WHERE id = %s;", (str(task.project_id),))
    project = cursor.fetchone()
    cursor.close()
    
    new_task['project_name'] = project['name'] if project else None
    return new_task

# Update the PUT route (update_task function):
@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task: TaskUpdate, db = Depends(get_db)):
    cursor = db.cursor()
    
    update_fields = []
    values = []
    if task.title is not None:
        update_fields.append("title = %s"); values.append(task.title)
    if task.description is not None:
        update_fields.append("description = %s"); values.append(task.description)
    if task.status is not None:
        update_fields.append("status = %s"); values.append(task.status)
    if task.deadline is not None:
        update_fields.append("deadline = %s"); values.append(task.deadline)
    if task.assigned_to is not None:
        update_fields.append("assigned_to = %s"); values.append(task.assigned_to)
    if task.task_cost is not None:
        update_fields.append("task_cost = %s"); values.append(task.task_cost)
    if task.notes is not None:
        update_fields.append("notes = %s"); values.append(task.notes)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(task_id)
    query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = %s RETURNING *;"
    
    cursor.execute(query, tuple(values))
    updated_task = cursor.fetchone()
    db.commit()
    cursor.close()

    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task
# 3. PUT (Update) task status/details
@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task: TaskUpdate, db = Depends(get_db)):
    cursor = db.cursor()
    
    update_fields = []
    values = []
    if task.title is not None:
        update_fields.append("title = %s"); values.append(task.title)
    if task.description is not None:
        update_fields.append("description = %s"); values.append(task.description)
    if task.status is not None:
        update_fields.append("status = %s"); values.append(task.status)
    if task.deadline is not None:
        update_fields.append("deadline = %s"); values.append(task.deadline)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(task_id)
    query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = %s RETURNING *;"
    
    cursor.execute(query, tuple(values))
    updated_task = cursor.fetchone()
    db.commit()
    cursor.close()

    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task

# 4. DELETE a task
@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str, db = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
    db.commit()
    cursor.close()
    return {"message": "Task deleted"}
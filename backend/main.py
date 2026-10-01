from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime

from openai import OpenAI

# Database and Routers
from database import get_db
from routers import clients, projects, tasks, quotes, invoices, payments, dashboard, notifications
from google_calendar import get_auth_url, save_token

# Import ALL CRM tools
from crm_tools import (
    get_all_clients, get_client_balance, get_all_projects, get_dashboard_summary, 
    mark_project_complete, get_client_details, get_invoices, 
    create_client, create_project, record_payment, create_invoice, add_deadline_to_calendar,
    create_quote, generate_quote_pdf, get_quotes, fetch_and_send_quote_pdf, mvp_smart_quote_handler,
    get_invoice_details, update_invoice, delete_invoice, send_invoice_pdf, get_all_invoices,
    create_task, update_task, get_tasks, get_task_summary, delete_task, mvp_smart_task_handler,convert_quote_to_project,get_db_connection
)

load_dotenv()

# ==========================================
# 1. Initialize the App & CORS
# ==========================================
app = FastAPI(title="Freelancer CRM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 2. OpenRouter Setup (Bulletproof AI)
# ==========================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if OPENROUTER_API_KEY:
    print(f"🔑 OPENROUTER API KEY LOADED: {OPENROUTER_API_KEY[:10]}...")
    ai_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    print("✅ AI Client initialized (Gemini via OpenRouter)")
else:
    print("❌ CRITICAL: OPENROUTER_API_KEY missing in .env!")
    ai_client = None

# ==========================================
# 3. Conversation Memory
# ==========================================
conversation_history = defaultdict(list)
MAX_HISTORY = 5

def add_to_history(user_id: str, role: str, content: str):
    conversation_history[user_id].append({"role": role, "content": content})
    if len(conversation_history[user_id]) > MAX_HISTORY:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY:]

def get_history(user_id: str) -> str:
    history = conversation_history.get(user_id, [])
    if not history:
        return ""
    return "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])

# ==========================================
# 4. Define Tools for AI Function Calling
# ==========================================
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_client",
            "description": "Create a new client in the CRM database",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the client"},
                    "company": {"type": "string", "description": "Company name (optional)"},
                    "email": {"type": "string", "description": "Email address (optional)"},
                    "phone": {"type": "string", "description": "Phone number (optional)"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_quote",
            "description": "Create a new quotation for a client",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string", "description": "Name of the client"},
                    "quote_number": {"type": "string", "description": "Quote number (e.g., Q-001)"},
                    "to_name": {"type": "string", "description": "Recipient name"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "amount": {"type": "number"}
                            },
                            "required": ["description", "amount"]
                        },
                        "description": "List of services/items with amounts"
                    }
                },
                "required": ["client_name", "quote_number", "to_name", "items"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_and_send_quote_pdf",
            "description": "Fetch a quotation by search term and send the PDF to Telegram",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {"type": "string", "description": "Client name, quote number, or company to search for"}
                },
                "required": ["search_term"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_client_balance",
            "description": "Get the outstanding balance for a client",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string", "description": "Name of the client"}
                },
                "required": ["client_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_projects",
            "description": "List all projects with their status",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_project",
            "description": "Create a new project. Auto-creates client if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string", "description": "Client name (auto-created if doesn't exist)"},
                    "project_name": {"type": "string", "description": "Project name"},
                    "total_cost": {"type": "number", "description": "Total project cost (optional, defaults to 0)"},
                    "deadline": {"type": "string", "description": "Deadline (YYYY-MM-DD or 'in 30 days', 'in 2 weeks')"}
                },
                "required": ["client_name", "project_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_invoice_details",
            "description": "Get detailed information about a specific invoice",
            "parameters": {
                "type": "object",
                "properties": {
                    "invoice_number": {"type": "string", "description": "Invoice number to look up"}
                },
                "required": ["invoice_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_invoice",
            "description": "Update an invoice status, due date, or notes",
            "parameters": {
                "type": "object",
                "properties": {
                    "invoice_number": {"type": "string", "description": "Invoice number to update"},
                    "status": {"type": "string", "description": "New status (paid, unpaid, overdue, cancelled)"},
                    "due_date": {"type": "string", "description": "New due date (YYYY-MM-DD)"},
                    "notes": {"type": "string", "description": "Notes to add"}
                },
                "required": ["invoice_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_invoice",
            "description": "Delete or cancel an invoice",
            "parameters": {
                "type": "object",
                "properties": {
                    "invoice_number": {"type": "string", "description": "Invoice number to delete"}
                },
                "required": ["invoice_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_invoice_pdf",
            "description": "Generate and send an invoice PDF to Telegram",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_term": {"type": "string", "description": "Invoice number or client name to search"}
                },
                "required": ["search_term"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_invoices",
            "description": "List all invoices, optionally filtered by status",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status: paid, unpaid, overdue (optional)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "record_payment",
            "description": "Record a payment received from a client",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string", "description": "Name of the client"},
                    "amount": {"type": "number", "description": "Payment amount"},
                    "payment_method": {"type": "string", "description": "Payment method (bank transfer, cash, UPI)"},
                    "invoice_number": {"type": "string", "description": "Invoice number (optional)"}
                },
                "required": ["client_name", "amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_invoice",
            "description": "Create a new invoice for a client with line items",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_name": {"type": "string", "description": "Name of the client"},
                    "invoice_number": {"type": "string", "description": "Invoice number (e.g., INV-001)"},
                    "items": {
                        "type": "array",
                        "description": "List of services/items with description and amount",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string", "description": "Service description"},
                                "amount": {"type": "number", "description": "Amount for this item"}
                            },
                            "required": ["description", "amount"]
                        }
                    },
                    "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format (optional)"}
                },
                "required": ["client_name", "invoice_number", "items"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new task and optionally assign it to a person with a budget",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "project_name": {"type": "string", "description": "Project name (optional)"},
                    "assigned_to": {"type": "string", "description": "Person's name to assign task to"},
                    "task_cost": {"type": "number", "description": "Budget/amount for the task"},
                    "deadline": {"type": "string", "description": "Due date (YYYY-MM-DD or 'today', 'tomorrow', 'next week')"},
                    "description": {"type": "string", "description": "Task description (optional)"},
                    "notes": {"type": "string", "description": "Additional notes (optional)"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update an existing task's status, assignee, cost, deadline, or notes",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title to update"},
                    "status": {"type": "string", "description": "New status (pending, in_progress, completed)"},
                    "assigned_to": {"type": "string", "description": "New assignee"},
                    "task_cost": {"type": "number", "description": "New budget"},
                    "deadline": {"type": "string", "description": "New deadline (YYYY-MM-DD)"},
                    "notes": {"type": "string", "description": "New notes"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_tasks",
            "description": "Get tasks filtered by assignee, project, status, or deadline",
            "parameters": {
                "type": "object",
                "properties": {
                    "assigned_to": {"type": "string", "description": "Filter by assignee"},
                    "project_name": {"type": "string", "description": "Filter by project"},
                    "status": {"type": "string", "description": "Filter by status"},
                    "deadline_before": {"type": "string", "description": "Show tasks due before this date (YYYY-MM-DD)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_task_summary",
            "description": "Get budget summary for a project or person",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Project name"},
                    "assigned_to": {"type": "string", "description": "Person's name"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task by title",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title to delete"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convert_quote_to_project",
            "description": "Convert an accepted quotation into a project. Auto-updates quote status to 'Accepted'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "quote_number": {"type": "string", "description": "Quote number to convert (e.g., Q-001)"}
                },
                "required": ["quote_number"]
            }
        }
    }

]
# Tool mapping to actual Python functions
tool_map = {
    "create_client": create_client,
    "create_quote": create_quote,
    "fetch_and_send_quote_pdf": fetch_and_send_quote_pdf,
    "get_client_balance": get_client_balance,
    "get_all_projects": get_all_projects,
    "create_invoice": create_invoice,
    "get_invoice_details": get_invoice_details,
    "update_invoice": update_invoice,
    "delete_invoice": delete_invoice,
    "send_invoice_pdf": send_invoice_pdf,
    "get_all_invoices": get_all_invoices,
    "record_payment": record_payment,
    "get_invoices": get_invoices,
    "create_task": create_task,
    "update_task": update_task,
    "get_tasks": get_tasks,
    "get_task_summary": get_task_summary,
    "delete_task": delete_task,
    "convert_quote_to_project": convert_quote_to_project,
}

# ==========================================
# 5. Basic & Test Routes
# ==========================================
@app.get("/")
def read_root():
    return {"message": "Welcome to Freelancer CRM API!"}

@app.get("/api/calendar/connect")
def connect_calendar():
    return {"auth_url": get_auth_url()}

@app.get("/api/calendar/callback")
def calendar_callback(request: Request):
    code = request.query_params.get("code")
    if code:
        save_token(code)
        return RedirectResponse(url="http://localhost:5173/settings?calendar_connected=true")
    return {"error": "Failed to connect"}

@app.get("/api/ai-test")
def test_ai_connection():
    try:
        if not ai_client:
            return {"status": "error", "message": "OpenRouter API key not configured"}
        completion = ai_client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=[{"role": "user", "content": "Reply with exactly: '✅ AI is connected and ready!'"}],
            max_tokens=50
        )
                # DEBUG: Token usage tracking
        if hasattr(completion, 'usage') and completion.usage:
            print(f"📊 TOKEN USAGE:")
            print(f"   Input tokens: {completion.usage.prompt_tokens}")
            print(f"   Output tokens: {completion.usage.completion_tokens}")
            print(f"   Total tokens: {completion.usage.total_tokens}")

        return {"status": "success", "ai_response": completion.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/api/test-db")
def test_database(db = Depends(get_db)):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT version();")
        result = cursor.fetchone()
        cursor.close()
        return {"status": "success", "message": "Connected to Supabase!", "db_version": result['version']}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==========================================
# 6. AI AGENT CHAT ENDPOINT (Hybrid Router)
# ==========================================
class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"

@app.post("/api/chat")
def unified_crm_assistant(request: ChatRequest):
    print(f"\n{'='*60}")
    print(f"📨 USER MESSAGE: {request.message}")
    print(f"👤 USER ID: {request.user_id}")
    print(f"{'='*60}")
    
    msg_lower = request.message.lower()
    user_id = request.user_id
    
    # LANE 1: Simple Quote Fetch (Zero AI)
    simple_fetch_keywords = ["send quote", "fetch quote", "get pdf", "send me the quote", "send the quote", "pdf for"]
    is_simple_fetch = any(kw in msg_lower for kw in simple_fetch_keywords)
    is_complex = any(kw in msg_lower for kw in ["create", "make", "add", "new", "and"])
    
    if is_simple_fetch and not is_complex:
        print("🚀 [ROUTE] Simple quote fetch → Static Handler")
        from crm_tools import mvp_smart_quote_handler
        result = mvp_smart_quote_handler(request.message)
        return {"status": "success", "response": result}
    
    # Check for invoice operations
    from crm_tools import mvp_smart_invoice_handler
    invoice_result = mvp_smart_invoice_handler(request.message)
    
    if invoice_result is not None:
        print("🚀 [ROUTE] Simple invoice operation → Static Handler")
        return {"status": "success", "response": invoice_result}

     # Check for task operations
    from crm_tools import mvp_smart_task_handler
    task_result = mvp_smart_task_handler(request.message)
    
    if task_result is not None:
        print("🚀 [ROUTE] Simple task operation → Static Handler")
        return {"status": "success", "response": task_result}
    
    # LANE 2: AI with Tool Calling (Complex operations)
    print("🤖 [ROUTE] Complex/Contextual → AI with Tools")
    
        # Check if this is a simple text query (no tools needed)
    simple_keywords = ["hi", "hello", "thanks", "help", "what can you do"]
    is_simple_query = any(kw in msg_lower for kw in simple_keywords)
    
    if is_simple_query and not any(tool in msg_lower for tool in ["create", "send", "show", "list", "mark", "record"]):
        # Use cheaper model for simple queries
        print("💡 [ROUTE] Simple query → Using lightweight model")
        try:
            completion = ai_client.chat.completions.create(
                model="google/gemini-flash-1.5",  # Cheaper model
                messages=[{"role": "user", "content": request.message}],
                max_tokens=100,
                temperature=0.7
            )
            response_text = completion.choices[0].message.content.strip()
            return {"status": "success", "response": response_text}
        except Exception as e:
            print(f"❌ Lightweight model error: {e}")
            # Fall back to full model if lightweight fails
    
    # LANE 2: AI with Tool Calling
    print("🤖 [ROUTE] Complex/Contextual → AI with Tools")
    
    if not ai_client:
        return {"status": "error", "response": "AI not configured. Check OPENROUTER_API_KEY."}
    
    # Add to history
    add_to_history(user_id, "User", request.message)
    history = get_history(user_id)
    
    system_prompt = f"""CRM assistant. Execute ALL requested tools in ONE response.

CRITICAL RULES:
1. If user asks for MULTIPLE actions, you MUST call ALL tools in a SINGLE response.
2. Even if a tool returns "already exists", you MUST continue with the remaining tools.
3. NEVER stop after one tool call if multiple were requested.
4. Format currency as ₹XX,XXX.
5. Simple requests (send/show/list) are handled by the system automatically.

🚫 PDF GENERATION RULES:
6. NEVER call fetch_and_send_quote_pdf or send_invoice_pdf in the same response as create_quote or create_invoice.
7. After creating a quote/invoice, you MUST ONLY say: "✅ Quotation [Number] created for [Client]. Total: ₹[Amount]. Would you like me to generate and send the PDF for this?"
8. ONLY call the PDF tool if the user replies "yes" in a NEW message.

🎯 PROJECT CREATION RULES (PROACTIVE):
9. The `create_project` tool auto-creates the client if needed. You don't need to call create_client separately.
10. `total_cost` is OPTIONAL - if user doesn't specify a project budget, use 0 or omit it.
11. Always call create_project when user asks to create a project, even if you think the client might not exist.

🎯 PROJECT CREATION RULES:

TYPE 1 - QUOTE-CONVERTED PROJECTS:
When user says "Accept quote Q-001" or "Convert quote Q-001 to project":
→ Call: convert_quote_to_project(quote_number="Q-001")
→ This automatically creates the project from quote data and marks quote as 'Accepted'

TYPE 2 - MANUAL PROJECTS:
When user says "Create project X for client Y":
→ Call: create_project(client_name="Y", project_name="X", total_cost=0)

PROJECT EXAMPLES:
User: "Accept quote Q-001 and create project"
You: Call convert_quote_to_project(quote_number="Q-001")

User: "Convert quote Q-KD-005 to project"
You: Call convert_quote_to_project(quote_number="Q-KD-005")

User: "Create project 'Logo Design' for TechCorp"
You: Call create_project(client_name="TechCorp", project_name="Logo Design")
MANDATORY WORKFLOW:
User: "Create quote Q-001 for KD Companies with Web Design 15000"
You call: create_client + create_quote
You reply EXACTLY: "✅ Quotation Q-001 created for KD Companies. Total: ₹15,000. Would you like me to generate and send the PDF for this?"
You STOP.

User: "Yes"
You call: fetch_and_send_quote_pdf(search_term="Q-001")
🎯 PROJECT CREATION RULES:

TYPE 1 - QUOTE-CONVERTED PROJECTS:
When user says "Accept quote Q-001" or "Convert quote Q-001 to project":
→ Call: convert_quote_to_project(quote_number="Q-001")
→ This automatically creates the project from quote data and marks quote as 'Accepted'

TYPE 2 - MANUAL PROJECTS:
When user says "Create project X for client Y":
→ Call: create_project(client_name="Y", project_name="X", total_cost=0)
→ total_cost is optional (defaults to 0)

PROJECT EXAMPLES:
User: "Accept quote Q-001 and create project"
You: Call convert_quote_to_project(quote_number="Q-001")

User: "Convert quote Q-KD-005 to project"
You: Call convert_quote_to_project(quote_number="Q-KD-005")

User: "Create project 'Logo Design' for TechCorp"
You: Call create_project(client_name="TechCorp", project_name="Logo Design")

User: "Create project 'Website Redesign' for KD Companies with budget ₹50,000"
You: Call create_project(client_name="KD Companies", project_name="Website Redesign", total_cost=50000)
TOOLS:
• create_client(name, company?, email?, phone?)
• create_quote(client_name, quote_number, to_name, items:[{{description,amount}}])
• fetch_and_send_quote_pdf(search_term)
• create_invoice(client_name, invoice_number, items:[{{description,amount}}], due_date?)
• get_invoice_details(invoice_number)
• update_invoice(invoice_number, status?, due_date?, notes?)
• delete_invoice(invoice_number)
• send_invoice_pdf(search_term)
• record_payment(client_name, amount, payment_method?, invoice_number?)
• get_all_invoices(status?)
• get_client_balance(client_name)
• get_all_projects()
• create_project(client_name, project_name, total_cost?, deadline?)
• create_task(title, project_name?, assigned_to?, task_cost?, deadline?, description?, notes?)
• update_task(title, status?, assigned_to?, task_cost?, deadline?, notes?)
• get_tasks(assigned_to?, project_name?, status?, deadline_before?)
• get_task_summary(project_name?, assigned_to?)
• delete_task(title)

History:
{history if history else 'None'}"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.message}
    ]
    
    try:
        print(f"✅ [DEBUG] Calling OpenRouter with tools...")
        
        # First call: AI decides whether to use tools
        completion = ai_client.chat.completions.create(
            model="google/gemini-2.5-flash",
            messages=messages,
            tools=tools,
            max_tokens=300,
            temperature=0
        )
        
        response_message = completion.choices[0].message
        print(f"🤖 [DEBUG] AI response type: {'tool_calls' if response_message.tool_calls else 'text'}")
        
        # If AI wants to call tools
        if response_message.tool_calls:
            print(f"🔧 [DEBUG] Tool calls detected: {len(response_message.tool_calls)}")
            
            # Add AI's response to messages
            messages.append(response_message.model_dump())
            
            # Execute each tool call
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"  → Executing: {function_name}({function_args})")
                
                # 🛠️ BULLETPROOF FIX: Correct AI hallucinated parameter names
                if function_name == "create_client":
                    if "clientname" in function_args and "name" not in function_args:
                        function_args["name"] = function_args.pop("clientname")
                    elif "client_name" in function_args and "name" not in function_args:
                        function_args["name"] = function_args.pop("client_name")
                
                if function_name == "create_quote":
                    if "clientname" in function_args and "client_name" not in function_args:
                        function_args["client_name"] = function_args.pop("clientname")
                
                if function_name == "record_payment":
                    if "clientname" in function_args and "client_name" not in function_args:
                        function_args["client_name"] = function_args.pop("clientname")
                    if "invoicenumber" in function_args and "invoice_number" not in function_args:
                        function_args["invoice_number"] = function_args.pop("invoicenumber")
                    if "paymentmethod" in function_args and "payment_method" not in function_args:
                        function_args["payment_method"] = function_args.pop("paymentmethod")

                # Now execute the tool with the corrected arguments
                if function_name in tool_map:
                    tool_result = tool_map[function_name].invoke(function_args)
                    print(f"  ✅ Tool result: {tool_result[:150]}...")
                else:
                    tool_result = f"❌ Tool '{function_name}' not found"
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
            
            # Second call: AI generates final response based on tool results
            print(f"🤖 [DEBUG] Calling AI again for final response...")
            final_completion = ai_client.chat.completions.create(
                model="google/gemini-2.5-flash",
                messages=messages,
                max_tokens=200,
                temperature=0
            )
            
            final_text = final_completion.choices[0].message.content
            if final_text is None:
                final_text = "✅ Action completed."
            else:
                final_text = final_text.strip()
            
            print(f"💬 FINAL RESPONSE: {final_text[:200]}")
            
            add_to_history(user_id, "Assistant", final_text)
            return {"status": "success", "response": final_text}
        
        else:
            # No tool calls, just a text response
            final_text = response_message.content
            if final_text is None:
                tool_names = [tc.function.name for tc in response_message.tool_calls]
                if "create_client" in tool_names and "create_quote" in tool_names:
                    final_text = "✅ Client and quotation created successfully."
                elif "create_client" in tool_names:
                    final_text = "✅ Client created successfully."
                elif "create_quote" in tool_names:
                    final_text = "✅ Quotation created successfully."
                else:
                    final_text = "✅ Action completed."
            else:
                final_text = final_text.strip()
            
            print(f"💬 DIRECT RESPONSE: {final_text[:200]}")
            
            add_to_history(user_id, "Assistant", final_text)
            return {"status": "success", "response": final_text}
            
    except Exception as e:
        print(f"❌ [DEBUG] AI ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "response": f"Error: {str(e)}"}

# ==========================================
# 7. MANUAL CRM ENDPOINTS (For React Frontend)
# ==========================================
class QuoteItemModel(BaseModel):
    description: str
    note: Optional[str] = ""
    quantity: float = 1
    amount: float

class TimelineModel(BaseModel):
    process: str
    note: Optional[str] = ""
    delivery: str

class CreateQuoteRequest(BaseModel):
    client_name: str
    quote_number: str
    to_name: str
    items: List[QuoteItemModel]
    requirements: Optional[str] = ""
    timeline: Optional[List[TimelineModel]] = []
    terms: Optional[str] = ""
    payment_schedule: Optional[str] = "Project advance 50% on total work amount, and 50% final project submitting"
    from_name: str = "MD SAEED"
    from_email: str = "muhammadsaeed999@gmail.com"
    from_phone: str = "+91 7559978561"
    tax_rate: float = 0
    discount: float = 0
    valid_days: int = 30
    notes: Optional[str] = ""

@app.post("/api/quotes/manual")
def create_quote_manual(request: CreateQuoteRequest):
    items_dict = [item.model_dump() for item in request.items]
    timeline_dict = [tl.model_dump() for tl in request.timeline] if request.timeline else None
    
    result = create_quote.invoke({
        "client_name": request.client_name,
        "quote_number": request.quote_number,
        "to_name": request.to_name,
        "items": items_dict,
        "requirements": request.requirements,
        "timeline": timeline_dict,
        "terms": request.terms,
        "payment_schedule": request.payment_schedule,
        "from_name": request.from_name,
        "from_email": request.from_email,
        "from_phone": request.from_phone,
        "tax_rate": request.tax_rate,
        "discount": request.discount,
        "valid_days": request.valid_days,
        "notes": request.notes
    })
    
    if "❌" in result:
        raise HTTPException(status_code=400, detail=result)
        
    return {"status": "success", "message": result, "quote_number": request.quote_number}

@app.get("/api/quotes/{quote_number}/pdf")
def get_quote_pdf(quote_number: str):
    pdf_result = generate_quote_pdf.invoke({"quote_number": quote_number})
    
    if "❌" in pdf_result:
        raise HTTPException(status_code=404, detail=pdf_result)
    
    pdf_path = f"/tmp/quote_{quote_number}.pdf"
    if os.path.exists(pdf_path):
        return FileResponse(path=pdf_path, filename=f"Quotation_{quote_number}.pdf", media_type="application/pdf")
    else:
        raise HTTPException(status_code=500, detail="PDF file was not generated.")

@app.get("/api/quotes/list")
def list_all_quotes():
    try:
        from crm_tools import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT q.id, q.quote_number, q.quotation_date, q.valid_until,
                   q.to_name, q.total_amount, q.status, c.name as client_name
            FROM quotes q
            LEFT JOIN clients c ON q.client_id = c.id
            ORDER BY q.created_at DESC;
        """)
        quotes = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = [{
            "id": str(q[0]),
            "quote_number": q[1],
            "quotation_date": str(q[2]) if q[2] else "",
            "valid_until": str(q[3]) if q[3] else "",
            "to_name": q[4] or "",
            "total_amount": float(q[5] or 0),
            "status": q[6],
            "client_name": q[7] or "Unknown"
        } for q in quotes]
        
        return {"status": "success", "quotes": result}
    except Exception as e:
        print(f"Error in list_all_quotes: {str(e)}")
        return {"status": "error", "message": str(e)}

import json # Make sure this is at the top of your file if not already there

@app.post("/api/quotes/{quote_number}/convert-to-project")
async def convert_quote_to_project_api(quote_number: str):
    """Convert an accepted quotation into a Project AND automatically generate an Invoice."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Find the quote (removed q.items from SELECT)
        cursor.execute("""
            SELECT q.id, q.quote_number, q.to_name, q.total_amount, q.client_id,
                   c.name as client_name, c.company
            FROM quotes q
            LEFT JOIN clients c ON q.client_id = c.id
            WHERE q.quote_number = %s;
        """, (quote_number,))
        quote = cursor.fetchone()
        
        if not quote:
            cursor.close()
            conn.close()
            return {"status": "error", "message": f"Quote '{quote_number}' not found."}
        
        quote_id, q_number, to_name, total_amount, client_id, client_name, company = quote
        
        # 2. Fetch items for this quote from the quote_items table
        cursor.execute("""
            SELECT description, amount FROM quote_items WHERE quote_id = %s ORDER BY sort_order;
        """, (quote_id,))
        quote_items_rows = cursor.fetchall()
        
        # Format items as a list of dicts for the invoice JSON column
        items_list = [{"description": row[0], "amount": float(row[1])} for row in quote_items_rows]
        items_json = json.dumps(items_list)
        
        # 3. Check if project already exists for this quote
        cursor.execute("SELECT id, name FROM projects WHERE quote_id = %s;", (quote_id,))
        existing_project = cursor.fetchone()
        
        if existing_project:
            cursor.close()
            conn.close()
            return {
                "status": "error", 
                "message": f"Project for quote '{quote_number}' already exists.",
                "project_id": str(existing_project[0]),
                "project_name": existing_project[1]
            }
        
        # 4. Generate names
        project_name = f"Project - {q_number}"
        # Convert Q-001 to INV-001
        invoice_number = f"INV-{q_number.replace('Q-', '')}" 
        
        # 5. Insert Project
        cursor.execute("""
            INSERT INTO projects (client_id, name, status, total_cost, quote_id, source)
            VALUES (%s, %s, 'Pending', %s, %s, 'quote')
            RETURNING id;
        """, (client_id, project_name, total_amount, quote_id))
        project_id = cursor.fetchone()[0]
        
        # 6. Create Invoice (Unpaid status, ready to send directly)
        cursor.execute("""
            INSERT INTO invoices (client_id, project_id, invoice_number, status, total_amount, items, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            RETURNING id;
        """, (client_id, project_id, invoice_number, 'Unpaid', total_amount, items_json))
        invoice_id = cursor.fetchone()[0]
        
        # 7. Update quote status to 'Accepted'
        cursor.execute("""
            UPDATE quotes SET status = 'Accepted' WHERE id = %s;
        """, (quote_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Quote '{quote_number}' successfully converted!",
            "project": {
                "id": str(project_id),
                "name": project_name,
                "client": client_name or company,
                "total_cost": float(total_amount)
            },
            "invoice": {
                "id": str(invoice_id),
                "invoice_number": invoice_number,
                "total_amount": float(total_amount),
                "status": "Unpaid"
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
    """Convert an accepted quotation into a Project AND automatically generate an Invoice."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Find the quote and its items
        cursor.execute("""
            SELECT q.id, q.quote_number, q.to_name, q.total_amount, q.client_id, q.items,
                   c.name as client_name, c.company
            FROM quotes q
            LEFT JOIN clients c ON q.client_id = c.id
            WHERE q.quote_number = %s;
        """, (quote_number,))
        quote = cursor.fetchone()
        
        if not quote:
            cursor.close()
            conn.close()
            return {"status": "error", "message": f"Quote '{quote_number}' not found."}
        
        quote_id, q_number, to_name, total_amount, client_id, items_json, client_name, company = quote
        
        # 2. Check if project already exists for this quote
        cursor.execute("SELECT id, name FROM projects WHERE quote_id = %s;", (quote_id,))
        existing_project = cursor.fetchone()
        
        if existing_project:
            cursor.close()
            conn.close()
            return {
                "status": "error", 
                "message": f"Project for quote '{quote_number}' already exists.",
                "project_id": str(existing_project[0]),
                "project_name": existing_project[1]
            }
        
        # 3. Generate names
        project_name = f"Project - {q_number}"
        # Convert Q-001 to INV-001
        invoice_number = f"INV-{q_number.replace('Q-', '')}" 
        
        # 4. Insert Project
        cursor.execute("""
            INSERT INTO projects (client_id, name, status, total_cost, quote_id, source)
            VALUES (%s, %s, 'Pending', %s, %s, 'quote')
            RETURNING id;
        """, (client_id, project_name, total_amount, quote_id))
        project_id = cursor.fetchone()[0]
        
        # 5. Create Invoice (Draft status so you can review before sending)
                # 5. Create Invoice (Unpaid status, ready to send directly)
        cursor.execute("""
            INSERT INTO invoices (client_id, project_id, invoice_number, status, total_amount, items, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            RETURNING id;
        """, (client_id, project_id, invoice_number, 'Unpaid', total_amount, items_json))
        invoice_id = cursor.fetchone()[0]
        
        # 6. Update quote status to 'Accepted'
        cursor.execute("""
            UPDATE quotes SET status = 'Accepted' WHERE id = %s;
        """, (quote_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Quote '{quote_number}' successfully converted!",
            "project": {
                "id": str(project_id),
                "name": project_name,
                "client": client_name or company,
                "total_cost": float(total_amount)
            },
            "invoice": {
                "id": str(invoice_id),
                "invoice_number": invoice_number,
                "total_amount": float(total_amount),
                "status": "Draft"
            }
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
    """Convert an accepted quotation into a project via the CRM frontend."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Find the quote
        cursor.execute("""
            SELECT q.id, q.quote_number, q.to_name, q.total_amount, q.client_id,
                   c.name as client_name, c.company
            FROM quotes q
            LEFT JOIN clients c ON q.client_id = c.id
            WHERE q.quote_number = %s;
        """, (quote_number,))
        quote = cursor.fetchone()
        
        if not quote:
            cursor.close()
            conn.close()
            return {"status": "error", "message": f"Quote '{quote_number}' not found."}
        
        quote_id, q_number, to_name, total_amount, client_id, client_name, company = quote
        
        # 2. Check if project already exists for this quote
        cursor.execute("SELECT id, name FROM projects WHERE quote_id = %s;", (quote_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return {
                "status": "error", 
                "message": f"Project for quote '{quote_number}' already exists.",
                "project_id": str(existing[0]),
                "project_name": existing[1]
            }
        
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
        
        return {
            "status": "success",
            "message": f"Quote '{quote_number}' converted to project successfully!",
            "project": {
                "id": str(project_id),
                "name": project_name,
                "client": client_name,
                "company": company,
                "total_cost": float(total_amount),
                "source": "quote",
                "quote_number": q_number
            }
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.put("/api/quotes/{quote_number}/status")
async def update_quote_status(quote_number: str, status: str):
    """Quick status update for a quote without full edit."""
    try:
        valid_statuses = ['Draft', 'Sent', 'Accepted', 'Rejected']
        if status not in valid_statuses:
            return {"status": "error", "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE quotes SET status = %s WHERE quote_number = %s RETURNING id;
        """, (status, quote_number))
        
        updated = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if not updated:
            return {"status": "error", "message": f"Quote '{quote_number}' not found."}
        
        return {"status": "success", "message": f"Quote '{quote_number}' status updated to '{status}'."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.put("/api/invoices/{invoice_number}/status")
async def update_invoice_status_quick(invoice_number: str, status: str):
    """Quick status update for an invoice."""
    try:
        valid_statuses = ['Draft', 'Sent', 'Paid', 'Overdue', 'Cancelled']
        if status not in valid_statuses:
            return {"status": "error", "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE invoices SET status = %s WHERE invoice_number = %s RETURNING id;
        """, (status, invoice_number))
        
        updated = cursor.fetchone()
        
        # ✨ If marked as Paid, also update linked project to Completed
        if status == 'Paid' and updated:
            cursor.execute("""
                UPDATE projects SET status = 'Completed' 
                WHERE id IN (SELECT project_id FROM invoices WHERE invoice_number = %s)
                AND project_id IS NOT NULL;
            """, (invoice_number,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if not updated:
            return {"status": "error", "message": f"Invoice '{invoice_number}' not found."}
        
        return {"status": "success", "message": f"Invoice '{invoice_number}' status updated to '{status}'."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/invoices/list")
async def list_invoices_full():
    """List all invoices with client info, project info, and balance."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                i.id, i.invoice_number, i.created_at, i.due_date, i.status, i.total_amount,
                COALESCE(i.paid_amount, 0) as paid_amount,
                (i.total_amount - COALESCE(i.paid_amount, 0)) as balance,
                c.name as client_name, c.company,
                p.name as project_name, p.id as project_id
            FROM invoices i
            LEFT JOIN clients c ON i.client_id = c.id
            LEFT JOIN projects p ON i.project_id = p.id
            ORDER BY i.created_at DESC;
        """)
        
        invoices = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for inv in invoices:
            result.append({
                "id": str(inv[0]),
                "invoice_number": inv[1],
                "created_at": inv[2].isoformat() if inv[2] else None,
                "due_date": inv[3].isoformat() if hasattr(inv[3], 'isoformat') and inv[3] else None,
                "status": inv[4],
                "total_amount": float(inv[5] or 0),
                "paid_amount": float(inv[6] or 0), # ✨ NEW
                "balance": float(inv[7] or 0),     #  NEW
                "client_name": inv[8],
                "company": inv[9],
                "project_name": inv[10],
                "project_id": str(inv[11]) if inv[11] else None
            })
        
        return {"status": "success", "invoices": result}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
    """List all invoices with linked project information."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                i.id, i.invoice_number, i.created_at, i.due_date, i.status, i.total_amount,
                c.name as client_name, c.company,
                p.name as project_name, p.id as project_id
            FROM invoices i
            LEFT JOIN clients c ON i.client_id = c.id
            LEFT JOIN projects p ON i.project_id = p.id
            ORDER BY i.created_at DESC;
        """)
        
        invoices = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for inv in invoices:
            result.append({
                "id": str(inv[0]),
                "invoice_number": inv[1],
                "created_at": inv[2].isoformat() if inv[2] else None,
                "due_date": inv[3].isoformat() if hasattr(inv[3], 'isoformat') else str(inv[3]) if inv[3] else None,
                "status": inv[4],
                "total_amount": float(inv[5] or 0),
                "client_name": inv[6],
                "company": inv[7],
                "project_name": inv[8],
                "project_id": str(inv[9]) if inv[9] else None
            })
        
        return {"status": "success", "invoices": result}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/quotes/{quote_number}")
def get_single_quote(quote_number: str):
    try:
        from crm_tools import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT q.quote_number, q.to_name, q.requirements, q.terms, 
                   q.payment_schedule, q.total_amount, q.status, q.notes
            FROM quotes q WHERE q.quote_number = %s;
        """, (quote_number,))
        quote = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not quote:
            return {"status": "error", "message": "Quote not found"}
        
        return {
            "status": "success",
            "quote": {
                "quote_number": quote[0],
                "to_name": quote[1] or "",
                "requirements": quote[2] or "",
                "terms": quote[3] or "",
                "payment_schedule": quote[4] or "",
                "total_amount": float(quote[5] or 0),
                "status": quote[6],
                "notes": quote[7] or ""
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/projects/list")
async def list_projects_full():
    """List all projects with client info and assigned team members."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.id, p.name, p.status, p.total_cost, p.deadline, p.created_at, p.source,
                c.name as client_name, c.company,
                COALESCE((SELECT STRING_AGG(DISTINCT assigned_to, ', ') FROM tasks WHERE project_id = p.id AND assigned_to IS NOT NULL AND assigned_to != ''), '') as assignees_str
            FROM projects p
            LEFT JOIN clients c ON p.client_id = c.id
            ORDER BY p.created_at DESC;
        """)
        
        projects = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for p in projects:
            assignees_str = p[9] or ""
            # Split the comma-separated string into a clean Python list
            assignees_list = [a.strip() for a in assignees_str.split(',') if a.strip()] if assignees_str else []
            
            result.append({
                "id": str(p[0]),
                "name": p[1],
                "status": p[2] or 'Pending',
                "total_cost": float(p[3] or 0),
                "deadline": p[4].isoformat() if hasattr(p[4], 'isoformat') and p[4] else None,
                "created_at": p[5].isoformat() if p[5] else None,
                "source": p[6] or 'manual',
                "client_name": p[7],
                "company": p[8],
                "assignees": assignees_list  # This is what the frontend reads!
            })
        
        return {"status": "success", "projects": result}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
    """List all projects with client info and assigned team members."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.id, p.name, p.status, p.total_cost, p.deadline, p.created_at, p.source,
                c.name as client_name, c.company,
                COALESCE((SELECT STRING_AGG(DISTINCT assigned_to, ', ') FROM tasks WHERE project_id = p.id AND assigned_to IS NOT NULL AND assigned_to != ''), '') as assignees
            FROM projects p
            LEFT JOIN clients c ON p.client_id = c.id
            ORDER BY p.created_at DESC;
        """)
        
        projects = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for p in projects:
            # Parse the comma-separated string into a clean list of names
            assignees_str = p[9] or ""
            assignees_list = [a.strip() for a in assignees_str.split(',') if a.strip()] if assignees_str else []
            
            result.append({
                "id": str(p[0]),
                "name": p[1],
                "status": p[2] or 'Pending',
                "total_cost": float(p[3] or 0),
                "deadline": p[4].isoformat() if hasattr(p[4], 'isoformat') and p[4] else None,
                "created_at": p[5].isoformat() if p[5] else None,
                "source": p[6] or 'manual',
                "client_name": p[7],
                "company": p[8],
                "assignees": assignees_list  # Returns a list like ["John", "Sarah"]
            })
        
        return {"status": "success", "projects": result}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
@app.put("/api/projects/{project_id}")
async def update_project(project_id: str, name: str = None, status: str = None, total_cost: float = None, deadline: str = None, notes: str = None, requirements: str = None, description: str = None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None: updates.append("name = %s"); params.append(name)
        if status is not None: updates.append("status = %s"); params.append(status)
        if total_cost is not None: updates.append("total_cost = %s"); params.append(total_cost)
        if deadline is not None: updates.append("deadline = %s"); params.append(deadline if deadline else None)
        if notes is not None: updates.append("notes = %s"); params.append(notes)
        if description is not None: updates.append("description = %s"); params.append(description)
        
        # Handle requirements as JSON string
        if requirements is not None:
            req_json = requirements if requirements.startswith('[') else json.dumps([requirements])
            updates.append("requirements = %s")
            params.append(req_json)
        
        if not updates:
            cursor.close(); conn.close()
            return {"status": "error", "message": "No fields to update."}
        
        params.append(project_id)
        query = f"UPDATE projects SET {', '.join(updates)} WHERE id = %s RETURNING id;"
        cursor.execute(query, params)
        
        updated = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if not updated: return {"status": "error", "message": "Project not found."}
        return {"status": "success", "message": "Project updated successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    """Update project details."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None: updates.append("name = %s"); params.append(name)
        if status is not None: updates.append("status = %s"); params.append(status)
        if total_cost is not None: updates.append("total_cost = %s"); params.append(total_cost)
        if deadline is not None: updates.append("deadline = %s"); params.append(deadline if deadline else None)
        if notes is not None: updates.append("notes = %s"); params.append(notes)
        if requirements is not None: updates.append("requirements = %s"); params.append(requirements)
        if description is not None: updates.append("description = %s"); params.append(description)
        
        if not updates:
            cursor.close(); conn.close()
            return {"status": "error", "message": "No fields to update."}
        
        params.append(project_id)
        query = f"UPDATE projects SET {', '.join(updates)} WHERE id = %s RETURNING id;"
        cursor.execute(query, params)
        
        updated = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if not updated: return {"status": "error", "message": "Project not found."}
        return {"status": "success", "message": "Project updated successfully."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}
    """Update project details."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build dynamic update query
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if status is not None:
            updates.append("status = %s")
            params.append(status)
        if total_cost is not None:
            updates.append("total_cost = %s")
            params.append(total_cost)
        if deadline is not None:
            updates.append("deadline = %s")
            params.append(deadline if deadline else None)
        if notes is not None:
            # Check if notes column exists
            cursor.execute("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'projects' AND column_name = 'notes';
            """)
            if cursor.fetchone():
                updates.append("notes = %s")
                params.append(notes)
        
        if not updates:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "No fields to update."}
        
        params.append(project_id)
        query = f"UPDATE projects SET {', '.join(updates)} WHERE id = %s RETURNING id;"
        cursor.execute(query, params)
        
        updated = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if not updated:
            return {"status": "error", "message": f"Project '{project_id}' not found."}
        
        return {"status": "success", "message": "Project updated successfully."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.put("/api/projects/{project_id}/status")
async def update_project_status_quick(project_id: str, status: str):
    """Quick status update for a project."""
    try:
        valid_statuses = ['Pending', 'In Progress', 'Completed', 'On Hold', 'Cancelled']
        if status not in valid_statuses:
            return {"status": "error", "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update project status
        cursor.execute("""
            UPDATE projects SET status = %s WHERE id = %s RETURNING id;
        """, (status, project_id))
        
        updated = cursor.fetchone()
        
        # ✨ If marked as Completed, also update linked tasks to completed
        if status == 'Completed' and updated:
            cursor.execute("""
                UPDATE tasks SET status = 'completed' 
                WHERE project_id = %s AND status != 'completed';
            """, (project_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        if not updated:
            return {"status": "error", "message": f"Project '{project_id}' not found."}
        
        return {"status": "success", "message": f"Project status updated to '{status}'."}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/projects")
async def create_project_api(name: str, client_name: str = None, total_cost: float = 0, deadline: str = None, status: str = "Pending", requirements: str = "[]", description: str = ""):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        client_id = None
        if client_name:
            cursor.execute("SELECT id FROM clients WHERE LOWER(name) LIKE LOWER(%s) LIMIT 1;", (f"%{client_name}%",))
            client = cursor.fetchone()
            if not client:
                cursor.execute("INSERT INTO clients (name, company) VALUES (%s, %s) RETURNING id;", (client_name, client_name))
                client_id = cursor.fetchone()[0]
            else:
                client_id = client[0]

        # Save requirements as JSON string
        req_json = requirements if requirements.startswith('[') else json.dumps([requirements])

        cursor.execute("""
            INSERT INTO projects (client_id, name, status, total_cost, deadline, source, requirements, description)
            VALUES (%s, %s, %s, %s, %s, 'manual', %s, %s)
            RETURNING id, created_at;
        """, (client_id, name, status, total_cost, deadline if deadline else None, req_json, description))
        
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": "Project created", "id": str(result[0])}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def create_project_api(name: str, client_name: str = None, total_cost: float = 0, deadline: str = None, status: str = "Pending", requirements: str = "", description: str = ""):
    """Create a new project via frontend."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        client_id = None
        if client_name:
            cursor.execute("SELECT id FROM clients WHERE LOWER(name) LIKE LOWER(%s) LIMIT 1;", (f"%{client_name}%",))
            client = cursor.fetchone()
            if not client:
                cursor.execute("INSERT INTO clients (name, company) VALUES (%s, %s) RETURNING id;", (client_name, client_name))
                client_id = cursor.fetchone()[0]
            else:
                client_id = client[0]

        cursor.execute("""
            INSERT INTO projects (client_id, name, status, total_cost, deadline, source, requirements, description)
            VALUES (%s, %s, %s, %s, %s, 'manual', %s, %s)
            RETURNING id, created_at;
        """, (client_id, name, status, total_cost, deadline if deadline else None, requirements, description))
        
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Project created", "id": str(result[0])}
    except Exception as e:
        return {"status": "error", "message": str(e)}
@app.delete("/api/projects/{project_id}")
async def delete_project_api(project_id: str):
    """Delete a project."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = %s RETURNING id;", (project_id,))
        deleted = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if deleted:
            return {"status": "success", "message": "Project deleted"}
        return {"status": "error", "message": "Project not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}



@app.get("/api/projects/{project_id}")
async def get_project_details(project_id: str):
    """Get full details of a single project including requirements."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, p.status, p.total_cost, p.deadline, p.created_at, p.source, p.requirements, p.description,
                   c.name as client_name, c.company
            FROM projects p LEFT JOIN clients c ON p.client_id = c.id WHERE p.id = %s;
        """, (project_id,))
        project = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not project: 
            return {"status": "error", "message": "Project not found"}
        
        return {"status": "success", "project": {
            "id": str(project[0]), "name": project[1], "status": project[2], "total_cost": float(project[3] or 0),
            "deadline": project[4].isoformat() if project[4] else None, "created_at": project[5].isoformat() if project[5] else None,
            "source": project[6], "requirements": project[7], "description": project[8],
            "client_name": project[9], "company": project[10]
        }}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    """Get full details of a single project."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, p.status, p.total_cost, p.deadline, p.created_at, p.source, p.requirements, p.description,
                   c.name as client_name, c.company
            FROM projects p LEFT JOIN clients c ON p.client_id = c.id WHERE p.id = %s;
        """, (project_id,))
        project = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not project: return {"status": "error", "message": "Project not found"}
        
        return {"status": "success", "project": {
            "id": str(project[0]), "name": project[1], "status": project[2], "total_cost": float(project[3] or 0),
            "deadline": project[4].isoformat() if project[4] else None, "created_at": project[5].isoformat() if project[5] else None,
            "source": project[6], "requirements": project[7], "description": project[8],
            "client_name": project[9], "company": project[10]
        }}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/projects/{project_id}/tasks")
async def get_project_tasks(project_id: str):
    """Get all tasks for a specific project."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, assigned_to, task_cost, deadline, status, created_at 
            FROM tasks WHERE project_id = %s ORDER BY created_at DESC;
        """, (project_id,))
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for t in tasks:
            result.append({
                "id": str(t[0]), "title": t[1], "assigned_to": t[2] or "", 
                "task_cost": float(t[3] or 0), "deadline": t[4].isoformat() if t[4] else None,
                "status": t[5] or 'pending', "created_at": t[6].isoformat() if t[6] else None
            })
        return {"status": "success", "tasks": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/projects/{project_id}/tasks")
async def create_project_task(project_id: str, title: str, assigned_to: str = "", task_cost: float = 0, deadline: str = None):
    """Create a new task for a specific project."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (project_id, title, assigned_to, task_cost, deadline, status)
            VALUES (%s, %s, %s, %s, %s, 'pending') RETURNING id;
        """, (project_id, title, assigned_to, task_cost, deadline if deadline else None))
        task_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": "Task created", "id": str(task_id)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/test-pdf/{quote_number}")
def test_pdf_to_telegram(quote_number: str):
    """Direct test: Generate PDF and send to Telegram. No AI agent needed."""
    try:
        print(f"\n🧪 Testing PDF for quote: {quote_number}")
        result = generate_quote_pdf.invoke({"quote_number": quote_number})
        print(f"📊 Result: {result}")
        return {"status": "success", "message": result}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/api/projects/{project_id}/assignees")
async def add_project_assignee(project_id: str, name: str, task_title: str = "", task_cost: float = 0):
    """Add a person to a project with a specific task and budget."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Use the provided title, or fallback to a default
        final_title = task_title.strip() if task_title.strip() else f"Task for {name}"
        
        cursor.execute("""
            INSERT INTO tasks (project_id, title, assigned_to, task_cost, status)
            VALUES (%s, %s, %s, %s, 'pending') RETURNING id;
        """, (project_id, final_title, name, task_cost))
        
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": f"Added {name} to project"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    """Add a person to a project by creating a task for them."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Create a task for this person so they are linked to the project
        cursor.execute("""
            INSERT INTO tasks (project_id, title, assigned_to, status)
            VALUES (%s, %s, %s, 'pending') RETURNING id;
        """, (project_id, f"Assignment for {name}", name))
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": f"Added {name} to project"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.delete("/api/projects/{project_id}/assignees/{name}")
async def remove_project_assignee(project_id: str, name: str):
    """Remove a person from a project by deleting their tasks."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE project_id = %s AND assigned_to = %s;", (project_id, name))
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": f"Removed {name} from project"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Add this to your imports at the top:
import json

# ... inside your main.py file ...

@app.get("/api/projects/{project_id}/invoices")
async def get_project_invoices(project_id: str):
    """Get all invoices linked to a specific project."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, invoice_number, total_amount, status, created_at, due_date
            FROM invoices WHERE project_id = %s ORDER BY created_at DESC;
        """, (project_id,))
        invoices = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for inv in invoices:
            result.append({
                "id": str(inv[0]), "invoice_number": inv[1], "total_amount": float(inv[2] or 0),
                "status": inv[3] or 'Draft', "created_at": inv[4].isoformat() if inv[4] else None,
                "due_date": inv[5].isoformat() if hasattr(inv[5], 'isoformat') and inv[5] else None
            })
        return {"status": "success", "invoices": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.put("/api/projects/{project_id}/toggle-requirement")
async def toggle_requirement(project_id: str, index: int):
    """Toggle the completion status of a specific requirement."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch current requirements
        cursor.execute("SELECT requirements FROM projects WHERE id = %s;", (project_id,))
        row = cursor.fetchone()
        if not row:
            return {"status": "error", "message": "Project not found"}
            
        reqs = row[0]
        # Parse requirements (handle both old string arrays and new object arrays)
        if isinstance(reqs, str):
            try: reqs = json.loads(reqs)
            except: reqs = []
            
        if not isinstance(reqs, list): reqs = []
        
        # Convert old string format to object format if needed
        new_reqs = []
        for r in reqs:
            if isinstance(r, str):
                new_reqs.append({"text": r, "completed": False})
            else:
                new_reqs.append(r)
                
        # Toggle the specific index
        if 0 <= index < len(new_reqs):
            new_reqs[index]["completed"] = not new_reqs[index].get("completed", False)
            
        # Save back to DB
        cursor.execute("UPDATE projects SET requirements = %s WHERE id = %s;", (json.dumps(new_reqs), project_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "requirements": new_reqs}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/invoices/{invoice_number}/record-payment")
async def record_invoice_payment(invoice_number: str, amount: float, payment_method: str, payment_date: str):
    """Record a payment for an invoice and update its paid amount."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Get invoice details (including current paid_amount)
        cursor.execute("""
            SELECT id, total_amount, client_id, project_id, COALESCE(paid_amount, 0) 
            FROM invoices WHERE invoice_number = %s
        """, (invoice_number,))
        invoice = cursor.fetchone()
        
        if not invoice:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Invoice not found"}
        
        inv_id, total_amount, client_id, project_id, current_paid = invoice
        
        # 2. Calculate the new paid amount
        new_paid_amount = float(current_paid) + float(amount)
        
        # 3. Determine the new status (Paid if fully covered, otherwise stays Unpaid/Partial)
        new_status = 'Paid' if new_paid_amount >= float(total_amount) else 'Unpaid'
        
        # 4. Update the invoice with the new paid amount and status
        cursor.execute("""
            UPDATE invoices 
            SET paid_amount = %s, status = %s
            WHERE id = %s
        """, (new_paid_amount, new_status, inv_id))
        
        # 5. (Optional) Log to payments table if it exists
        try:
            cursor.execute("""
                INSERT INTO payments (client_id, invoice_id, amount, payment_method, payment_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (client_id, inv_id, amount, payment_method, payment_date))
        except Exception:
            pass # Ignore if payments table doesn't exist
            
        # 6. If fully paid and linked to a project, mark project as Completed
        if new_paid_amount >= float(total_amount) and project_id:
            cursor.execute("UPDATE projects SET status = 'Completed' WHERE id = %s", (project_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Payment recorded successfully"}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
    """Record a payment for an invoice and update its status."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Get invoice details
        cursor.execute("""
            SELECT id, total_amount, client_id, project_id 
            FROM invoices WHERE invoice_number = %s
        """, (invoice_number,))
        invoice = cursor.fetchone()
        
        if not invoice:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Invoice not found"}
        
        inv_id, total_amount, client_id, project_id = invoice
        
        # 2. Update invoice status to 'Paid' (Notes removed to prevent errors)
        cursor.execute("""
            UPDATE invoices 
            SET status = 'Paid'
            WHERE id = %s
        """, (inv_id,))
        
        # 3. (Optional) Log to payments table if it exists
        try:
            cursor.execute("""
                INSERT INTO payments (client_id, invoice_id, amount, payment_method, payment_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (client_id, inv_id, amount, payment_method, payment_date))
        except Exception:
            pass # Ignore if payments table doesn't exist
            
        # 4. If fully paid and linked to a project, mark project as Completed
        if float(amount) >= float(total_amount) and project_id:
            cursor.execute("UPDATE projects SET status = 'Completed' WHERE id = %s", (project_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Payment recorded successfully"}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
    """Record a payment for an invoice and update its status."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Get invoice details
        cursor.execute("""
            SELECT id, total_amount, client_id, project_id 
            FROM invoices WHERE invoice_number = %s
        """, (invoice_number,))
        invoice = cursor.fetchone()
        
        if not invoice:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Invoice not found"}
        
        inv_id, total_amount, client_id, project_id = invoice
        
        # 2. Build the note string safely in Python first
        payment_note = f"Payment recorded: ₹{amount} on {payment_date} via {payment_method}"
        
        # 3. Update invoice status to 'Paid' and append the note safely
        cursor.execute("""
            UPDATE invoices 
            SET status = 'Paid', 
                notes = CASE 
                    WHEN notes IS NULL OR notes = '' THEN %s 
                    ELSE notes || E'\n\n' || %s 
                END
            WHERE id = %s
        """, (payment_note, payment_note, inv_id))
        
        # 4. (Optional) Log to payments table if it exists
        try:
            cursor.execute("""
                INSERT INTO payments (client_id, invoice_id, amount, payment_method, payment_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (client_id, inv_id, amount, payment_method, payment_date))
        except Exception:
            pass # Ignore if payments table doesn't exist
            
        # 5. If fully paid and linked to a project, mark project as Completed
        if float(amount) >= float(total_amount) and project_id:
            cursor.execute("UPDATE projects SET status = 'Completed' WHERE id = %s", (project_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Payment recorded successfully"}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
    """Record a payment for an invoice and update its status."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Get invoice details
        cursor.execute("""
            SELECT id, total_amount, client_id, project_id 
            FROM invoices WHERE invoice_number = %s
        """, (invoice_number,))
        invoice = cursor.fetchone()
        
        if not invoice:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Invoice not found"}
        
        inv_id, total_amount, client_id, project_id = invoice
        
        # 2. Update invoice status to 'Paid' and add a note
        cursor.execute("""
            UPDATE invoices 
            SET status = 'Paid', 
                notes = COALESCE(notes || E'\n\n', '') || 'Payment recorded: ₹%s on %s via %s'
            WHERE id = %s
        """, (amount, payment_date, payment_method, inv_id))
        
        # 3. (Optional) If a payments table exists, log it there too
        try:
            cursor.execute("""
                INSERT INTO payments (client_id, invoice_id, amount, payment_method, payment_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (client_id, inv_id, amount, payment_method, payment_date))
        except Exception:
            pass # Ignore if payments table doesn't exist
            
        # 4. If fully paid and linked to a project, mark project as Completed
        if float(amount) >= float(total_amount) and project_id:
            cursor.execute("UPDATE projects SET status = 'Completed' WHERE id = %s", (project_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Payment recorded successfully"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}   

@app.put("/api/tasks/{task_id}/status")
async def update_task_status(task_id: str, status: str):
    """Update the status of a specific task."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tasks SET status = %s WHERE id = %s RETURNING id;
        """, (status, task_id))
        updated = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if updated:
            return {"status": "success", "message": "Task status updated"}
        return {"status": "error", "message": "Task not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}   


@app.put("/api/tasks/{task_id}/pay")
async def pay_task(task_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET is_paid = TRUE WHERE id = %s RETURNING id;", (task_id,))
        updated = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": "Task marked as paid"} if updated else {"status": "error", "message": "Task not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 2. Create Invoice from Task (Bill the client)
@app.post("/api/tasks/{task_id}/invoice")
async def invoice_task(task_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch task and project details
        cursor.execute("""
            SELECT t.task_cost, t.title, t.project_id, p.client_id, p.name 
            FROM tasks t JOIN projects p ON t.project_id = p.id WHERE t.id = %s;
        """, (task_id,))
        task_data = cursor.fetchone()
        
        if not task_data:
            cursor.close(); conn.close()
            return {"status": "error", "message": "Task not found"}
            
        task_cost, task_title, project_id, client_id, project_name = task_data
        invoice_number = f"INV-TASK-{task_id[:6].upper()}"
        
        # Create the invoice
        cursor.execute("""
            INSERT INTO invoices (client_id, project_id, invoice_number, total_amount, status, items, created_at)
            VALUES (%s, %s, %s, %s, 'Unpaid', %s, NOW()) RETURNING id;
        """, (client_id, project_id, invoice_number, task_cost, json.dumps([{"description": task_title, "amount": task_cost}])))
        
        # Mark task as invoiced
        cursor.execute("UPDATE tasks SET is_invoiced = TRUE WHERE id = %s;", (task_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": f"Invoice {invoice_number} created successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)} 

@app.get("/api/tasks")
async def get_all_tasks(project_id: str = None):
    """Fetch all tasks across all projects with client and project details."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ✨ Added t.is_paid and t.is_invoiced to the SELECT query
        if project_id:
            cursor.execute("""
                SELECT t.id, t.title, t.description, t.status, t.deadline, t.assigned_to, t.task_cost, t.notes, t.project_id, p.name as project_name, t.is_paid, t.is_invoiced
                FROM tasks t LEFT JOIN projects p ON t.project_id = p.id WHERE t.project_id = %s ORDER BY t.created_at DESC;
            """, (project_id,))
        else:
            cursor.execute("""
                SELECT t.id, t.title, t.description, t.status, t.deadline, t.assigned_to, t.task_cost, t.notes, t.project_id, p.name as project_name, t.is_paid, t.is_invoiced
                FROM tasks t LEFT JOIN projects p ON t.project_id = p.id ORDER BY t.created_at DESC;
            """)
            
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        
        result = []
        for t in tasks:
            result.append({
                "id": str(t[0]), "title": t[1], "description": t[2], "status": t[3] or 'To Do',
                "deadline": t[4].isoformat() if hasattr(t[4], 'isoformat') and t[4] else None,
                "assigned_to": t[5] or "", "task_cost": float(t[6] or 0), "notes": t[7],
                "project_id": str(t[8]) if t[8] else None, "project_name": t[9],
                "is_paid": bool(t[10]), "is_invoiced": bool(t[11])  #  Return the boolean values
            })
        return result
    except Exception as e:
        return {"error": str(e)}
# ==========================================
# 8. Include all routers
# ==========================================
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(quotes.router, prefix="/api/quotes", tags=["Quotes"])    
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["Invoices"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
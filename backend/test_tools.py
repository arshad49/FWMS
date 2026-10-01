from crm_tools import get_all_clients, get_client_balance, get_all_projects, get_dashboard_summary

print("Testing get_all_clients:")
print(get_all_clients.invoke({}))
print("\n" + "="*50 + "\n")

print("Testing get_dashboard_summary:")
print(get_dashboard_summary.invoke({}))
print("\n" + "="*50 + "\n")

print("Testing get_all_projects:")
print(get_all_projects.invoke({}))
import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Users, FolderKanban, ListTodo, FileText, Receipt, 
  Menu, ChevronLeft, Settings // <-- Settings is now properly imported
} from 'lucide-react';

export default function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const location = useLocation();

  const menuItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/clients', label: 'Client', icon: Users },
    { path: '/projects', label: 'Project', icon: FolderKanban },
    { path: '/tasks', label: 'Task', icon: ListTodo },
    { path: '/quotes', label: 'Quotes', icon: FileText },
    { path: '/invoices', label: 'Invoices', icon: Receipt },
    { path: '/settings', label: 'Settings', icon: Settings }, // <-- Fixed icon name
  ];

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full bg-white">
      {/* Logo */}
      <div className="p-6 flex items-center gap-3 border-b border-gray-100">
        <div className="w-8 h-8 bg-blue-900 rounded-lg flex items-center justify-center flex-shrink-0">
          <FolderKanban size={18} className="text-white" />
        </div>
        {!isCollapsed && <h1 className="font-bold text-slate-900 text-lg tracking-tight">Freelancer CRM</h1>}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          return (
            <Link 
              key={item.path} 
              to={item.path} 
              onClick={() => setIsMobileOpen(false)}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200 text-sm font-medium ${
                active 
                  ? 'bg-blue-50 text-blue-900 font-semibold' 
                  : 'text-gray-500 hover:bg-gray-50 hover:text-slate-900'
              }`}
            >
              <Icon size={18} className={active ? 'text-blue-900' : 'text-gray-400'} />
              {!isCollapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Actions */}
      <div className="p-4 border-t border-gray-100 space-y-1">
        <Link to="/" className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium text-gray-500 hover:bg-gray-50 hover:text-slate-900 transition">
          <Settings size={18} className="text-gray-400" />
          {!isCollapsed && <span>Settings</span>}
        </Link>
      </div>
    </div>
  );

  return (
    <>
      <aside className={`hidden md:flex flex-col border-r border-gray-200 transition-all duration-300 ${isCollapsed ? 'w-20' : 'w-64'}`}>
        <SidebarContent />
        <button 
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute bottom-20 right-[-12px] w-6 h-6 bg-white border border-gray-200 rounded-full flex items-center justify-center shadow-sm hover:bg-gray-50 z-10"
        >
          <ChevronLeft size={14} className={`transition-transform ${isCollapsed ? 'rotate-180' : ''}`} />
        </button>
      </aside>

      {isMobileOpen && (
        <div className="md:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={() => setIsMobileOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-64 bg-white shadow-xl">
            <SidebarContent />
          </aside>
        </div>
      )}

      <button 
        onClick={() => setIsMobileOpen(true)} 
        className="md:hidden fixed top-4 left-4 z-40 p-2 bg-white rounded-lg shadow-md border border-gray-200"
      >
        <Menu size={20} className="text-blue-900" />
      </button>
    </>
  );
}
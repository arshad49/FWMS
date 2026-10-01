import { useState, useEffect, useRef } from 'react';
import api from './api';
import { Bell, AlertCircle, Calendar, Check, Search } from 'lucide-react';

export default function Topbar({ onSearchClick }) {
  const [notifications, setNotifications] = useState([]);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const notifRef = useRef(null);

  const [readIds, setReadIds] = useState(() => {
    const saved = localStorage.getItem('readNotifs');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    api.get('/notifications')
      .then(res => setNotifications(res.data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    function handleClickOutside(event) {
      if (notifRef.current && !notifRef.current.contains(event.target)) setIsNotifOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const markAsRead = (id) => {
    const newReadIds = [...readIds, id];
    setReadIds(newReadIds);
    localStorage.setItem('readNotifs', JSON.stringify(newReadIds));
  };

  const markAllAsRead = () => {
    const allIds = notifications.map(n => n.id);
    setReadIds(allIds);
    localStorage.setItem('readNotifs', JSON.stringify(allIds));
  };

  const unreadCount = notifications.filter(n => !readIds.includes(n.id)).length;

  return (
    <div className="bg-white border-b border-gray-200 px-8 py-3 flex justify-between items-center sticky top-0 z-30 shadow-sm">
      
      {/* 1. Visible Search Bar */}
      <button 
        onClick={onSearchClick}
        className="flex items-center gap-3 px-4 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg text-sm text-gray-500 transition w-72 text-left group"
      >
        <Search size={16} className="text-gray-400 group-hover:text-blue-900 transition" />
        <span className="flex-1">Search...</span>
        <kbd className="px-1.5 py-0.5 bg-white border border-gray-200 rounded text-[10px] font-mono text-gray-400 shadow-sm">K</kbd>
      </button>

      {/* 2. Notification Bell */}
      <div className="relative" ref={notifRef}>
        <button 
          onClick={() => setIsNotifOpen(!isNotifOpen)}
          className="relative p-2.5 text-gray-500 hover:text-blue-900 hover:bg-gray-50 rounded-xl transition"
        >
          <Bell size={20} />
          {unreadCount > 0 && (
            <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white"></span>
          )}
        </button>

        {isNotifOpen && (
          <div className="absolute right-0 top-14 w-96 bg-white rounded-xl shadow-2xl border border-gray-200 z-50 overflow-hidden">
            <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
              <h3 className="font-bold text-slate-900 text-sm">Notifications</h3>
              {unreadCount > 0 && (
                <button onClick={markAllAsRead} className="text-[11px] font-semibold text-blue-900 hover:text-blue-800 flex items-center gap-1 bg-white px-2.5 py-1 rounded-md border border-gray-200 shadow-sm transition">
                  <Check size={12} /> Mark all read
                </button>
              )}
            </div>
            <div className="max-h-[450px] overflow-y-auto">
              {notifications.length > 0 ? (
                notifications.map((notif) => {
                  const isRead = readIds.includes(notif.id);
                  return (
                    <div key={notif.id} onClick={() => !isRead && markAsRead(notif.id)} className={`p-4 border-b border-gray-50 transition cursor-pointer ${isRead ? 'bg-white' : 'bg-blue-50/40 hover:bg-blue-50'}`}>
                      <div className="flex gap-3">
                        <div className={`mt-0.5 w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${notif.severity === 'high' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-900'}`}>
                          {notif.severity === 'high' ? <AlertCircle size={16} /> : <Calendar size={16} />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <p className={`text-xs font-bold mb-0.5 ${isRead ? 'text-gray-700' : 'text-slate-900'}`}>{notif.title}</p>
                            {!isRead && <div className="w-2 h-2 rounded-full bg-blue-900 flex-shrink-0 mt-1.5"></div>}
                          </div>
                          <p className="text-[11px] text-gray-500 leading-snug">{notif.message}</p>
                          <p className="text-[10px] text-gray-400 mt-1.5 font-medium">{notif.date}</p>
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="p-10 text-center">
                  <Bell size={28} className="mx-auto text-gray-300 mb-3" />
                  <p className="text-xs text-gray-500 font-medium">All caught up!</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
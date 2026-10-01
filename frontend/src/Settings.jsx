import { useState, useEffect } from 'react';
import api from './api';
import toast from 'react-hot-toast';
import { Calendar, CheckCircle, AlertCircle } from 'lucide-react';

export default function Settings() {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('calendar_connected') === 'true') {
      setIsConnected(true);
      toast.success("Google Calendar connected successfully!");
    }
  }, []);

  const handleConnect = async () => {
    try {
      const res = await api.get('/calendar/connect');
      window.location.href = res.data.auth_url; 
    } catch (error) {
      toast.error("Failed to generate login link. Is client_secret.json in the backend folder?");
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Settings</h1>
      <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <Calendar size={20} className="text-blue-900" /> Google Calendar Integration
        </h2>
        
        {isConnected ? (
          <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
            <CheckCircle size={20} />
            <div>
              <p className="font-semibold">Connected</p>
              <p className="text-sm">Your project deadlines will automatically sync to your Google Calendar.</p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3 p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <AlertCircle size={20} className="text-gray-500" />
            <div className="flex-1">
              <p className="font-semibold text-slate-900">Not Connected</p>
              <p className="text-sm text-gray-600 mb-3">Connect your Google account to automatically add and remove deadline reminders.</p>
              <button onClick={handleConnect} className="px-4 py-2 bg-blue-900 text-white rounded-lg hover:bg-blue-800 transition text-sm font-medium">
                Connect Google Calendar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
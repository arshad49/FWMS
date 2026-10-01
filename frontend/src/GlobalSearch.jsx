import { useState, useEffect, useRef, Fragment } from 'react';
import { useNavigate } from 'react-router-dom';
import { Dialog, Transition } from '@headlessui/react';
import { Search, Users, FolderKanban, FileText, Receipt } from 'lucide-react';
import api from './api';

export default function GlobalSearch({ isOpen, setIsOpen }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const navigate = useNavigate();
  const inputRef = useRef(null);

  // Listen for Cmd+K to open it even if not clicked
  useEffect(() => {
    function handleKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [setIsOpen]);

  // Auto-focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery('');
      setResults([]);
    }
  }, [isOpen]);

  useEffect(() => {
    if (query.length < 2) { setResults([]); return; }
    const search = async () => {
      try {
        const [clients, projects, quotes, invoices] = await Promise.all([
          api.get('/clients'), api.get('/projects'), api.get('/quotes'), api.get('/invoices')
        ]);
        const allResults = [
          ...clients.data.filter(c => c.name.toLowerCase().includes(query.toLowerCase())).map(c => ({ type: 'Client', title: c.name, subtitle: c.company || 'No company', path: `/clients/${c.id}`, icon: Users })),
          ...projects.data.filter(p => p.name.toLowerCase().includes(query.toLowerCase())).map(p => ({ type: 'Project', title: p.name, subtitle: p.client_name || 'Unknown', path: `/projects/${p.id}`, icon: FolderKanban })),
          ...quotes.data.filter(q => q.quote_number.toLowerCase().includes(query.toLowerCase())).map(q => ({ type: 'Quote', title: q.quote_number, subtitle: q.client_name || 'Unknown', path: '/quotes', icon: FileText })),
          ...invoices.data.filter(i => i.invoice_number.toLowerCase().includes(query.toLowerCase())).map(i => ({ type: 'Invoice', title: i.invoice_number, subtitle: i.client_name || 'Unknown', path: '/invoices', icon: Receipt })),
        ];
        setResults(allResults.slice(0, 8));
      } catch (error) { setResults([]); }
    };
    const timeout = setTimeout(search, 300);
    return () => clearTimeout(timeout);
  }, [query]);

  const handleSelect = (item) => {
    navigate(item.path);
    setIsOpen(false);
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-[100]" onClose={() => setIsOpen(false)}>
        <Transition.Child as={Fragment} enter="ease-out duration-200" enterFrom="opacity-0" enterTo="opacity-100" leave="ease-in duration-150" leaveFrom="opacity-100" leaveTo="opacity-0">
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        </Transition.Child>
        
        <div className="fixed inset-0 flex items-start justify-center pt-[20vh]">
          <Transition.Child as={Fragment} enter="ease-out duration-200" enterFrom="opacity-0 scale-95" enterTo="opacity-100 scale-100" leave="ease-in duration-150" leaveFrom="opacity-100 scale-100" leaveTo="opacity-0 scale-95">
            <Dialog.Panel className="w-full max-w-xl bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
              <div className="flex items-center gap-3 px-5 py-4 bg-gray-50 border-b border-gray-200">
                <Search size={20} className="text-gray-400 flex-shrink-0" />
                <input
                  ref={inputRef}
                  type="text"
                  placeholder="Type to search..."
                  className="flex-1 bg-transparent outline-none text-base text-slate-900 placeholder:text-gray-400 font-medium"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  autoComplete="off"
                />
                <kbd className="hidden sm:inline-block px-2 py-1 bg-white border border-gray-200 rounded text-[10px] font-mono text-gray-500 shadow-sm">ESC</kbd>
              </div>
              <div className="max-h-96 overflow-y-auto bg-white">
                {results.length > 0 ? (
                  <ul className="p-2">
                    {results.map((item, i) => {
                      const Icon = item.icon;
                      return (
                        <li key={i}>
                          <button onClick={() => handleSelect(item)} className="w-full flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-blue-50 transition text-left group">
                            <div className="w-10 h-10 rounded-lg bg-gray-100 group-hover:bg-blue-100 flex items-center justify-center transition flex-shrink-0">
                              <Icon size={18} className="text-gray-500 group-hover:text-blue-900 transition" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-bold text-slate-900 truncate">{item.title}</p>
                              <p className="text-xs text-gray-500 truncate">{item.subtitle}</p>
                            </div>
                            <span className="text-[10px] uppercase tracking-wider font-bold text-gray-400 bg-gray-100 group-hover:bg-white px-2 py-1 rounded">{item.type}</span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                ) : query.length >= 2 ? (
                  <div className="p-10 text-center text-sm text-gray-500">No results found for "{query}"</div>
                ) : (
                  <div className="p-10 text-center text-sm text-gray-400">Start typing to search across your CRM...</div>
                )}
              </div>
            </Dialog.Panel>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition>
  );
}
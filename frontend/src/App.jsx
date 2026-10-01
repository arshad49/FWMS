import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AnimatePresence, motion } from 'framer-motion';
import { useState } from 'react';

import Sidebar from './Sidebar';
import Topbar from './Topbar';
import GlobalSearch from './GlobalSearch';

import Dashboard from './Dashboard';
import Clients from './Clients';
import ClientDetail from './ClientDetail';
import Projects from './Projects';
import Tasks from './Tasks';
import Quotes from './Quotes';
import Invoices from './Invoices';
import Settings from './Settings';
import CreateQuote from './pages/CreateQuote';
import EditQuote from './pages/EditQuote';
import ProjectDetails from "./pages/ProjectDetails";
const pageVariants = {
  initial: { opacity: 0, y: 15 },
  in: { opacity: 1, y: 0 },
  out: { opacity: 0, y: -15 }
};

const pageTransition = { type: "tween", ease: "easeOut", duration: 0.25 };

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        variants={pageVariants}
        initial="initial"
        animate="in"
        exit="out"
        transition={pageTransition}
        className="w-full h-full"
      >
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/clients" element={<Clients />} />
          <Route path="/clients/:id" element={<ClientDetail />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:id" element={<ProjectDetails />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/quotes" element={<Quotes />} />
          <Route path="/quotes/new" element={<CreateQuote />} />
          <Route path="/invoices" element={<Invoices />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/quotes/edit/:quoteNumber" element={<EditQuote />} />
          <Route path="/projects/:id" element={<ProjectDetails />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

export default function App() {
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  return (
    <Router>
      <div className="flex h-screen bg-gray-50 overflow-hidden">
        <Toaster position="top-right" toastOptions={{ style: { borderRadius: '10px', border: '1px solid #e2e8f0' } }} />
        
        <GlobalSearch isOpen={isSearchOpen} setIsOpen={setIsSearchOpen} />

        <Sidebar />
        
        <div className="flex-1 flex flex-col min-w-0">
          <Topbar onSearchClick={() => setIsSearchOpen(true)} />
          
          <main className="flex-1 overflow-auto relative">
            <AnimatedRoutes />
          </main>
        </div>
      </div>
    </Router>
  );
}
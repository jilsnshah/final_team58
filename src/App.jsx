import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import ReportPage from './pages/ReportPage';
import ProjectsPage from './pages/ProjectsPage';
import * as api from './services/api';
import { ThemeContext } from './context/ThemeContext';
import './index.css';

function AppContent() {
  const [theme, setTheme] = React.useState('dark'); // 'dark' or 'light'
  const navigate = useNavigate();
  const lastThemeChangeRef = React.useRef(0);

  const toggleTheme = async () => {
    try {
      // Debounce to prevent rapid double-clicks
      const now = Date.now();
      if (now - lastThemeChangeRef.current < 500) {
        console.log('⏱️ Theme change debounced (too fast)');
        return;
      }
      lastThemeChangeRef.current = now;

      // Call backend to broadcast theme change to all connected clients
      await api.changeTheme();
      console.log('🎨 Theme change request sent to backend');
      // The actual theme toggle will happen when we receive the WebSocket event
    } catch (error) {
      console.error('❌ Failed to call backend theme change:', error);
      // Fallback to local theme change if backend call fails
      setTheme(prev => prev === 'dark' ? 'light' : 'dark');
    }
  };

  React.useEffect(() => {
    // Initialize WebSocket and listen for frontend action commands
    try {
      console.log('🔌 Initializing WebSocket connection...');
      api.initWebSocket();

      let themeChangeTimeout = null;

      // Listen for theme change commands
      api.onDataUpdate('change_theme', (data) => {
        console.log('🎨 THEME CHANGE EVENT RECEIVED!', data);
        
        // Debounce to prevent double-processing if event fires multiple times
        if (themeChangeTimeout) {
          console.log('⏱️ Ignoring duplicate theme change event');
          return;
        }
        
        // Toggle theme state directly (not calling toggleTheme to avoid infinite loop)
        setTheme(prev => {
          const newTheme = prev === 'dark' ? 'light' : 'dark';
          console.log(`✅ Theme toggled: ${prev} → ${newTheme}`);
          return newTheme;
        });
        
        // Set timeout to allow next theme change after 500ms
        themeChangeTimeout = setTimeout(() => {
          themeChangeTimeout = null;
        }, 500);
      });

      // Listen for navigation commands
      api.onDataUpdate('navigate', (data) => {
        console.log('🧭 NAVIGATION EVENT RECEIVED!', data);
        if (data.action === 'projects') {
          console.log('📍 Navigating to /projects');
          navigate('/projects');
        } else if (data.action === 'project') {
          // Navigate to individual project detail page
          const projectId = data.project_id;
          console.log(`📍 Navigating to /report/${projectId}`);
          navigate(`/report/${projectId}`);
        } else if (data.action === 'company') {
          // Use ticker if available, otherwise fall back to company_name
          const urlId = data.ticker || data.company_name;
          console.log(`📍 Navigating to /report/${urlId}`);
          // Navigate to company report page
          navigate(`/report/${urlId}`);
        }
      });

      // Note: Watchlist events (add_to_watchlist, remove_from_watchlist) are handled
      // in Dashboard.jsx where the watchlist state is managed

      console.log('✅ All WebSocket event listeners registered');

    } catch (err) {
      console.error('❌ WebSocket setup error:', err);
    }
  }, [navigate]);

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      <div className={`min-h-screen ${theme === 'dark' ? 'bg-gray-50' : 'bg-white'}`}>
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/report/:id" element={<ReportPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
        </Routes>
      </div>
    </ThemeContext.Provider>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;

import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { DashboardIcon, PersonIcon, FileTextIcon, GearIcon, TargetIcon } from '@radix-ui/react-icons';
import Dashboard from './pages/Dashboard';
import Competitors from './pages/Competitors';
import Reports from './pages/Reports';

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="logo">
        <TargetIcon className="logo-icon" width={20} height={20} />
        <span>Competity</span>
      </div>
      
      <nav className="nav-links">
        <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <DashboardIcon width={16} height={16} />
          <span>Overview</span>
        </NavLink>
        <NavLink to="/competitors" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <PersonIcon width={16} height={16} />
          <span>Competitors</span>
        </NavLink>
        <NavLink to="/reports" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <FileTextIcon width={16} height={16} />
          <span>Reports</span>
        </NavLink>
      </nav>
      
      <div style={{ marginTop: 'auto' }}>
        <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <GearIcon width={16} height={16} />
          <span>Settings</span>
        </NavLink>
      </div>
    </aside>
  );
}

function App() {
  return (
    <Router>
      <div className="layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/competitors" element={<Competitors />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={
              <div className="flat-panel">
                <h2>Settings</h2>
                <p>System configuration panel coming soon.</p>
              </div>
            } />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

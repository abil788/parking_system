import { Link, useNavigate, useLocation } from 'react-router-dom';
import { logout } from '../utils/auth';

export default function Layout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <div className="min-h-screen flex bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 text-white">
        <div className="p-4">
          <h1 className="text-2xl font-bold">Parking System</h1>
          <p className="text-sm text-gray-400">v1.0.0</p>
        </div>
        
        <nav className="mt-8">
          <Link
            to="/dashboard"
            className={`block px-4 py-3 hover:bg-gray-700 ${
              isActive('/dashboard') ? 'bg-blue-600' : ''
            }`}
          >
            Dashboard
          </Link>
          <Link
            to="/cards"
            className={`block px-4 py-3 hover:bg-gray-700 ${
              isActive('/cards') ? 'bg-blue-600' : ''
            }`}
          >
            Cards Management
          </Link>
          <Link
            to="/logs"
            className={`block px-4 py-3 hover:bg-gray-700 ${
              isActive('/logs') ? 'bg-blue-600' : ''
            }`}
          >
            Access Logs
          </Link>
        </nav>

        <div className="absolute bottom-0 w-64 p-4 bg-gray-900">
          <div className="mb-2">
            <p className="text-sm font-semibold">{user.username}</p>
            <p className="text-xs text-gray-400">{user.role}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-full bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded"
          >
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
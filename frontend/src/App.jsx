import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { isAuthenticated } from './utils/auth';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Cards from './pages/Cards';
import Logs from './pages/Logs';
import Layout from './components/Layout';

// Protected Route Component
function PrivateRoute({ children }) {
  return isAuthenticated() ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Navigate to="/dashboard" />
            </PrivateRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/cards"
          element={
            <PrivateRoute>
              <Layout>
                <Cards />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/logs"
          element={
            <PrivateRoute>
              <Layout>
                <Logs />
              </Layout>
            </PrivateRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
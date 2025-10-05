import { useState, useEffect, useRef } from 'react';
import { getLogs, exportLogs } from '../services/api';

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    action: '',
    result: ''
  });
  const wsRef = useRef(null);

  useEffect(() => {
    loadLogs();
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [page, filters]);

  const connectWebSocket = () => {
    // WebSocket connection for real-time updates
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const newLog = JSON.parse(event.data);
      console.log('New log received:', newLog);
      
      // Add new log to the top if it matches current filters
      if (matchesFilters(newLog)) {
        setLogs(prevLogs => [newLog, ...prevLogs]);
      }
      
      // Show notification
      showNotification(newLog);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Reconnect after 5 seconds
      setTimeout(connectWebSocket, 5000);
    };
    
    wsRef.current = ws;
  };

  const matchesFilters = (log) => {
    if (filters.action && log.action !== filters.action) return false;
    if (filters.result && log.result !== filters.result) return false;
    
    const logDate = new Date(log.timestamp).toISOString().split('T')[0];
    if (filters.start_date && logDate < filters.start_date) return false;
    if (filters.end_date && logDate > filters.end_date) return false;
    
    return true;
  };

  const showNotification = (log) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('New Access Event', {
        body: `${log.card_uid || 'Unknown'} - ${log.result.toUpperCase()}`,
        icon: log.result === 'granted' ? '✓' : '✗'
      });
    }
  };

  const requestNotificationPermission = () => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  };

  const loadLogs = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: 20, ...filters };
      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (params[key] === '') delete params[key];
      });

      const response = await getLogs(params);
      setLogs(response.data.logs);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Error loading logs:', error);
      alert('Error loading logs');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const params = { ...filters };
      Object.keys(params).forEach(key => {
        if (params[key] === '') delete params[key];
      });

      const response = await exportLogs(params);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `access_logs_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      alert('Error exporting logs');
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(1);
  };

  const resetFilters = () => {
    const today = new Date().toISOString().split('T')[0];
    setFilters({
      start_date: today,
      end_date: today,
      action: '',
      result: ''
    });
    setPage(1);
  };

  const pageSize = 20;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="p-8 bg-gray-100 min-h-screen">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Access Logs</h1>
        <div className="flex gap-2">
          <button
            onClick={requestNotificationPermission}
            className="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded"
          >
            Enable Notifications
          </button>
          <button
            onClick={handleExport}
            className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Real-time indicator */}
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${wsRef.current?.readyState === 1 ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
          <span className="text-sm font-medium">
            {wsRef.current?.readyState === 1 ? 'Real-time updates active' : 'Connecting...'}
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              className="border rounded px-3 py-2 w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              className="border rounded px-3 py-2 w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Action</label>
            <select
              value={filters.action}
              onChange={(e) => handleFilterChange('action', e.target.value)}
              className="border rounded px-3 py-2 w-full"
            >
              <option value="">All Actions</option>
              <option value="enter">Enter</option>
              <option value="exit">Exit</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Result</label>
            <select
              value={filters.result}
              onChange={(e) => handleFilterChange('result', e.target.value)}
              className="border rounded px-3 py-2 w-full"
            >
              <option value="">All Results</option>
              <option value="granted">Granted</option>
              <option value="denied">Denied</option>
            </select>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadLogs}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Apply Filters
          </button>
          <button
            onClick={resetFilters}
            className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Card UID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Owner</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vehicle</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Result</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan="8" className="px-6 py-4 text-center">Loading...</td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan="8" className="px-6 py-4 text-center text-gray-500">No logs found</td></tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{log.card_uid || 'N/A'}</td>
                    <td className="px-6 py-4 text-sm">{log.owner_name || 'N/A'}</td>
                    <td className="px-6 py-4 text-sm">{log.vehicle_plate || 'N/A'}</td>
                    <td className="px-6 py-4 text-sm">{log.reader_location || 'N/A'}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded ${
                        log.action === 'enter' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
                      }`}>{log.action}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded ${
                        log.result === 'granted' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>{log.result}</span>
                    </td>
                    <td className="px-6 py-4 text-sm">{log.reason || '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 flex justify-between items-center border-t">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-50"
            >Previous</button>
            <span>Page {page} of {totalPages}</span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1 border rounded hover:bg-gray-100 disabled:opacity-50"
            >Next</button>
          </div>
        )}
      </div>
    </div>
  );
}
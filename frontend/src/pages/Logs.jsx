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
  const [appliedFilters, setAppliedFilters] = useState(filters);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // WebSocket connection - TERPISAH dari filters
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []); // Empty dependency - hanya connect sekali

  // Load logs only when appliedFilters or page changes
  useEffect(() => {
    loadLogs();
  }, [page, appliedFilters]);

  const connectWebSocket = () => {
    try {
      // Sesuaikan dengan backend URL Anda
      const ws = new WebSocket('ws://localhost:8000/ws');
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
      };
      
      ws.onmessage = (event) => {
        try {
          const newLog = JSON.parse(event.data);
          console.log('📨 New log received:', newLog);
          
          // LANGSUNG tambahkan ke state jika cocok dengan filter
          if (matchesAppliedFilters(newLog)) {
            setLogs(prevLogs => {
              // Cek duplikat berdasarkan ID atau timestamp + card_uid
              const isDuplicate = prevLogs.some(log => 
                log.id === newLog.id || 
                (log.timestamp === newLog.timestamp && log.card_uid === newLog.card_uid)
              );
              
              if (!isDuplicate) {
                return [newLog, ...prevLogs];
              }
              return prevLogs;
            });
            
            setTotal(prev => prev + 1);
          }
          
          // Show notification
          showNotification(newLog);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setIsConnected(false);
      };
      
      ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);
        
        // Auto-reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('🔄 Attempting to reconnect...');
          connectWebSocket();
        }, 3000);
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setIsConnected(false);
      
      // Retry connection
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 3000);
    }
  };

  const matchesAppliedFilters = (log) => {
    if (appliedFilters.action && log.action !== appliedFilters.action) return false;
    if (appliedFilters.result && log.result !== appliedFilters.result) return false;
    
    const logDate = new Date(log.timestamp).toISOString().split('T')[0];
    if (appliedFilters.start_date && logDate < appliedFilters.start_date) return false;
    if (appliedFilters.end_date && logDate > appliedFilters.end_date) return false;
    
    return true;
  };

  const showNotification = (log) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('New Access Event', {
        body: `${log.card_uid || 'Unknown'} - ${log.action} - ${log.result.toUpperCase()}`,
        icon: log.result === 'granted' ? '✅' : '❌',
        tag: 'parking-access', // Prevent duplicate notifications
        requireInteraction: false
      });
    }
  };

  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      if (Notification.permission === 'default') {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
          alert('Notifications enabled! You will receive real-time alerts.');
        }
      } else if (Notification.permission === 'denied') {
        alert('Notifications are blocked. Please enable them in browser settings.');
      } else {
        alert('Notifications are already enabled!');
      }
    } else {
      alert('This browser does not support notifications.');
    }
  };

  const loadLogs = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: 20, ...appliedFilters };
      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (params[key] === '') delete params[key];
      });

      const response = await getLogs(params);
      setLogs(response.data.logs);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Error loading logs:', error);
      alert('Error loading logs: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const params = { ...appliedFilters };
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
      alert('Error exporting logs: ' + error.message);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    // TIDAK langsung load logs atau set appliedFilters
  };

  const applyFilters = () => {
    setAppliedFilters(filters);
    setPage(1);
    // loadLogs akan otomatis dipanggil karena appliedFilters berubah
  };

  const resetFilters = () => {
    const today = new Date().toISOString().split('T')[0];
    const newFilters = {
      start_date: today,
      end_date: today,
      action: '',
      result: ''
    };
    setFilters(newFilters);
    setAppliedFilters(newFilters);
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
            className="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded transition"
          >
            Enable Notifications
          </button>
          <button
            onClick={handleExport}
            className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded transition"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Real-time indicator - IMPROVED */}
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
          <span className="text-sm font-medium">
            {isConnected ? '✅ Real-time updates active' : '⚠️ Connecting to server...'}
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
              className="border rounded px-3 py-2 w-full focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              className="border rounded px-3 py-2 w-full focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Action</label>
            <select
              value={filters.action}
              onChange={(e) => handleFilterChange('action', e.target.value)}
              className="border rounded px-3 py-2 w-full focus:ring-2 focus:ring-blue-500"
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
              className="border rounded px-3 py-2 w-full focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Results</option>
              <option value="granted">Granted</option>
              <option value="denied">Denied</option>
            </select>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={applyFilters}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition"
          >
            Apply Filters
          </button>
          <button
            onClick={resetFilters}
            className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded transition"
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Card UID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Owner</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vehicle</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Result</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reason</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan="8" className="px-6 py-4 text-center">
                  <div className="flex justify-center items-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                  </div>
                </td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan="8" className="px-6 py-4 text-center text-gray-500">No logs found</td></tr>
              ) : (
                logs.map((log, index) => (
                  <tr 
                    key={log.id || index} 
                    className="hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">{log.card_uid || 'N/A'}</td>
                    <td className="px-6 py-4 text-sm">{log.owner_name || 'N/A'}</td>
                    <td className="px-6 py-4 text-sm">{log.vehicle_plate || 'N/A'}</td>
                    <td className="px-6 py-4 text-sm">{log.reader_location || 'N/A'}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded font-medium ${
                        log.action === 'enter' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
                      }`}>{log.action}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs rounded font-medium ${
                        log.result === 'granted' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>{log.result}</span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">{log.reason || '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 flex justify-between items-center border-t bg-gray-50">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 border rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              Previous
            </button>
            <span className="text-sm text-gray-700">
              Page <span className="font-medium">{page}</span> of <span className="font-medium">{totalPages}</span>
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-4 py-2 border rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
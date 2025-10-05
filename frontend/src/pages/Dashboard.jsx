import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { getCards, getLogs } from '../services/api';

const StatCard = ({ title, value, color, icon }) => (
  <div className="bg-white p-6 rounded-lg shadow">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-gray-500 text-sm font-semibold mb-2">{title}</p>
        <p className={`text-3xl font-bold ${color}`}>{value}</p>
      </div>
      <div className={`text-4xl ${color}`}>{icon}</div>
    </div>
  </div>
);

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalCards: 0,
    activeCards: 0,
    todayEntries: 0,
    deniedAccess: 0
  });
  
  const [hourlyData, setHourlyData] = useState([]);
  const [statusData, setStatusData] = useState([]);
  const [recentLogs, setRecentLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      // Load cards stats
      const cardsRes = await getCards({ page: 1, page_size: 1 });
      const activeRes = await getCards({ status: 'active', page: 1, page_size: 1 });

      // Load today's logs
      const today = new Date().toISOString().split('T')[0];
      const logsRes = await getLogs({ start_date: today, page: 1, page_size: 100 });
      const logs = logsRes.data.logs;
      
      // Calculate stats
      const entries = logs.filter(log => log.action === 'enter').length;
      const denied = logs.filter(log => log.result === 'denied').length;

      setStats({
        totalCards: cardsRes.data.total,
        activeCards: activeRes.data.total,
        todayEntries: entries,
        deniedAccess: denied
      });

      // Process hourly data
      setHourlyData(processHourlyData(logs));

      // Process status data
      setStatusData([
        { name: 'Granted', value: logs.filter(l => l.result === 'granted').length, color: '#10b981' },
        { name: 'Denied', value: denied, color: '#ef4444' }
      ]);

      setRecentLogs(logs.slice(0, 10));
      setLoading(false);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setLoading(false);
    }
  };

  const processHourlyData = (logs) => {
    const hours = Array.from({ length: 24 }, (_, i) => ({
      hour: `${i}:00`,
      entries: 0,
      exits: 0
    }));

    logs.forEach(log => {
      const hour = new Date(log.timestamp).getHours();
      if (log.action === 'enter') hours[hour].entries++;
      else hours[hour].exits++;
    });

    return hours.filter(h => h.entries > 0 || h.exits > 0);
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen"><div className="text-xl">Loading...</div></div>;
  }

  return (
    <div className="p-8 bg-gray-100 min-h-screen">
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard title="Total Cards" value={stats.totalCards} color="text-blue-600" icon="🎫" />
        <StatCard title="Active Cards" value={stats.activeCards} color="text-green-600" icon="✓" />
        <StatCard title="Today's Entries" value={stats.todayEntries} color="text-purple-600" icon="→" />
        <StatCard title="Access Denied" value={stats.deniedAccess} color="text-red-600" icon="✗" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Hourly Traffic</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={hourlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="entries" fill="#3b82f6" name="Entries" />
              <Bar dataKey="exits" fill="#8b5cf6" name="Exits" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">Access Results</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}`}
                outerRadius={100}
                dataKey="value"
              >
                {statusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Recent Access Logs</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Card UID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Owner</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vehicle</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Result</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recentLogs.length === 0 ? (
                <tr><td colSpan="6" className="px-6 py-4 text-center text-gray-500">No recent logs</td></tr>
              ) : (
                recentLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">{log.card_uid || 'N/A'}</td>
                    <td className="px-6 py-4 text-sm">{log.owner_name || 'N/A'}</td>
                    <td className="px-6 py-4 text-sm">{log.vehicle_plate || 'N/A'}</td>
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
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
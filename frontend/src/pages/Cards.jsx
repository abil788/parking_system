import { useState, useEffect } from 'react';
import { getCards, createCard, updateCard, deleteCard } from '../services/api';
import * as XLSX from 'xlsx';

export default function Cards() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingCard, setEditingCard] = useState(null);
  const [showBulkModal, setShowBulkModal] = useState(false);

  const [formData, setFormData] = useState({
    card_uid: '',
    owner_name: '',
    vehicle_plate: '',
    status: 'active',
    expires_at: '',
    notes: ''
  });

  useEffect(() => {
    loadCards();
  }, [page, search, statusFilter]);

  const loadCards = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: 10 };
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;

      const response = await getCards(params);
      setCards(response.data.cards);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Error loading cards:', error);
      alert('Error loading cards');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingCard) {
        await updateCard(editingCard.id, formData);
        alert('Card updated successfully!');
      } else {
        await createCard(formData);
        alert('Card created successfully!');
      }
      setShowModal(false);
      resetForm();
      loadCards();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error saving card');
    }
  };

  const handleEdit = (card) => {
    setEditingCard(card);
    setFormData({
      card_uid: card.card_uid,
      owner_name: card.owner_name,
      vehicle_plate: card.vehicle_plate,
      status: card.status,
      expires_at: card.expires_at ? card.expires_at.substring(0, 16) : '',
      notes: card.notes || ''
    });
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this card?')) return;
    try {
      await deleteCard(id);
      alert('Card deleted successfully!');
      loadCards();
    } catch (error) {
      alert('Error deleting card');
    }
  };

  const resetForm = () => {
    setEditingCard(null);
    setFormData({
      card_uid: '',
      owner_name: '',
      vehicle_plate: '',
      status: 'active',
      expires_at: '',
      notes: ''
    });
  };

  const handleBulkUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const data = await parseExcel(file);
      let success = 0;
      let failed = 0;

      for (const row of data) {
        try {
          await createCard({
            card_uid: row['Card UID'] || row['card_uid'],
            owner_name: row['Owner Name'] || row['owner_name'],
            vehicle_plate: row['Vehicle Plate'] || row['vehicle_plate'],
            status: row['Status'] || row['status'] || 'active',
            expires_at: row['Expires At'] || row['expires_at'] || null,
            notes: row['Notes'] || row['notes'] || ''
          });
          success++;
        } catch (error) {
          console.error('Error creating card:', error);
          failed++;
        }
      }

      alert(`Bulk upload complete!\nSuccess: ${success}\nFailed: ${failed}`);
      setShowBulkModal(false);
      loadCards();
    } catch (error) {
      alert('Error parsing Excel file');
    }
  };

  const parseExcel = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: 'array' });
          const sheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[sheetName];
          const jsonData = XLSX.utils.sheet_to_json(worksheet);
          resolve(jsonData);
        } catch (error) {
          reject(error);
        }
      };
      reader.onerror = () => reject(reader.error);
      reader.readAsArrayBuffer(file);
    });
  };

  const downloadTemplate = () => {
    const template = [
      {
        'Card UID': 'CARD001',
        'Owner Name': 'John Doe',
        'Vehicle Plate': 'B1234XYZ',
        'Status': 'active',
        'Expires At': '2025-12-31',
        'Notes': 'Mahasiswa'
      }
    ];
    
    const worksheet = XLSX.utils.json_to_sheet(template);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Cards');
    XLSX.writeFile(workbook, 'card_template.xlsx');
  };

  const pageSize = 10;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="p-8 bg-gray-100 min-h-screen">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Cards Management</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowBulkModal(true)}
            className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
          >
            Bulk Upload
          </button>
          <button
            onClick={() => { resetForm(); setShowModal(true); }}
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            + Add Card
          </button>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Search by UID, name, or plate..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="border rounded px-3 py-2"
          />
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="border rounded px-3 py-2"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="blocked">Blocked</option>
            <option value="lost">Lost</option>
          </select>
        </div>
      </div>

      {/* Cards Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Card UID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Owner</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vehicle</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expires</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr><td colSpan="6" className="px-6 py-4 text-center">Loading...</td></tr>
            ) : cards.length === 0 ? (
              <tr><td colSpan="6" className="px-6 py-4 text-center text-gray-500">No cards found</td></tr>
            ) : (
              cards.map((card) => (
                <tr key={card.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">{card.card_uid}</td>
                  <td className="px-6 py-4">{card.owner_name}</td>
                  <td className="px-6 py-4">{card.vehicle_plate}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs rounded ${
                      card.status === 'active' ? 'bg-green-100 text-green-800' :
                      card.status === 'blocked' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>{card.status}</span>
                  </td>
                  <td className="px-6 py-4">
                    {card.expires_at ? new Date(card.expires_at).toLocaleDateString() : 'Never'}
                  </td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => handleEdit(card)}
                      className="text-blue-600 hover:text-blue-900 mr-2"
                    >Edit</button>
                    <button
                      onClick={() => handleDelete(card.id)}
                      className="text-red-600 hover:text-red-900"
                    >Delete</button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

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

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
          <div className="bg-white p-5 rounded-md w-96">
            <h3 className="text-lg font-bold mb-4">{editingCard ? 'Edit Card' : 'Add Card'}</h3>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-sm font-bold mb-2">Card UID *</label>
                <input
                  type="text"
                  value={formData.card_uid}
                  onChange={(e) => setFormData({...formData, card_uid: e.target.value})}
                  className="shadow border rounded w-full py-2 px-3"
                  required
                  disabled={!!editingCard}
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-bold mb-2">Owner Name *</label>
                <input
                  type="text"
                  value={formData.owner_name}
                  onChange={(e) => setFormData({...formData, owner_name: e.target.value})}
                  className="shadow border rounded w-full py-2 px-3"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-bold mb-2">Vehicle Plate *</label>
                <input
                  type="text"
                  value={formData.vehicle_plate}
                  onChange={(e) => setFormData({...formData, vehicle_plate: e.target.value})}
                  className="shadow border rounded w-full py-2 px-3"
                  required
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-bold mb-2">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({...formData, status: e.target.value})}
                  className="shadow border rounded w-full py-2 px-3"
                >
                  <option value="active">Active</option>
                  <option value="blocked">Blocked</option>
                  <option value="lost">Lost</option>
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-sm font-bold mb-2">Expires At</label>
                <input
                  type="datetime-local"
                  value={formData.expires_at}
                  onChange={(e) => setFormData({...formData, expires_at: e.target.value})}
                  className="shadow border rounded w-full py-2 px-3"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-bold mb-2">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  className="shadow border rounded w-full py-2 px-3"
                  rows="3"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => { setShowModal(false); resetForm(); }}
                  className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
                >Cancel</button>
                <button
                  type="submit"
                  className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                >Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Upload Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
          <div className="bg-white p-5 rounded-md w-96">
            <h3 className="text-lg font-bold mb-4">Bulk Upload Cards</h3>
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Upload Excel file with card data</p>
              <button
                onClick={downloadTemplate}
                className="text-blue-600 hover:text-blue-900 text-sm mb-4"
              >Download Template</button>
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleBulkUpload}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
            <div className="flex justify-end">
              <button
                onClick={() => setShowBulkModal(false)}
                className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
              >Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
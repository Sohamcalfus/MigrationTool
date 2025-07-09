import React, { useState, useEffect } from 'react';
import { Database, RefreshCw, Trash2, CheckCircle, XCircle, Calendar, Filter } from 'lucide-react';

const MappingViewer = () => {
  const [mappings, setMappings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dbStatus, setDbStatus] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all');

  const checkDbStatus = async () => {
    try {
      const response = await fetch('http://localhost:5000/test-db');
      const data = await response.json();
      setDbStatus(data);
    } catch (error) {
      setDbStatus({ status: 'error', message: 'Cannot connect to database' });
    }
  };

  const fetchMappings = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/view-mappings');
      const data = await response.json();
      
      if (data.status === 'success') {
        setMappings(data.mappings);
      } else {
        alert('Error fetching mappings: ' + data.message);
      }
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const clearMappings = async () => {
    if (!window.confirm('Are you sure you want to clear all mappings? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch('http://localhost:5000/clear-mappings', {
        method: 'DELETE',
      });
      const data = await response.json();
      
      if (data.status === 'success') {
        alert(data.message);
        fetchMappings();
      } else {
        alert('Error: ' + data.message);
      }
    } catch (error) {
      alert('Error: ' + error.message);
    }
  };

  useEffect(() => {
    checkDbStatus();
    fetchMappings();
  }, []);

  const filteredMappings = mappings.filter(mapping => {
    if (filterStatus === 'all') return true;
    return mapping.status === filterStatus;
  });

  const groupedMappings = filteredMappings.reduce((groups, mapping) => {
    const date = mapping.created_at ? mapping.created_at.split(' ')[0] : 'Unknown';
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(mapping);
    return groups;
  }, {});

  const StatusBadge = ({ status }) => (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
      status === 'Y' 
        ? 'bg-green-100 text-green-800' 
        : 'bg-yellow-100 text-yellow-800'
    }`}>
      {status === 'Y' ? (
        <>
          <CheckCircle className="w-3 h-3 mr-1" />
          Mapped
        </>
      ) : (
        <>
          <XCircle className="w-3 h-3 mr-1" />
          Unmapped
        </>
      )}
    </span>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Database className="h-6 w-6 text-primary-600 mr-3" />
            <h2 className="text-2xl font-semibold text-gray-900">Column Mappings Database</h2>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={fetchMappings}
              disabled={loading}
              className="btn-secondary flex items-center"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={clearMappings}
              className="bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200 flex items-center"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear All
            </button>
          </div>
        </div>

        {/* Database Status */}
        <div className="mt-4">
          <div className={`p-4 rounded-lg border ${
            dbStatus?.status === 'success' 
              ? 'bg-green-50 border-green-200' 
              : 'bg-red-50 border-red-200'
          }`}>
            <div className="flex items-center">
              {dbStatus?.status === 'success' ? (
                <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
              ) : (
                <XCircle className="h-5 w-5 text-red-600 mr-2" />
              )}
              <span className={`font-medium ${
                dbStatus?.status === 'success' ? 'text-green-800' : 'text-red-800'
              }`}>
                Database Status: {dbStatus?.status === 'success' 
                  ? `Connected - ${dbStatus.table_count} total mappings` 
                  : dbStatus?.message || 'Unknown'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Controls */}
      <div className="card p-6">
        <div className="flex items-center mb-4">
          <Filter className="h-5 w-5 text-gray-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Filter by Status</h3>
        </div>
        <div className="flex space-x-2">
          {[
            { value: 'all', label: `All (${mappings.length})`, color: 'bg-gray-100 text-gray-800' },
            { value: 'Y', label: `Mapped (${mappings.filter(m => m.status === 'Y').length})`, color: 'bg-green-100 text-green-800' },
            { value: 'N', label: `Unmapped (${mappings.filter(m => m.status === 'N').length})`, color: 'bg-yellow-100 text-yellow-800' }
          ].map((filter) => (
            <button
              key={filter.value}
              onClick={() => setFilterStatus(filter.value)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                filterStatus === filter.value
                  ? 'bg-primary-600 text-white'
                  : filter.color + ' hover:opacity-80'
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      {/* Mappings Display */}
      {loading ? (
        <div className="card p-12">
          <div className="flex items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-primary-600 mr-3" />
            <span className="text-lg text-gray-600">Loading mappings...</span>
          </div>
        </div>
      ) : Object.keys(groupedMappings).length === 0 ? (
        <div className="card p-12">
          <div className="text-center">
            <Database className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No mappings found</h3>
            <p className="text-gray-600">Upload files using the "File Processing" tab to create mappings.</p>
          </div>
        </div>
      ) : (
        Object.entries(groupedMappings).map(([date, dateMappings]) => (
          <div key={date} className="card p-6">
            <div className="flex items-center mb-4">
              <Calendar className="h-5 w-5 text-primary-600 mr-2" />
              <h3 className="text-lg font-semibold text-gray-900">Session: {date}</h3>
              <span className="ml-auto text-sm text-gray-500">
                {dateMappings.length} mappings
              </span>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Template Column
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Raw Column
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Module
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created At
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {dateMappings.map((mapping) => (
                    <tr key={mapping.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-medium text-gray-900">{mapping.template_column}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {mapping.raw_column ? (
                          <span className="text-gray-900">{mapping.raw_column}</span>
                        ) : (
                          <span className="text-gray-400 italic">No mapping</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <StatusBadge status={mapping.status} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {mapping.fbdi_module}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {mapping.created_at}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))
      )}
    </div>
  );
};

export default MappingViewer;

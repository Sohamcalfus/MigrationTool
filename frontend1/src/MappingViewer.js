import React, { useState, useEffect } from "react";

const MappingViewer = () => {
  const [mappings, setMappings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dbStatus, setDbStatus] = useState(null);
  const [filterStatus, setFilterStatus] = useState("all"); // "all", "Y", "N"

  // Fetch database status
  const checkDbStatus = async () => {
    try {
      const response = await fetch("http://localhost:5000/test-db");
      const data = await response.json();
      setDbStatus(data);
    } catch (error) {
      setDbStatus({ status: "error", message: "Cannot connect to database" });
    }
  };

  // Fetch mappings from database
  const fetchMappings = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:5000/view-mappings");
      const data = await response.json();
      
      if (data.status === "success") {
        setMappings(data.mappings);
      } else {
        alert("Error fetching mappings: " + data.message);
      }
    } catch (error) {
      alert("Error: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Clear all mappings
  const clearMappings = async () => {
    if (!window.confirm("Are you sure you want to clear all mappings? This action cannot be undone.")) {
      return;
    }

    try {
      const response = await fetch("http://localhost:5000/clear-mappings", {
        method: "DELETE",
      });
      const data = await response.json();
      
      if (data.status === "success") {
        alert(data.message);
        fetchMappings(); // Refresh the list
      } else {
        alert("Error: " + data.message);
      }
    } catch (error) {
      alert("Error: " + error.message);
    }
  };

  useEffect(() => {
    checkDbStatus();
    fetchMappings();
  }, []);

  // Filter mappings based on status
  const filteredMappings = mappings.filter(mapping => {
    if (filterStatus === "all") return true;
    return mapping.status === filterStatus;
  });

  // Group mappings by created_at (session)
  const groupedMappings = filteredMappings.reduce((groups, mapping) => {
    const date = mapping.created_at ? mapping.created_at.split(' ')[0] : 'Unknown';
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(mapping);
    return groups;
  }, {});

  return (
    <div className="row">
      <div className="col-12">
        <div className="card">
          <div className="card-header d-flex justify-content-between align-items-center">
            <h3 className="card-title mb-0">Column Mappings Database</h3>
            <div>
              <button
                className="btn btn-outline-primary me-2"
                onClick={fetchMappings}
                disabled={loading}
              >
                {loading ? "Refreshing..." : "Refresh"}
              </button>
              <button
                className="btn btn-outline-danger"
                onClick={clearMappings}
              >
                Clear All
              </button>
            </div>
          </div>
          <div className="card-body">
            {/* Database Status */}
            <div className="mb-3">
              <div className={`alert ${dbStatus?.status === "success" ? "alert-success" : "alert-danger"}`}>
                <strong>Database Status:</strong> {dbStatus?.status === "success" 
                  ? `Connected - ${dbStatus.table_count} total mappings` 
                  : dbStatus?.message || "Unknown"}
              </div>
            </div>

            {/* Filter Controls */}
            <div className="mb-3">
              <label className="form-label">Filter by Status:</label>
              <div className="btn-group" role="group">
                <input
                  type="radio"
                  className="btn-check"
                  name="statusFilter"
                  id="filterAll"
                  value="all"
                  checked={filterStatus === "all"}
                  onChange={(e) => setFilterStatus(e.target.value)}
                />
                <label className="btn btn-outline-secondary" htmlFor="filterAll">
                  All ({mappings.length})
                </label>

                <input
                  type="radio"
                  className="btn-check"
                  name="statusFilter"
                  id="filterY"
                  value="Y"
                  checked={filterStatus === "Y"}
                  onChange={(e) => setFilterStatus(e.target.value)}
                />
                <label className="btn btn-outline-success" htmlFor="filterY">
                  Mapped (Y) ({mappings.filter(m => m.status === "Y").length})
                </label>

                <input
                  type="radio"
                  className="btn-check"
                  name="statusFilter"
                  id="filterN"
                  value="N"
                  checked={filterStatus === "N"}
                  onChange={(e) => setFilterStatus(e.target.value)}
                />
                <label className="btn btn-outline-warning" htmlFor="filterN">
                  Unmapped (N) ({mappings.filter(m => m.status === "N").length})
                </label>
              </div>
            </div>

            {/* Mappings Display */}
            {loading ? (
              <div className="text-center">
                <div className="spinner-border" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
              </div>
            ) : Object.keys(groupedMappings).length === 0 ? (
              <div className="alert alert-info">
                No mappings found. Upload files using the "File Upload" tab to create mappings.
              </div>
            ) : (
              Object.entries(groupedMappings).map(([date, dateMappings]) => (
                <div key={date} className="mb-4">
                  <h5 className="text-primary">Session: {date}</h5>
                  <div className="table-responsive">
                    <table className="table table-striped table-hover">
                      <thead className="table-dark">
                        <tr>
                          <th>ID</th>
                          <th>Template Column</th>
                          <th>Raw Column</th>
                          <th>Status</th>
                          <th>Module</th>
                          <th>Subset</th>
                          <th>Created At</th>
                        </tr>
                      </thead>
                      <tbody>
                        {dateMappings.map((mapping) => (
                          <tr key={mapping.id}>
                            <td>{mapping.id}</td>
                            <td>
                              <strong>{mapping.template_column}</strong>
                            </td>
                            <td>
                              {mapping.raw_column || (
                                <span className="text-muted">No mapping</span>
                              )}
                            </td>
                            <td>
                              <span
                                className={`badge ${
                                  mapping.status === "Y"
                                    ? "bg-success"
                                    : "bg-warning text-dark"
                                }`}
                              >
                                {mapping.status === "Y" ? "Mapped" : "Unmapped"}
                              </span>
                            </td>
                            <td>{mapping.fbdi_module}</td>
                            <td>{mapping.fbdi_subset}</td>
                            <td>{mapping.created_at}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MappingViewer;

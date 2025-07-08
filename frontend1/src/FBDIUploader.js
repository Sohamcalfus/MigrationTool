import React, { useState } from "react";

const FBDIUploader = () => {
  const [templateFile, setTemplateFile] = useState(null);
  const [rawFile, setRawFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processingMode, setProcessingMode] = useState("new"); // "new" or "fromTable"

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!templateFile || !rawFile) {
      alert("Please upload both files.");
      return;
    }

    const formData = new FormData();
    formData.append("template_file", templateFile);
    formData.append("raw_file", rawFile);

    setLoading(true);

    try {
      // Choose endpoint based on processing mode
      const endpoint = processingMode === "new" 
        ? "http://localhost:5000/generate-fbdi"
        : "http://localhost:5000/generate-fbdi-from-table";

      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to generate FBDI file");
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = processingMode === "new" 
        ? "fbdi_output.zip" 
        : "fbdi_output_from_table.zip";
      document.body.appendChild(a);
      a.click();
      a.remove();

      // Show success message
      alert(`FBDI file generated successfully using ${processingMode === "new" ? "new mapping" : "stored mappings"}!`);

    } catch (error) {
      alert("Error: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="row justify-content-center">
      <div className="col-md-8">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title mb-0">FBDI File Generator</h3>
          </div>
          <div className="card-body">
            {/* Processing Mode Selection */}
            <div className="mb-4">
              <label className="form-label fw-bold">Processing Mode:</label>
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="radio"
                  name="processingMode"
                  id="newMapping"
                  value="new"
                  checked={processingMode === "new"}
                  onChange={(e) => setProcessingMode(e.target.value)}
                />
                <label className="form-check-label" htmlFor="newMapping">
                  <strong>Create New Mapping</strong> - Discover and store new column mappings
                </label>
              </div>
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="radio"
                  name="processingMode"
                  id="fromTable"
                  value="fromTable"
                  checked={processingMode === "fromTable"}
                  onChange={(e) => setProcessingMode(e.target.value)}
                />
                <label className="form-check-label" htmlFor="fromTable">
                  <strong>Use Stored Mappings</strong> - Apply existing mappings from database
                </label>
              </div>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label htmlFor="templateFile" className="form-label">
                  Template File (.xlsm)
                </label>
                <input
                  type="file"
                  className="form-control"
                  id="templateFile"
                  accept=".xlsm"
                  onChange={(e) => setTemplateFile(e.target.files[0])}
                />
                {templateFile && (
                  <div className="form-text text-success">
                    ✓ Selected: {templateFile.name}
                  </div>
                )}
              </div>

              <div className="mb-3">
                <label htmlFor="rawFile" className="form-label">
                  Raw Data File (.xlsx)
                </label>
                <input
                  type="file"
                  className="form-control"
                  id="rawFile"
                  accept=".xlsx"
                  onChange={(e) => setRawFile(e.target.files[0])}
                />
                {rawFile && (
                  <div className="form-text text-success">
                    ✓ Selected: {rawFile.name}
                  </div>
                )}
              </div>

              <button
                type="submit"
                className="btn btn-primary w-100"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span
                      className="spinner-border spinner-border-sm me-2"
                      role="status"
                      aria-hidden="true"
                    ></span>
                    {processingMode === "new" ? "Creating Mapping & Generating..." : "Applying Mappings & Generating..."}
                  </>
                ) : (
                  processingMode === "new" ? "Generate FBDI with New Mapping" : "Generate FBDI from Stored Mappings"
                )}
              </button>
            </form>

            <div className="mt-3">
              <div className="alert alert-info">
                <strong>Mode Info:</strong>
                {processingMode === "new" ? (
                  <span> This will create new column mappings and store them in the database for future use.</span>
                ) : (
                  <span> This will use previously stored column mappings from the database. Make sure you have run the "Create New Mapping" mode at least once.</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FBDIUploader;

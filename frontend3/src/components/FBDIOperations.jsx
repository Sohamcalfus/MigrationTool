import React, { useState, useEffect } from "react";

const FBDIOperations = () => {
  const [loading, setLoading] = useState(false);
  const [selectedFbdiFile, setSelectedFbdiFile] = useState(null);
  const [businessUnit, setBusinessUnit] = useState('300000003170678');
  const [batchSource, setBatchSource] = useState('MILGARD EBS SPREADSHEET');
  const [glDate, setGlDate] = useState(new Date().toISOString().split('T')[0]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setSelectedFbdiFile(file);
    setResult(null);
    setError(null);
  };

  const handleProcessFBDI = async () => {
    if (!selectedFbdiFile) {
      alert("Please select an FBDI file first");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("fbdi_file", selectedFbdiFile);
      formData.append("business_unit", businessUnit);
      formData.append("batch_source", batchSource);
      formData.append("gl_date", glDate);

      console.log("📤 Uploading FBDI file:", selectedFbdiFile.name);
      console.log("📊 Parameters:", { businessUnit, batchSource, glDate });

      const response = await fetch("http://localhost:5000/fbdi/process-fbdi", {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
        console.log("✅ Workflow completed successfully:", data);
      } else {
        setError(data);
        console.error("❌ Workflow failed:", data);
      }
    } catch (err) {
      const errorData = {
        step: "network",
        error: err.message
      };
      setError(errorData);
      console.error("❌ Network error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFbdiFile(null);
    setResult(null);
    setError(null);
    // Reset file input
    const fileInput = document.getElementById('fbdi-file-input');
    if (fileInput) fileInput.value = '';
  };

  const getStepStatus = (step) => {
    if (error?.step === step) return "error";
    if (result) return "success";
    return "pending";
  };

  const getStepIcon = (step) => {
    const status = getStepStatus(step);
    switch (status) {
      case "success": return "✅";
      case "error": return "❌";
      default: return "⏳";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h1 className="text-3xl font-bold text-indigo-700 mb-2">
            🚀 FBDI Processing Center
          </h1>
          <p className="text-gray-600">
            Upload your FBDI file and process it through Oracle Cloud in one go
          </p>
          <button
            onClick={handleReset}
            className="mt-3 text-sm text-gray-500 hover:text-gray-700 underline"
          >
            🔄 Reset Form
          </button>
        </div>

        {/* Main Form */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-6">
            📁 Upload & Process FBDI
          </h2>

          {/* File Upload */}
          <div className="mb-6">
            <label className="block font-medium text-gray-700 mb-2">
              Select FBDI File (ZIP)
            </label>
            <input
              id="fbdi-file-input"
              type="file"
              accept=".zip"
              onChange={handleFileChange}
              className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            {selectedFbdiFile && (
              <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-700">
                  ✅ Selected: <strong>{selectedFbdiFile.name}</strong>
                </p>
                <p className="text-xs text-green-600">
                  Size: {(selectedFbdiFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
            )}
          </div>

          {/* Parameters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block font-medium text-gray-700 mb-2">
                Business Unit
              </label>
              <input
                type="text"
                value={businessUnit}
                onChange={(e) => setBusinessUnit(e.target.value)}
                className="w-full border-2 border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block font-medium text-gray-700 mb-2">
                Batch Source
              </label>
              <input
                type="text"
                value={batchSource}
                onChange={(e) => setBatchSource(e.target.value)}
                className="w-full border-2 border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block font-medium text-gray-700 mb-2">
                GL Date
              </label>
              <input
                type="date"
                value={glDate}
                onChange={(e) => setGlDate(e.target.value)}
                className="w-full border-2 border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          {/* Process Button */}
          <button
            onClick={handleProcessFBDI}
            disabled={loading || !selectedFbdiFile}
            className={`w-full px-6 py-4 rounded-lg font-semibold text-lg transition-all duration-300 ${
              loading || !selectedFbdiFile
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white transform hover:scale-105"
            }`}
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 818-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing FBDI Workflow...
              </span>
            ) : (
              "🚀 Process FBDI (Upload → Interface → AutoInvoice)"
            )}
          </button>
        </div>

        {/* Workflow Progress */}
        {(loading || result || error) && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-6">
              📊 Workflow Progress
            </h2>

            <div className="space-y-4">
              {/* Step 1: UCM Upload */}
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{getStepIcon("upload")}</span>
                <div className="flex-1">
                  <h3 className="font-medium text-gray-800">Step 1: Upload to UCM</h3>
                  <p className="text-sm text-gray-600">Uploading FBDI file to Oracle Content Management</p>
                </div>
                {result?.document_id && (
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    Doc ID: {result.document_id}
                  </span>
                )}
              </div>

              {/* Step 2: Interface Loader */}
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{getStepIcon("interface_submit")}</span>
                <div className="flex-1">
                  <h3 className="font-medium text-gray-800">Step 2: Interface Loader</h3>
                  <p className="text-sm text-gray-600">Loading data into Oracle interface tables</p>
                </div>
                {result?.interface_job_id && (
                  <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                    Job: {result.interface_job_id}
                  </span>
                )}
              </div>

              {/* Step 3: AutoInvoice Import */}
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{getStepIcon("autoinvoice_submit")}</span>
                <div className="flex-1">
                  <h3 className="font-medium text-gray-800">Step 3: AutoInvoice Import</h3>
                  <p className="text-sm text-gray-600">Creating invoice transactions from interface data</p>
                </div>
                {result?.autoinvoice_job_id && (
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                    Job: {result.autoinvoice_job_id}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Success Result */}
        {result && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-8">
            <h2 className="text-xl font-semibold text-green-800 mb-4">
              ✅ Workflow Completed Successfully!
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="font-medium text-green-800 mb-2">UCM Upload</h3>
                <div className="text-sm text-green-700 space-y-1">
                  <p><strong>Document ID:</strong> {result.document_id}</p>
                  <p><strong>Filename:</strong> {result.ucm_filename}</p>
                </div>
              </div>
              
              <div>
                <h3 className="font-medium text-green-800 mb-2">Interface Loader</h3>
                <div className="text-sm text-green-700 space-y-1">
                  <p><strong>Job ID:</strong> {result.interface_job_id}</p>
                  <p><strong>Status:</strong> {result.interface_status}</p>
                </div>
              </div>
              
              <div>
                <h3 className="font-medium text-green-800 mb-2">AutoInvoice Import</h3>
                <div className="text-sm text-green-700 space-y-1">
                  <p><strong>Job ID:</strong> {result.autoinvoice_job_id}</p>
                  <p><strong>Status:</strong> {result.autoinvoice_status}</p>
                </div>
              </div>
              
              <div>
                <h3 className="font-medium text-green-800 mb-2">Parameters Used</h3>
                <div className="text-sm text-green-700 space-y-1">
                  <p><strong>Business Unit:</strong> {businessUnit}</p>
                  <p><strong>Batch Source:</strong> {batchSource}</p>
                  <p><strong>GL Date:</strong> {glDate}</p>
                </div>
              </div>
            </div>

            {/* Generate Report Button */}
            <div className="mt-4 pt-4 border-t border-green-200">
              <button
                onClick={() => {
                  // Call your existing report generation endpoint
                  fetch("http://localhost:5000/generate-execution-report", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ 
                      autoinvoice_request_id: result.autoinvoice_job_id 
                    })
                  })
                  .then(response => response.blob())
                  .then(blob => {
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `AutoInvoice_Report_${result.autoinvoice_job_id}.pdf`;
                    a.click();
                    URL.revokeObjectURL(url);
                  })
                  .catch(err => alert("Error generating report: " + err.message));
                }}
                className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium"
              >
                📊 Generate Execution Report
              </button>
            </div>
          </div>
        )}

        {/* Error Result */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
            <h2 className="text-xl font-semibold text-red-800 mb-4">
              ❌ Workflow Failed
            </h2>
            
            <div className="space-y-3">
              <div>
                <h3 className="font-medium text-red-800">Failed at: {error.step}</h3>
                <p className="text-sm text-red-700 mt-1">
                  {typeof error.error === 'string' ? error.error : JSON.stringify(error.error)}
                </p>
              </div>
              
              {error.job_id && (
                <div>
                  <h4 className="font-medium text-red-800">Job Details:</h4>
                  <div className="text-sm text-red-700">
                    <p><strong>Job ID:</strong> {error.job_id}</p>
                    {error.status && <p><strong>Status:</strong> {error.status}</p>}
                  </div>
                </div>
              )}
            </div>

            <div className="mt-4 pt-4 border-t border-red-200">
              <button
                onClick={handleReset}
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium"
              >
                🔄 Try Again
              </button>
            </div>
          </div>
        )}

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-blue-800 mb-3">
            ℹ️ How it works
          </h2>
          <ul className="text-sm text-blue-700 space-y-2">
            <li>• <strong>Step 1:</strong> Your FBDI file is uploaded to Oracle UCM</li>
            <li>• <strong>Step 2:</strong> Interface Loader processes the file into Oracle interface tables</li>
            <li>• <strong>Step 3:</strong> AutoInvoice Import creates actual invoice transactions</li>
            <li>• Each step waits for the previous one to complete successfully</li>
            <li>• You can generate execution reports after completion</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default FBDIOperations;

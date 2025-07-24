import React, { useState } from 'react';
import { Upload, Download, FileText, CheckCircle, XCircle, AlertCircle, BarChart3, Clock } from 'lucide-react';

const ReconReport = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect({ target: { files: e.dataTransfer.files } });
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      const allowedTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel'
      ];
      
      if (!allowedTypes.includes(file.type) && !file.name.toLowerCase().endsWith('.xlsx') && !file.name.toLowerCase().endsWith('.xls')) {
        setError('Please select a valid Excel file (.xlsx or .xls)');
        return;
      }
      
      setSelectedFile(file);
      setError(null);
      setResult(null);
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedFile) {
      setError('Please select a raw file first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('rawFile', selectedFile);

      const response = await fetch('http://localhost:5000/reconreport/generate', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        setResult(data);
      } else {
        setError(data.error || 'Failed to generate reconciliation report');
      }
    } catch (err) {
      setError(`Network error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!result?.download_url) return;

    try {
      const response = await fetch(`http://localhost:5000${result.download_url}`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = result.filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError('Failed to download file');
      }
    } catch (err) {
      setError(`Download error: ${err.message}`);
    }
  };

  const resetForm = () => {
    setSelectedFile(null);
    setResult(null);
    setError(null);
    // Reset file input
    const fileInput = document.getElementById('rawFileInput');
    if (fileInput) fileInput.value = '';
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <BarChart3 className="w-8 h-8 text-white" />
                </div>
              </div>
              <div className="ml-6">
                <h1 className="text-3xl font-bold text-gray-900">Reconciliation Report Generator</h1>
                <p className="text-lg text-gray-600 mt-2">
                  Generate comprehensive reconciliation reports by comparing raw data with Oracle Cloud reports
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* File Upload Section */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
              <div className="mb-6">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">Upload Raw Data File</h2>
                <p className="text-gray-600">Select your Excel file containing the raw invoice data for reconciliation</p>
              </div>
              
              <div className="space-y-6">
                {/* Drag & Drop Area */}
                <div
                  className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
                    dragActive
                      ? 'border-blue-400 bg-blue-50'
                      : selectedFile
                      ? 'border-green-400 bg-green-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <input
                    id="rawFileInput"
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={handleFileSelect}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  
                  <div className="space-y-4">
                    {selectedFile ? (
                      <>
                        <CheckCircle className="w-12 h-12 text-green-500 mx-auto" />
                        <div>
                          <p className="text-lg font-medium text-green-700">{selectedFile.name}</p>
                          <p className="text-sm text-green-600">
                            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • Ready to process
                          </p>
                        </div>
                      </>
                    ) : (
                      <>
                        <Upload className="w-12 h-12 text-gray-400 mx-auto" />
                        <div>
                          <p className="text-lg font-medium text-gray-700">
                            Drag and drop your Excel file here
                          </p>
                          <p className="text-sm text-gray-500">
                            or click to browse (.xlsx, .xls files only)
                          </p>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex justify-between items-center">
                  <button
                    onClick={resetForm}
                    disabled={loading}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                  >
                    Reset
                  </button>
                  
                  <button
                    onClick={handleGenerateReport}
                    disabled={loading || !selectedFile}
                    className={`inline-flex items-center px-8 py-3 rounded-lg font-semibold text-white transition-all duration-200 ${
                      loading || !selectedFile
                        ? "bg-gray-400 cursor-not-allowed"
                        : "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                    }`}
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Generating...
                      </>
                    ) : (
                      <>
                        <BarChart3 className="w-5 h-5 mr-2" />
                        Generate Report
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Results Section */}
            {result && result.status === 'success' && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
                <div className="flex items-center mb-6">
                  <CheckCircle className="w-8 h-8 text-green-500 mr-3" />
                  <div>
                    <h3 className="text-2xl font-semibold text-gray-900">Report Generated Successfully</h3>
                    <p className="text-gray-600">Your reconciliation report is ready for download</p>
                  </div>
                </div>
                
                {/* Statistics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                  <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl p-6">
                    <div className="text-3xl font-bold text-gray-900">{result.total_records}</div>
                    <div className="text-sm text-gray-600 mt-1">Total Records Processed</div>
                  </div>
                  <div className="bg-gradient-to-r from-green-50 to-emerald-100 rounded-xl p-6">
                    <div className="text-3xl font-bold text-green-600">{result.matched_records}</div>
                    <div className="text-sm text-gray-600 mt-1">Successfully Matched</div>
                  </div>
                  <div className="bg-gradient-to-r from-blue-50 to-cyan-100 rounded-xl p-6">
                    <div className="text-3xl font-bold text-blue-600">{result.match_percentage}%</div>
                    <div className="text-sm text-gray-600 mt-1">Match Accuracy Rate</div>
                  </div>
                </div>

                {/* Download Section */}
                <div className="flex items-center justify-between p-6 bg-gray-50 rounded-xl">
                  <div className="flex items-center">
                    <FileText className="w-8 h-8 text-blue-500 mr-4" />
                    <div>
                      <div className="text-lg font-semibold text-gray-900">{result.filename}</div>
                      <div className="text-sm text-gray-600">Excel Reconciliation Report</div>
                    </div>
                  </div>
                  <button
                    onClick={handleDownload}
                    className="inline-flex items-center px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    Download Report
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            
            {/* Status Card */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Process Status</h3>
              <div className="space-y-3">
                <div className={`flex items-center p-3 rounded-lg ${selectedFile ? 'bg-green-50' : 'bg-gray-50'}`}>
                  {selectedFile ? (
                    <CheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  ) : (
                    <div className="w-5 h-5 border-2 border-gray-300 rounded-full mr-3" />
                  )}
                  <span className={`text-sm font-medium ${selectedFile ? 'text-green-700' : 'text-gray-600'}`}>
                    File Selected
                  </span>
                </div>
                
                <div className={`flex items-center p-3 rounded-lg ${loading ? 'bg-blue-50' : result ? 'bg-green-50' : 'bg-gray-50'}`}>
                  {loading ? (
                    <Clock className="w-5 h-5 text-blue-500 mr-3 animate-pulse" />
                  ) : result ? (
                    <CheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  ) : (
                    <div className="w-5 h-5 border-2 border-gray-300 rounded-full mr-3" />
                  )}
                  <span className={`text-sm font-medium ${loading ? 'text-blue-700' : result ? 'text-green-700' : 'text-gray-600'}`}>
                    {loading ? 'Processing...' : result ? 'Report Generated' : 'Processing Pending'}
                  </span>
                </div>
                
                <div className={`flex items-center p-3 rounded-lg ${result ? 'bg-green-50' : 'bg-gray-50'}`}>
                  {result ? (
                    <CheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  ) : (
                    <div className="w-5 h-5 border-2 border-gray-300 rounded-full mr-3" />
                  )}
                  <span className={`text-sm font-medium ${result ? 'text-green-700' : 'text-gray-600'}`}>
                    Ready to Download
                  </span>
                </div>
              </div>
            </div>

            {/* Help Card */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">How it Works</h3>
              <div className="space-y-3 text-sm text-gray-600">
                <div className="flex items-start">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                    <span className="text-xs font-semibold text-blue-600">1</span>
                  </div>
                  <p>Upload your raw Excel file containing invoice data</p>
                </div>
                <div className="flex items-start">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                    <span className="text-xs font-semibold text-blue-600">2</span>
                  </div>
                  <p>System fetches corresponding data from Oracle Cloud</p>
                </div>
                <div className="flex items-start">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                    <span className="text-xs font-semibold text-blue-600">3</span>
                  </div>
                  <p>Performs detailed comparison and generates report</p>
                </div>
                <div className="flex items-start">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                    <span className="text-xs font-semibold text-blue-600">4</span>
                  </div>
                  <p>Download Excel report with color-coded matches</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Loading Overlay */}
        {loading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-8 max-w-md w-full mx-4">
              <div className="flex items-center justify-center mb-4">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 text-center mb-2">
                Generating Reconciliation Report
              </h3>
              <p className="text-gray-600 text-center">
                Please wait while we process your data and generate the report. This may take a few minutes.
              </p>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="fixed bottom-4 right-4 bg-red-50 border border-red-200 rounded-lg p-4 shadow-lg max-w-md">
            <div className="flex items-center">
              <XCircle className="w-5 h-5 text-red-500 mr-3 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-medium text-red-800">Error</h4>
                <p className="text-sm text-red-700">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="ml-4 text-red-400 hover:text-red-600"
              >
                <XCircle className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReconReport;

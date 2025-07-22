import React, { useState, useEffect } from "react";
import { useFBDI } from "./FBDIGenerator3";

const FBDIOperations = () => {
  const {
    rawFile,
    setRawFile,
    selectedTemplate,
    setSelectedTemplate,
    projectName,
    setProjectName,
    envType,
    setEnvType,
    generatedFBDI,
    setGeneratedFBDI,
    uploadedFile,
    setUploadedFile,
    jobStatuses,
    setJobStatuses,
    processProgress,
    setProcessProgress,
    fbdiTemplates
  } = useFBDI();

  const [loading, setLoading] = useState({
    upload: false,
    interface: false,
    invoice: false,
    full: false,
    report: false,
    complete: false
  });

  const [activeOperation, setActiveOperation] = useState("complete");
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [flowRequests, setFlowRequests] = useState([]);
  const [selectedFlowId, setSelectedFlowId] = useState("");
  const [workflowResult, setWorkflowResult] = useState(null); // New state for workflow results

  // Fetch latest jobs
  const fetchLatestJobs = async () => {
    try {
      const response = await fetch("http://localhost:5000/fbdi/latest-ess-jobs");
      const data = await response.json();
      setJobs(data.jobs || []);
    } catch (error) {
      console.error("Error fetching jobs:", error);
    }
  };

  useEffect(() => {
    fetchLatestJobs();
  }, []);

  // Updated Complete FBDI Workflow - now returns job IDs instead of report
  const handleCompleteWorkflow = async () => {
    if (!rawFile || !selectedTemplate || !projectName || !envType) {
      alert("Please fill all required fields");
      return;
    }

    setLoading(prev => ({ ...prev, complete: true }));

    try {
      const formData = new FormData();
      formData.append("raw_file", rawFile);
      formData.append("fbdi_type", selectedTemplate);
      formData.append("project_name", projectName);
      formData.append("env_type", envType);
      formData.append("business_unit", "300000003170678");
      formData.append("batch_source", "MILGARD EBS SPREADSHEET");
      formData.append("gl_date", new Date().toISOString().split('T')[0]);

      const response = await fetch("http://localhost:5000/fbdi/complete-fbdi-workflow", {
        method: "POST",
        body: formData
      });

      if (response.ok) {
        const data = await response.json(); // Now expecting JSON response
        setWorkflowResult(data); // Store the workflow result
        
        alert(`Complete FBDI workflow finished successfully! AutoInvoice Job ID: ${data.job_ids.autoinvoice_import}`);
        fetchLatestJobs();
        
        // Show the report generation option
        setActiveOperation("report");
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(prev => ({ ...prev, complete: false }));
    }
  };

  // New function to generate execution report using the AutoInvoice job ID
  const handleGenerateExecutionReport = async (autoinvoiceJobId = null) => {
    const jobId = autoinvoiceJobId || workflowResult?.job_ids?.autoinvoice_import || selectedJobId;
    
    if (!jobId) {
      alert("Please provide an AutoInvoice job ID");
      return;
    }

    setLoading(prev => ({ ...prev, report: true }));
    
    try {
      const response = await fetch("http://localhost:5000/generate-execution-report", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json" 
        },
        body: JSON.stringify({ 
          autoinvoice_request_id: jobId 
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        alert("Failed: " + (err.error || "Unknown Error"));
        return;
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `AutoInvoice_Execution_Report_${jobId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      
      alert("AutoInvoice execution report downloaded successfully!");
    } catch (error) {
      alert("Error: " + error.message);
    } finally {
      setLoading(prev => ({ ...prev, report: false }));
    }
  };

  // All other existing functions remain the same...
  const handleUploadToUCM = async () => {
    if (!uploadedFile) {
      alert("Please select a file to upload");
      return;
    }

    setLoading(prev => ({ ...prev, upload: true }));
    
    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64Content = e.target.result.split(',')[1];
        
        const response = await fetch("http://localhost:5000/fbdi/upload-to-ucm", {
          method: "POST",
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            document_content: base64Content,
            file_name: uploadedFile.name,
            document_account: 'fin$/recievables$/import$'
          })
        });

        const data = await response.json();
        
        if (response.ok) {
          alert(`Success: ${data.message}. Document ID: ${data.document_id}`);
          setJobStatuses(prev => ({
            ...prev,
            upload: { status: 'success', documentId: data.document_id }
          }));
        } else {
          alert(`Error: ${data.error}`);
        }
      };
      reader.readAsDataURL(uploadedFile);
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(prev => ({ ...prev, upload: false }));
    }
  };

  const handleLoadInterface = async () => {
    setLoading(prev => ({ ...prev, interface: true }));
    
    try {
      const response = await fetch("http://localhost:5000/fbdi/load-interface", {
        method: "POST",
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ess_parameters: '2,511142,N,N,N'
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        alert(`Success: ${data.message}. Job ID: ${data.job_id}`);
        setJobStatuses(prev => ({
          ...prev,
          interface: { status: 'success', jobId: data.job_id }
        }));
        fetchLatestJobs();
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(prev => ({ ...prev, interface: false }));
    }
  };

  const handleAutoInvoiceImport = async () => {
    setLoading(prev => ({ ...prev, invoice: true }));
    
    try {
      const response = await fetch("http://localhost:5000/fbdi/auto-invoice-import", {
        method: "POST",
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          business_unit: '300000003170678',
          batch_source: 'MILGARD EBS SPREADSHEET',
          gl_date: new Date().toISOString().split('T')[0]
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        alert(`Success: ${data.message}. Job ID: ${data.job_id}`);
        setJobStatuses(prev => ({
          ...prev,
          invoice: { status: 'success', jobId: data.job_id }
        }));
        fetchLatestJobs();
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(prev => ({ ...prev, invoice: false }));
    }
  };

  const checkJobStatus = async (jobId) => {
    try {
      const response = await fetch(`http://localhost:5000/fbdi/check-job-status/${jobId}`);
      const data = await response.json();
      
      if (response.ok) {
        alert(`Job ${jobId} Status: ${data.job_status}`);
        if (data.flow_id) {
          console.log(`Flow ID: ${data.flow_id}`);
          setSelectedFlowId(data.flow_id);
        }
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    }
  };

  const operations = [
    { id: "complete", label: "Complete Workflow", icon: "🚀" },
    { id: "upload", label: "Upload to UCM", icon: "📤" },
    { id: "interface", label: "Load Interface", icon: "🔄" },
    { id: "invoice", label: "Auto Invoice Import", icon: "📋" },
    { id: "report", label: "Generate Report", icon: "📊" },
    { id: "status", label: "Job Status", icon: "⏱️" }
  ];

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 space-y-8">
      <div className="border-b border-gray-200 pb-4">
        <h2 className="text-3xl font-bold text-indigo-700 mb-2">FBDI Operations Center</h2>
        <p className="text-gray-600">Manage your FBDI operations with Oracle Cloud ERP</p>
      </div>

      {/* Operation Tabs */}
      <div className="flex space-x-2 border-b border-gray-200 overflow-x-auto">
        {operations.map((op) => (
          <button
            key={op.id}
            onClick={() => setActiveOperation(op.id)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-t-lg font-medium transition-all duration-300 whitespace-nowrap ${
              activeOperation === op.id
                ? "bg-indigo-500 text-white"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            <span>{op.icon}</span>
            <span>{op.label}</span>
          </button>
        ))}
      </div>

      {/* Complete Workflow Tab */}
      {activeOperation === "complete" && (
        <div className="space-y-6">
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-purple-800 mb-4">Complete FBDI Workflow</h3>
            <p className="text-purple-700 mb-6">
              This will execute the entire FBDI process: Generate FBDI → Upload to UCM → Load Interface → Auto Invoice Import
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block font-medium text-gray-700 mb-2">Raw Data File</label>
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={(e) => setRawFile(e.target.files[0])}
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                {rawFile && (
                  <p className="text-sm text-green-600 mt-1">Selected: {rawFile.name}</p>
                )}
              </div>
              
              <div>
                <label className="block font-medium text-gray-700 mb-2">FBDI Type</label>
                <select
                  value={selectedTemplate}
                  onChange={(e) => setSelectedTemplate(e.target.value)}
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  {fbdiTemplates.map((type) => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block font-medium text-gray-700 mb-2">Project Name</label>
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="Enter project name"
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              
              <div>
                <label className="block font-medium text-gray-700 mb-2">Environment</label>
                <input
                  type="text"
                  value={envType}
                  onChange={(e) => setEnvType(e.target.value)}
                  placeholder="Enter environment type"
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>

            {/* Show workflow results if available */}
            {workflowResult && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                <h4 className="font-semibold text-green-800 mb-2">✅ Workflow Completed Successfully!</h4>
                <div className="text-sm text-green-700 space-y-1">
                  <p><strong>Project:</strong> {workflowResult.project_name}</p>
                  <p><strong>FBDI Type:</strong> {workflowResult.fbdi_type}</p>
                  <p><strong>Interface Loader Job ID:</strong> {workflowResult.job_ids.interface_loader}</p>
                  <p><strong>AutoInvoice Import Job ID:</strong> {workflowResult.job_ids.autoinvoice_import}</p>
                  <p><strong>Document ID:</strong> {workflowResult.document_id}</p>
                </div>
                <button
                  onClick={() => handleGenerateExecutionReport(workflowResult.job_ids.autoinvoice_import)}
                  className="mt-3 bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium"
                >
                  📊 Generate Execution Report
                </button>
              </div>
            )}

            <div className="bg-white rounded-lg p-4 mb-6">
              <h4 className="font-semibold text-gray-800 mb-2">Workflow Steps:</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Generate FBDI file from raw data</li>
                <li>• Upload FBDI to Oracle UCM</li>
                <li>• Submit Interface Loader job</li>
                <li>• Submit Auto Invoice Import job</li>
                <li>• Wait for jobs to complete</li>
              </ul>
            </div>

            <button
              onClick={handleCompleteWorkflow}
              disabled={loading.complete || !rawFile || !selectedTemplate || !projectName || !envType}
              className={`w-full px-6 py-4 rounded-lg font-semibold text-lg transition-all duration-300 ${
                loading.complete || !rawFile || !selectedTemplate || !projectName || !envType
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white transform hover:scale-105"
              }`}
            >
              {loading.complete ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing Complete Workflow...
                </span>
              ) : (
                "🚀 Start Complete FBDI Workflow"
              )}
            </button>
          </div>
        </div>
      )}

      {/* Generate Report Tab */}
      {activeOperation === "report" && (
        <div className="space-y-6">
          <div className="bg-green-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-800 mb-4">Generate Execution Report</h3>
            
            {workflowResult && (
              <div className="bg-white rounded-lg p-4 mb-4">
                <h4 className="font-semibold text-gray-800 mb-2">Use AutoInvoice Job from Last Workflow:</h4>
                <p className="text-sm text-gray-600 mb-3">Job ID: {workflowResult.job_ids.autoinvoice_import}</p>
                <button
                  onClick={() => handleGenerateExecutionReport(workflowResult.job_ids.autoinvoice_import)}
                  disabled={loading.report}
                  className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 ${
                    loading.report
                      ? "bg-gray-400 cursor-not-allowed"
                      : "bg-green-500 hover:bg-green-600 text-white"
                  }`}
                >
                  {loading.report ? "Generating Report..." : "📊 Generate Report for This Job"}
                </button>
              </div>
            )}

            <div className="bg-white rounded-lg p-4">
              <h4 className="font-semibold text-gray-800 mb-2">Or Enter AutoInvoice Job ID Manually:</h4>
              <div className="flex space-x-3">
                <input
                  type="text"
                  value={selectedJobId}
                  onChange={(e) => setSelectedJobId(e.target.value)}
                  placeholder="Enter AutoInvoice job ID"
                  className="flex-1 border-2 border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                <button
                  onClick={() => handleGenerateExecutionReport()}
                  disabled={loading.report || !selectedJobId}
                  className={`px-6 py-2 rounded-lg font-medium transition-all duration-300 ${
                    loading.report || !selectedJobId
                      ? "bg-gray-400 cursor-not-allowed"
                      : "bg-green-500 hover:bg-green-600 text-white"
                  }`}
                >
                  {loading.report ? "Generating..." : "Generate Report"}
                </button>
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg p-4 mt-4">
              <h4 className="font-semibold text-blue-800 mb-2">Recent Jobs:</h4>
              <div className="space-y-2">
                {jobs.slice(0, 5).map((job) => (
                  <div key={job.ReqstId} className="flex justify-between items-center bg-white rounded px-3 py-2">
                    <div>
                      <span className="font-medium text-gray-800">{job.ReqstId}</span>
                      <span className="text-sm text-gray-600 ml-2">{job.JobName}</span>
                    </div>
                    <button
                      onClick={() => setSelectedJobId(job.ReqstId)}
                      className="text-blue-500 hover:text-blue-700 text-sm font-medium"
                    >
                      Use This Job
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Upload to UCM Tab */}
      {activeOperation === "upload" && (
        <div className="space-y-6">
          <div className="bg-blue-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-4">Upload FBDI File to UCM</h3>
            <div className="space-y-4">
              <div>
                <label className="block font-medium text-gray-700 mb-2">Select FBDI File</label>
                <input
                  type="file"
                  accept=".zip"
                  onChange={(e) => setUploadedFile(e.target.files[0])}
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                {uploadedFile && (
                  <p className="text-sm text-green-600 mt-1">Selected: {uploadedFile.name}</p>
                )}
              </div>
              <button
                onClick={handleUploadToUCM}
                disabled={loading.upload || !uploadedFile}
                className={`px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${
                  loading.upload || !uploadedFile
                    ? "bg-gray-400 cursor-not-allowed"
                    : "bg-blue-500 hover:bg-blue-600 text-white"
                }`}
              >
                {loading.upload ? "Uploading..." : "Upload to UCM"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Load Interface Tab */}
      {activeOperation === "interface" && (
        <div className="space-y-6">
          <div className="bg-yellow-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-yellow-800 mb-4">Load Interface</h3>
            <p className="text-yellow-700 mb-4">Submit Interface Loader job to process uploaded FBDI files.</p>
            <button
              onClick={handleLoadInterface}
              disabled={loading.interface}
              className={`px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${
                loading.interface
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-yellow-500 hover:bg-yellow-600 text-white"
              }`}
            >
              {loading.interface ? "Loading..." : "Load Interface"}
            </button>
          </div>
        </div>
      )}

      {/* Auto Invoice Import Tab */}
      {activeOperation === "invoice" && (
        <div className="space-y-6">
          <div className="bg-orange-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-orange-800 mb-4">Auto Invoice Import</h3>
            <p className="text-orange-700 mb-4">Submit Auto Invoice Import job to create invoices from loaded interface data.</p>
            <button
              onClick={handleAutoInvoiceImport}
              disabled={loading.invoice}
              className={`px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${
                loading.invoice
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-orange-500 hover:bg-orange-600 text-white"
              }`}
            >
              {loading.invoice ? "Importing..." : "Auto Invoice Import"}
            </button>
          </div>
        </div>
      )}

      {/* Job Status Tab */}
      {activeOperation === "status" && (
        <div className="space-y-6">
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Check Job Status</h3>
            <div className="space-y-4">
              <div>
                <label className="block font-medium text-gray-700 mb-2">Job ID</label>
                <div className="flex space-x-3">
                  <input
                    type="text"
                    value={selectedJobId}
                    onChange={(e) => setSelectedJobId(e.target.value)}
                    placeholder="Enter job ID"
                    className="flex-1 border-2 border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  />
                  <button
                    onClick={() => checkJobStatus(selectedJobId)}
                    disabled={!selectedJobId}
                    className={`px-6 py-2 rounded-lg font-semibold transition-all duration-300 ${
                      !selectedJobId
                        ? "bg-gray-400 cursor-not-allowed"
                        : "bg-gray-500 hover:bg-gray-600 text-white"
                    }`}
                  >
                    Check Status
                  </button>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-gray-800 mb-2">Recent Jobs:</h4>
                <div className="space-y-2">
                  {jobs.map((job) => (
                    <div key={job.ReqstId} className="flex justify-between items-center bg-white rounded-lg p-3 border">
                      <div>
                        <span className="font-medium text-gray-800">{job.ReqstId}</span>
                        <span className="text-sm text-gray-600 ml-2">{job.JobName}</span>
                        <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                          job.RequestStatus === 'SUCCEEDED' ? 'bg-green-100 text-green-800' :
                          job.RequestStatus === 'ERROR' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {job.RequestStatus}
                        </span>
                      </div>
                      <button
                        onClick={() => checkJobStatus(job.ReqstId)}
                        className="text-blue-500 hover:text-blue-700 text-sm font-medium"
                      >
                        Check Status
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FBDIOperations;

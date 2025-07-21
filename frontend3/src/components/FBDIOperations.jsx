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

  // Complete FBDI Workflow
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
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${projectName}_AutoInvoiceExecutionReport.xml`;
        a.click();
        URL.revokeObjectURL(url);
        
        alert("Complete FBDI workflow finished successfully! Report downloaded.");
        fetchLatestJobs();
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

  const handleDownloadAutoInvoiceReport = async () => {
    const essParams = "300000003170678,MILGARD EBS SPREADSHEET,2025-07-17,,,,,,,,,,,,,,,,,,,,Y,N";
    
    setLoading(prev => ({ ...prev, report: true }));
    
    try {
      const response = await fetch("http://localhost:5000/fbdi/autoinvoice-import-and-get-report", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json" 
        },
        body: JSON.stringify({ 
          ess_parameters: essParams 
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
      a.download = "AutoInvoiceExecutionReport.xml";
      a.click();
      URL.revokeObjectURL(url);
      
      alert("AutoInvoice Import completed and report downloaded successfully!");
      fetchLatestJobs();
    } catch (error) {
      alert("Error: " + error.message);
    } finally {
      setLoading(prev => ({ ...prev, report: false }));
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

  const fetchFlowRequests = async (flowId) => {
    if (!flowId) return;
    
    try {
      const response = await fetch(`http://localhost:5000/fbdi/ess-flow-requests/${flowId}`);
      const data = await response.json();
      
      if (response.ok) {
        setFlowRequests(data.all_requests || []);
        if (data.autoinvoice_report_request) {
          alert(`AutoInvoice Report Request ID: ${data.autoinvoice_report_request.REQUESTID}`);
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
    { id: "report", label: "Download Report", icon: "📊" },
    { id: "status", label: "Job Status", icon: "⏱️" },
    { id: "flow", label: "Flow Requests", icon: "🔗" }
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
              This will execute the entire FBDI process in one go: Generate FBDI → Upload to UCM → Load Interface → Auto Invoice Import → Download Execution Report
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

            <div className="bg-white rounded-lg p-4 mb-6">
              <h4 className="font-semibold text-gray-800 mb-2">Workflow Steps:</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Generate FBDI file from raw data</li>
                <li>• Upload FBDI to Oracle UCM</li>
                <li>• Submit Interface Loader job</li>
                <li>• Submit Auto Invoice Import job</li>
                <li>• Wait for jobs to complete</li>
                <li>• Download execution report XML</li>
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

      {/* All other existing tabs remain the same */}
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

      {/* Continue with all other existing tabs... */}
      {/* The rest of the tabs remain unchanged from the previous implementation */}
    </div>
  );
};

export default FBDIOperations;

import React, { useState, useEffect, useRef } from "react";
import { useFBDI } from "./FBDIGenerator3";
import { Upload, Play, CheckCircle, XCircle, Clock, FileText, Settings, BarChart3, Download, ArrowRight } from "lucide-react";
 
const FBDIOperations = () => {
  const {
    generatedFbdiFile,
    workflowStep,
    setWorkflowStep,
    fbdiProcessingComplete,
    setFbdiProcessingComplete,
    processingResult,
    setProcessingResult
  } = useFBDI();
 
  const [loading, setLoading] = useState(false);
  const [selectedFbdiFile, setSelectedFbdiFile] = useState(null);
  const [businessUnit, setBusinessUnit] = useState('300000003170678');
  const [batchSource, setBatchSource] = useState('MILGARD EBS SPREADSHEET');
  const [glDate, setGlDate] = useState(new Date().toISOString().split('T')[0]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
 
  // Add loading state for ESS report download
  const [essReportLoading, setEssReportLoading] = useState(false);
 
  // ENHANCED PROGRESS TRACKING STATE
  const [currentProcessingStep, setCurrentProcessingStep] = useState(null);
  const [completedSteps, setCompletedSteps] = useState(new Set());
 
  // Use useRef to track if auto-processing has been initiated
  const autoProcessingInitiated = useRef(false);
  const stepTimers = useRef({});
 
  // Auto-start processing when component loads (if coming from workflow)
  useEffect(() => {
    if (workflowStep === 'process' &&
        generatedFbdiFile &&
        !autoProcessingInitiated.current &&
        !loading) {
     
      autoProcessingInitiated.current = true;
     
      const autoFile = new File([generatedFbdiFile.blob], generatedFbdiFile.filename, {
        type: 'application/zip'
      });
     
      setSelectedFbdiFile(autoFile);
     
      setTimeout(() => {
        handleProcessFBDI(autoFile);
      }, 0);
    }
  }, [workflowStep, generatedFbdiFile, loading]);
 
  // Reset the ref when workflow step changes away from 'process'
  useEffect(() => {
    if (workflowStep !== 'process') {
      autoProcessingInitiated.current = false;
    }
  }, [workflowStep]);
 
  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      Object.values(stepTimers.current).forEach(timer => clearTimeout(timer));
    };
  }, []);
 
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setSelectedFbdiFile(file);
    setResult(null);
    setError(null);
  };
 
  const handleProcessFBDI = async (fileArg) => {
    const file = fileArg || selectedFbdiFile;
    if (!file) {
      alert("Please select an FBDI file first");
      return;
    }
 
    if (loading) {
      console.log("⚠️ Processing already in progress, skipping duplicate call");
      return;
    }
 
    // INITIALIZE PROGRESS TRACKING
    setLoading(true);
    setError(null);
    setResult(null);
    setCurrentProcessingStep("upload");        // SET FIRST STEP
    setCompletedSteps(new Set());              // CLEAR COMPLETED STEPS
 
    // Clear any existing timers
    Object.values(stepTimers.current).forEach(timer => clearTimeout(timer));
    stepTimers.current = {};
 
    // SIMULATE STEP PROGRESSION WITH TIMERS
    stepTimers.current.interface = setTimeout(() => {
      setCompletedSteps(prev => new Set([...prev, "upload"]));
      setCurrentProcessingStep("interface_loader");
    }, 2000);
 
    stepTimers.current.autoinvoice = setTimeout(() => {
      setCompletedSteps(prev => new Set([...prev, "upload", "interface_loader"]));
      setCurrentProcessingStep("autoinvoice_import");
    }, 4000);
 
    try {
      const formData = new FormData();
      formData.append("fbdi_file", file);
      formData.append("business_unit", businessUnit);
      formData.append("batch_source", batchSource);
      formData.append("gl_date", glDate);
 
      console.log("📤 Processing FBDI file:", file.name);
      console.log("📊 Parameters:", { businessUnit, batchSource, glDate });
 
      const response = await fetch("http://localhost:5000/fbdi/process-fbdi", {
        method: "POST",
        body: formData
      });
 
      const data = await response.json();
 
      if (response.ok) {
        setResult(data);
        setProcessingResult(data);
        setFbdiProcessingComplete(true);
        // MARK ALL STEPS AS COMPLETED
        setCompletedSteps(new Set(["upload", "interface_loader", "autoinvoice_import"]));
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
      // CLEANUP
      Object.values(stepTimers.current).forEach(timer => clearTimeout(timer));
      stepTimers.current = {};
      setCurrentProcessingStep(null);
      setLoading(false);
    }
  };
 
  // Updated handleDownloadESS with loading state
  const handleDownloadESS = async () => {
    // Use the autoinvoice job ID from the new structure
    const jobId = result?.autoinvoice_import?.job_id || result?.autoinvoice_job_id;
    if (!jobId) return;
    window.myGlobalVariable = { requestId: jobId };
 
    setEssReportLoading(true);
   
    try {
      console.log("📄 Generating ESS report...");
     
      const response = await fetch("http://localhost:5000/generate-execution-report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          autoinvoice_request_id: jobId
        })
      });
 
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `AutoInvoice_Report_${jobId}.pdf`;
        a.click();
        URL.revokeObjectURL(url);
        console.log("✅ ESS report downloaded successfully");
      } else {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (err) {
      console.error("❌ Error generating ESS report:", err);
      alert("Error generating report: " + err.message);
    } finally {
      setEssReportLoading(false);
    }
  };
 
  const handleContinueToRecon = () => {
    setWorkflowStep('reconcile');
  };
 
  const handleReset = () => {
    setSelectedFbdiFile(null);
    setResult(null);
    setError(null);
    setCurrentProcessingStep(null);           // CLEAR PROGRESS STATE
    setCompletedSteps(new Set());             // CLEAR COMPLETED STEPS
    autoProcessingInitiated.current = false;
   
    // Clear timers
    Object.values(stepTimers.current).forEach(timer => clearTimeout(timer));
    stepTimers.current = {};
   
    const fileInput = document.getElementById('fbdi-file-input');
    if (fileInput) fileInput.value = '';
  };
 
  // FIXED getStepStatus function with proper sequential tracking
  const getStepStatus = (step) => {
    // Check for errors first
    if (error?.step === step || error?.[step]) return "error";
   
    // If we have final results, check actual API response
    if (result && !loading) {
      switch(step) {
        case "upload":
          return result.upload?.status === "SUCCEEDED" ? "success" : "error";
        case "interface_loader":
          const interfaceStatus = result.interface_loader?.RequestStatus;
          return (interfaceStatus === "SUCCEEDED" || interfaceStatus === "WARNING") ? "success" : "error";
        case "autoinvoice_import":
          const invoiceStatus = result.autoinvoice_import?.RequestStatus;
          return (invoiceStatus === "SUCCEEDED" || invoiceStatus === "WARNING") ? "success" : "error";
        default:
          return "pending";
      }
    }
   
    // THIS IS THE KEY FIX - During loading, use progress tracking
    if (loading) {
      // If step is completed, show success
      if (completedSteps.has(step)) {
        return "success";
      }
     
      // If step is currently running, show running
      if (currentProcessingStep === step) {
        return "running";
      }
     
      // Otherwise show pending
      return "pending";
    }
   
    return "pending";
  };
 
  // Enhanced status text with better messaging
  const getStatusText = (step) => {
    const status = getStepStatus(step);
   
    if (result && status === "success") {
      switch(step) {
        case "upload":
          return `✅ Completed - Document ID: ${result.upload?.document_id || 'N/A'}`;
        case "interface_loader":
          const details = result.interface_loader;
          const elapsed = details?.ElapsedTime || 'N/A';
          return `✅ Completed in ${elapsed} - Status: ${details?.RequestStatus}`;
        case "autoinvoice_import":
          const invoiceDetails = result.autoinvoice_import;
          const invoiceElapsed = invoiceDetails?.ElapsedTime || 'N/A';
          return `✅ Completed in ${invoiceElapsed} - Status: ${invoiceDetails?.RequestStatus}`;
      }
    }
   
    // Enhanced status messages
    switch (status) {
      case "success":
        return "✅ Completed successfully";
      case "error":
        return "❌ Failed - Check error details below";
      case "running":
        switch (step) {
          case "upload": return "🔄 Uploading FBDI file to Oracle UCM...";
          case "interface_loader": return "🔄 Loading data into Oracle interface tables...";
          case "autoinvoice_import": return "🔄 Creating invoice transactions...";
          default: return "🔄 Processing...";
        }
      case "pending":
        if (loading) {
          switch (step) {
            case "upload": return "⏳ Ready to upload";
            case "interface_loader":
              return completedSteps.has("upload") ? "⏳ Preparing to load data..." : "⏳ Waiting for upload to complete...";
            case "autoinvoice_import":
              return completedSteps.has("interface_loader") ? "⏳ Preparing to create invoices..." : "⏳ Waiting for previous steps...";
            default: return "⏳ Waiting...";
          }
        } else {
          switch (step) {
            case "upload": return "📤 Upload FBDI file to Oracle Content Management";
            case "interface_loader": return "🔧 Load data into Oracle interface tables";
            case "autoinvoice_import": return "🧾 Create invoice transactions from interface data";
            default: return "⏳ Waiting...";
          }
        }
      default:
        return "⏳ Pending";
    }
  };
 
  // Show success state with two options after processing is complete
  if (fbdiProcessingComplete && result) {
    return (
      <div className="space-y-6">
        {/* Success Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <div className="ml-4">
              <h2 className="text-2xl font-semibold text-gray-900">FBDI Processing Completed Successfully!</h2>
              <p className="text-gray-600 mt-1">All workflow steps have been completed. Choose your next action.</p>
            </div>
          </div>
        </div>
 
        {/* Processing Results - Updated for new JSON structure */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <BarChart3 className="w-6 h-6 text-green-600 mr-3" />
            <h3 className="text-lg font-medium text-green-800">Processing Results</h3>
          </div>
         
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                <span className="text-sm font-medium text-gray-700">Document ID</span>
                <span className="text-sm text-gray-900">{result.upload?.document_id || result.document_id || 'N/A'}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                <span className="text-sm font-medium text-gray-700">Interface Job ID</span>
                <span className="text-sm text-gray-900">{result.interface_loader?.job_id || result.interface_job_id || 'N/A'}</span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                <span className="text-sm font-medium text-gray-700">AutoInvoice Job ID</span>
                <span className="text-sm text-gray-900">{result.autoinvoice_import?.job_id || result.autoinvoice_job_id || 'N/A'}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                <span className="text-sm font-medium text-gray-700">Status</span>
                <span className="text-sm text-green-600 font-medium">SUCCEEDED</span>
              </div>
            </div>
          </div>
        </div>
 
        {/* Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                {essReportLoading ? (
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                ) : (
                  <FileText className="w-8 h-8 text-blue-600" />
                )}
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Download ESS Report</h3>
              <p className="text-gray-600 mb-6">
                {essReportLoading
                  ? "Generating execution report..."
                  : "Download the execution report with job details and processing status"
                }
              </p>
              <button
                onClick={handleDownloadESS}
                disabled={essReportLoading}
                className={`w-full px-6 py-3 rounded-lg font-medium transition-colors ${
                  essReportLoading
                    ? "bg-gray-400 cursor-not-allowed text-gray-600"
                    : "bg-blue-600 hover:bg-blue-700 text-white"
                }`}
              >
                {essReportLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white inline mr-2"></div>
                    Generating Report...
                  </>
                ) : (
                  <>
                    <Download className="w-5 h-5 inline mr-2" />
                    Download Report
                  </>
                )}
              </button>
            </div>
          </div>
 
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Continue to Reconciliation</h3>
              <p className="text-gray-600 mb-6">Proceed to generate reconciliation report comparing your data</p>
              <button
                onClick={handleContinueToRecon}
                className="w-full bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                <ArrowRight className="w-5 h-5 inline mr-2" />
                Continue
              </button>
            </div>
          </div>
        </div>
 
        <div className="text-center">
          <button
            onClick={() => {
              setFbdiProcessingComplete(false);
              setProcessingResult(null);
              setResult(null);
              setWorkflowStep('generate');
              handleReset();
            }}
            className="text-gray-500 hover:text-gray-700 text-sm underline"
          >
            Start Over
          </button>
        </div>
      </div>
    );
  }
 
  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Play className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <div className="ml-4">
              <h2 className="text-2xl font-semibold text-gray-900">FBDI Processing Center</h2>
              <p className="text-gray-600 mt-1">
                {workflowStep === 'process' ? 'Auto-processing your generated FBDI file...' : 'Processing FBDI files through Oracle Cloud workflow'}
              </p>
            </div>
          </div>
          {loading && (
            <div className="flex items-center text-blue-600">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-2"></div>
              <span className="text-sm font-medium">Processing...</span>
            </div>
          )}
        </div>
      </div>
 
      {/* Auto-processing Info */}
      {workflowStep === 'process' && generatedFbdiFile && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <Settings className="w-5 h-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-medium text-blue-900">Auto-Processing Configuration</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center justify-between p-3 bg-white rounded-lg">
              <span className="text-sm font-medium text-gray-700">File</span>
              <span className="text-sm text-gray-900">{generatedFbdiFile.filename}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-white rounded-lg">
              <span className="text-sm font-medium text-gray-700">Business Unit</span>
              <span className="text-sm text-gray-900">{businessUnit}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-white rounded-lg">
              <span className="text-sm font-medium text-gray-700">GL Date</span>
              <span className="text-sm text-gray-900">{glDate}</span>
            </div>
          </div>
        </div>
      )}
 
      {/* Main Form */}
      {workflowStep !== 'process' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-6">
            <Upload className="w-5 h-5 text-gray-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Upload & Process FBDI</h3>
          </div>
 
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              FBDI Package File (ZIP)
            </label>
            <input
              id="fbdi-file-input"
              type="file"
              accept=".zip"
              onChange={handleFileChange}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
            />
            {selectedFbdiFile && (
              <div className="mt-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center">
                  <CheckCircle className="w-5 h-5 text-green-500 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-green-800">{selectedFbdiFile.name}</p>
                    <p className="text-xs text-green-600">
                      Size: {(selectedFbdiFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
 
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Business Unit</label>
              <input
                type="text"
                value={businessUnit}
                onChange={(e) => setBusinessUnit(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
              />
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Batch Source</label>
              <input
                type="text"
                value={batchSource}
                onChange={(e) => setBatchSource(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
              />
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">GL Date</label>
              <input
                type="date"
                value={glDate}
                onChange={(e) => setGlDate(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
              />
            </div>
          </div>
 
          <div className="flex justify-end pt-6 border-t border-gray-200">
            <button
              onClick={() => handleProcessFBDI()}
              disabled={loading || !selectedFbdiFile}
              className={`inline-flex items-center px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                loading || !selectedFbdiFile
                  ? "bg-gray-300 cursor-not-allowed text-gray-500"
                  : "bg-purple-600 hover:bg-purple-700 text-white shadow-sm hover:shadow-md"
              }`}
            >
              {loading ? (
                <>
                  <div className="animate-spin -ml-1 mr-3 h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
                  Processing Workflow...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5 mr-2" />
                  Process FBDI Workflow
                </>
              )}
            </button>
          </div>
        </div>
      )}
 
      {/* ENHANCED Workflow Progress - NOW WORKS CORRECTLY */}
      {(loading || result || error) && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-6">
            <BarChart3 className="w-5 h-5 text-gray-600 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Workflow Progress</h3>
          </div>
 
          <div className="space-y-4">
            {/* Step 1: UCM Upload */}
            <div className="flex items-center p-4 rounded-lg border border-gray-200">
              <div className="flex-shrink-0 mr-4">
                {getStepStatus("upload") === "success" ? (
                  <CheckCircle className="w-6 h-6 text-green-500" />
                ) : getStepStatus("upload") === "error" ? (
                  <XCircle className="w-6 h-6 text-red-500" />
                ) : getStepStatus("upload") === "running" ? (
                  <Clock className="w-6 h-6 text-blue-500 animate-pulse" />
                ) : (
                  <Clock className="w-6 h-6 text-yellow-500" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-gray-900">Step 1: Upload to UCM</h4>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    getStepStatus("upload") === "success" ? "bg-green-100 text-green-800" :
                    getStepStatus("upload") === "error" ? "bg-red-100 text-red-800" :
                    getStepStatus("upload") === "running" ? "bg-blue-100 text-blue-800" :
                    "bg-yellow-100 text-yellow-800"
                  }`}>
                    {getStepStatus("upload") === "success" ? "SUCCEEDED" :
                     getStepStatus("upload") === "error" ? "FAILED" :
                     getStepStatus("upload") === "running" ? "RUNNING" :
                     "WAITING"}
                  </span>
                </div>
                <p className="text-sm text-gray-600">
                  {getStatusText("upload")}
                </p>
              </div>
            </div>
 
            {/* Step 2: Interface Loader */}
            <div className="flex items-center p-4 rounded-lg border border-gray-200">
              <div className="flex-shrink-0 mr-4">
                {getStepStatus("interface_loader") === "success" ? (
                  <CheckCircle className="w-6 h-6 text-green-500" />
                ) : getStepStatus("interface_loader") === "error" ? (
                  <XCircle className="w-6 h-6 text-red-500" />
                ) : getStepStatus("interface_loader") === "running" ? (
                  <Clock className="w-6 h-6 text-blue-500 animate-pulse" />
                ) : (
                  <Clock className="w-6 h-6 text-yellow-500" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-gray-900">Step 2: Interface Loader</h4>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    getStepStatus("interface_loader") === "success" ? "bg-green-100 text-green-800" :
                    getStepStatus("interface_loader") === "error" ? "bg-red-100 text-red-800" :
                    getStepStatus("interface_loader") === "running" ? "bg-blue-100 text-blue-800" :
                    "bg-yellow-100 text-yellow-800"
                  }`}>
                    {getStepStatus("interface_loader") === "success" ? "SUCCEEDED" :
                     getStepStatus("interface_loader") === "error" ? "FAILED" :
                     getStepStatus("interface_loader") === "running" ? "RUNNING" :
                     "WAITING"}
                  </span>
                </div>
                <p className="text-sm text-gray-600">
                  {getStatusText("interface_loader")}
                </p>
                {result?.interface_loader?.job_id && (
                  <p className="text-xs text-blue-600 mt-1">Job ID: {result.interface_loader.job_id}</p>
                )}
              </div>
            </div>
 
            {/* Step 3: AutoInvoice Import */}
            <div className="flex items-center p-4 rounded-lg border border-gray-200">
              <div className="flex-shrink-0 mr-4">
                {getStepStatus("autoinvoice_import") === "success" ? (
                  <CheckCircle className="w-6 h-6 text-green-500" />
                ) : getStepStatus("autoinvoice_import") === "error" ? (
                  <XCircle className="w-6 h-6 text-red-500" />
                ) : getStepStatus("autoinvoice_import") === "running" ? (
                  <Clock className="w-6 h-6 text-blue-500 animate-pulse" />
                ) : (
                  <Clock className="w-6 h-6 text-yellow-500" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium text-gray-900">Step 3: AutoInvoice Import</h4>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    getStepStatus("autoinvoice_import") === "success" ? "bg-green-100 text-green-800" :
                    getStepStatus("autoinvoice_import") === "error" ? "bg-red-100 text-red-800" :
                    getStepStatus("autoinvoice_import") === "running" ? "bg-blue-100 text-blue-800" :
                    "bg-yellow-100 text-yellow-800"
                  }`}>
                    {getStepStatus("autoinvoice_import") === "success" ? "SUCCEEDED" :
                     getStepStatus("autoinvoice_import") === "error" ? "FAILED" :
                     getStepStatus("autoinvoice_import") === "running" ? "RUNNING" :
                     "WAITING"}
                  </span>
                </div>
                <p className="text-sm text-gray-600">
                  {getStatusText("autoinvoice_import")}
                </p>
                {result?.autoinvoice_import?.job_id && (
                  <p className="text-xs text-blue-600 mt-1">Job ID: {result.autoinvoice_import.job_id}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
 
      {/* Error Result */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <XCircle className="w-6 h-6 text-red-600 mr-3" />
            <h3 className="text-lg font-medium text-red-800">Workflow Failed</h3>
          </div>
         
          <div className="space-y-4">
            <div>
              <h4 className="font-medium text-red-800">Failed at: {error.step}</h4>
              <p className="text-sm text-red-700 mt-1">
                {typeof error.error === 'string' ? error.error : JSON.stringify(error.error)}
              </p>
            </div>
           
            {error.job_id && (
              <div>
                <h4 className="font-medium text-red-800">Job Details:</h4>
                <div className="text-sm text-red-700 space-y-1">
                  <p><span className="font-medium">Job ID:</span> {error.job_id}</p>
                  {error.status && <p><span className="font-medium">Status:</span> {error.status}</p>}
                </div>
              </div>
            )}
          </div>
 
          <div className="mt-6 pt-4 border-t border-red-200">
            <button
              onClick={() => handleProcessFBDI()}
              className="inline-flex items-center bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      )}
 
      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-center mb-4">
          <Settings className="w-5 h-5 text-blue-600 mr-2" />
          <h3 className="text-lg font-medium text-blue-900">Workflow Overview</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-sm text-blue-800">
            <div className="font-medium mb-2">Step 1: UCM Upload</div>
            <p>Your FBDI file is uploaded to Oracle UCM for processing</p>
          </div>
          <div className="text-sm text-blue-800">
            <div className="font-medium mb-2">Step 2: Interface Loader</div>
            <p>Data is processed and loaded into Oracle interface tables</p>
          </div>
          <div className="text-sm text-blue-800">
            <div className="font-medium mb-2">Step 3: AutoInvoice Import</div>
            <p>Invoice transactions are created from the interface data</p>
          </div>
        </div>
      </div>
    </div>
  );
};
 
export default FBDIOperations;
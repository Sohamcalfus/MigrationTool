import React, { useState } from "react";
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
    full: false
  });

  const [activeOperation, setActiveOperation] = useState("upload");

  // Upload to UCM
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

  // Load Interface
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
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(prev => ({ ...prev, interface: false }));
    }
  };

  // Auto Invoice Import
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
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(prev => ({ ...prev, invoice: false }));
    }
  };

  // Full Process
  const handleFullProcess = async () => {
    if (!rawFile || !selectedTemplate || !projectName || !envType) {
      alert("Please fill all fields before starting full process");
      return;
    }

    setLoading(prev => ({ ...prev, full: true }));
    setProcessProgress({
      step1: 'active',
      step2: 'pending',
      step3: 'pending',
      step4: 'pending'
    });

    try {
      // Step 1: Generate FBDI
      const formData = new FormData();
      formData.append("raw_file", rawFile);
      formData.append("fbdi_type", selectedTemplate);
      formData.append("project_name", projectName);
      formData.append("env_type", envType);

      const generateResponse = await fetch("http://localhost:5000/generate-fbdi-from-type", {
        method: "POST",
        body: formData,
      });

      if (generateResponse.ok) {
        const blob = await generateResponse.blob();
        setGeneratedFBDI(blob);
        setProcessProgress(prev => ({ ...prev, step1: 'completed', step2: 'active' }));
        
        // Step 2: Upload to UCM
        const reader = new FileReader();
        reader.onload = async (e) => {
          const base64Content = e.target.result.split(',')[1];
          
          const uploadResponse = await fetch("http://localhost:5000/fbdi/upload-to-ucm", {
            method: "POST",
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              document_content: base64Content,
              file_name: `${projectName}_${selectedTemplate}_FBDI.zip`,
              document_account: 'fin$/recievables$/import$'
            })
          });

          const uploadData = await uploadResponse.json();
          
          if (uploadResponse.ok) {
            setProcessProgress(prev => ({ ...prev, step2: 'completed', step3: 'active' }));
            
            // Step 3: Load Interface
            const interfaceResponse = await fetch("http://localhost:5000/fbdi/load-interface", {
              method: "POST",
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                ess_parameters: '2,511142,N,N,N'
              })
            });

            const interfaceData = await interfaceResponse.json();
            
            if (interfaceResponse.ok) {
              setProcessProgress(prev => ({ ...prev, step3: 'completed', step4: 'active' }));
              
              // Step 4: Auto Invoice Import
              const invoiceResponse = await fetch("http://localhost:5000/fbdi/auto-invoice-import", {
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

              const invoiceData = await invoiceResponse.json();
              
              if (invoiceResponse.ok) {
                setProcessProgress(prev => ({ ...prev, step4: 'completed' }));
                alert('Full FBDI process completed successfully!');
              } else {
                throw new Error(`Auto Invoice Import failed: ${invoiceData.error}`);
              }
            } else {
              throw new Error(`Interface Loader failed: ${interfaceData.error}`);
            }
          } else {
            throw new Error(`UCM Upload failed: ${uploadData.error}`);
          }
        };
        reader.readAsDataURL(blob);
      } else {
        throw new Error('FBDI Generation failed');
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(prev => ({ ...prev, full: false }));
    }
  };

  // Check Job Status
  const checkJobStatus = async (jobId) => {
    try {
      const response = await fetch(`http://localhost:5000/fbdi/check-job-status/${jobId}`);
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error checking job status:', error);
      return { error: error.message };
    }
  };

  const operations = [
    { id: "upload", label: "Upload to UCM", icon: "📤" },
    { id: "interface", label: "Load Interface", icon: "🔄" },
    { id: "invoice", label: "Auto Invoice Import", icon: "📋" },
    { id: "full", label: "Full Process", icon: "🚀" }
  ];

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 space-y-8">
      <div className="border-b border-gray-200 pb-4">
        <h2 className="text-3xl font-bold text-indigo-700 mb-2">FBDI Operations Center</h2>
        <p className="text-gray-600">Manage your FBDI operations with Oracle Cloud ERP</p>
      </div>

      {/* Operation Tabs */}
      <div className="flex space-x-2 border-b border-gray-200">
        {operations.map((op) => (
          <button
            key={op.id}
            onClick={() => setActiveOperation(op.id)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-t-lg font-medium transition-all duration-300 ${
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
            <div className="space-y-4">
              <div>
                <label className="block font-medium text-gray-700 mb-2">ESS Parameters</label>
                <input
                  type="text"
                  defaultValue="2,511142,N,N,N"
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-yellow-500"
                />
              </div>
              <button
                onClick={handleLoadInterface}
                disabled={loading.interface}
                className={`px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${
                  loading.interface
                    ? "bg-gray-400 cursor-not-allowed"
                    : "bg-yellow-500 hover:bg-yellow-600 text-white"
                }`}
              >
                {loading.interface ? "Submitting..." : "Submit Interface Loader"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Auto Invoice Import Tab */}
      {activeOperation === "invoice" && (
        <div className="space-y-6">
          <div className="bg-green-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-800 mb-4">Auto Invoice Import</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block font-medium text-gray-700 mb-2">Business Unit</label>
                <input
                  type="text"
                  defaultValue="300000003170678"
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block font-medium text-gray-700 mb-2">Batch Source</label>
                <input
                  type="text"
                  defaultValue="MILGARD EBS SPREADSHEET"
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block font-medium text-gray-700 mb-2">GL Date</label>
                <input
                  type="date"
                  defaultValue={new Date().toISOString().split('T')[0]}
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
            </div>
            <button
              onClick={handleAutoInvoiceImport}
              disabled={loading.invoice}
              className={`mt-4 px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${
                loading.invoice
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-green-500 hover:bg-green-600 text-white"
              }`}
            >
              {loading.invoice ? "Submitting..." : "Submit Auto Invoice Import"}
            </button>
          </div>
        </div>
      )}

      {/* Full Process Tab */}
      {activeOperation === "full" && (
        <div className="space-y-6">
          <div className="bg-purple-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-purple-800 mb-4">Complete FBDI Process</h3>
            <p className="text-purple-700 mb-4">This will execute all steps in sequence: Generate → Upload → Load Interface → Auto Invoice Import</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block font-medium text-gray-700 mb-2">Raw File</label>
                <input
                  type="file"
                  accept=".xlsx"
                  onChange={(e) => setRawFile(e.target.files[0])}
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
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
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div>
                <label className="block font-medium text-gray-700 mb-2">Environment</label>
                <input
                  type="text"
                  value={envType}
                  onChange={(e) => setEnvType(e.target.value)}
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>

            {/* Progress Steps */}
            {Object.keys(processProgress).length > 0 && (
              <div className="mb-6">
                <h4 className="font-semibold mb-3">Process Progress:</h4>
                <div className="space-y-2">
                  {[
                    { key: 'step1', label: '1. Generating FBDI File' },
                    { key: 'step2', label: '2. Uploading to UCM' },
                    { key: 'step3', label: '3. Loading Interface' },
                    { key: 'step4', label: '4. Running Auto Invoice Import' }
                  ].map((step) => (
                    <div key={step.key} className={`p-3 rounded-lg ${
                      processProgress[step.key] === 'completed' ? 'bg-green-100 text-green-800' :
                      processProgress[step.key] === 'active' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {step.label}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={handleFullProcess}
              disabled={loading.full}
              className={`px-6 py-3 rounded-lg font-semibold transition-all duration-300 ${
                loading.full
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-purple-500 hover:bg-purple-600 text-white"
              }`}
            >
              {loading.full ? "Processing..." : "Start Full Process"}
            </button>
          </div>
        </div>
      )}

      {/* Job Status Display */}
      {Object.keys(jobStatuses).length > 0 && (
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Job Status</h3>
          <div className="space-y-2">
            {Object.entries(jobStatuses).map(([operation, status]) => (
              <div key={operation} className="flex justify-between items-center p-2 bg-white rounded">
                <span className="font-medium">{operation.toUpperCase()}</span>
                <span className={`px-2 py-1 rounded text-sm ${
                  status.status === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {status.status} {status.jobId && `(Job ID: ${status.jobId})`}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FBDIOperations;

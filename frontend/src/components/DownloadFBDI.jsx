import React, { useState } from "react";
import { useFBDI } from "./FBDIGenerator3";
import { Download, Package, CheckCircle, AlertCircle, FileText, Settings, ArrowRight, Play } from "lucide-react";

const DownloadFBDI = () => {
  const {
    rawFile,
    setRawFile,
    selectedTemplate,
    setSelectedTemplate,
    projectName,
    setProjectName,
    envType,
    setEnvType,
    mappings,
    fbdiTemplates,
    // New workflow states
    workflowStep,
    setWorkflowStep,
    fbdiGenerationComplete,
    setFbdiGenerationComplete,
    generatedFbdiFile,
    setGeneratedFbdiFile
  } = useFBDI();

  const [loading, setLoading] = useState(false);

  const handleDownload = async () => {
    if (!rawFile || !selectedTemplate || !projectName || !envType) {
      alert("Please fill all fields before generating FBDI.");
      return;
    }

    const formData = new FormData();
    formData.append("raw_file", rawFile);
    formData.append("fbdi_type", selectedTemplate);
    formData.append("project_name", projectName);
    formData.append("env_type", envType);

    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/generate-fbdi-from-type", {
        method: "POST",
        body: formData,
      });

      const blob = await res.blob();
      
      // Store the generated file for later use
      setGeneratedFbdiFile({
        blob: blob,
        filename: `${projectName}_${selectedTemplate}_FBDI.zip`,
        projectName,
        selectedTemplate,
        envType
      });
      
      // Mark generation as complete
      setFbdiGenerationComplete(true);
      
    } catch (err) {
      alert("Failed to generate FBDI");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadFBDI = () => {
    if (generatedFbdiFile) {
      const url = window.URL.createObjectURL(generatedFbdiFile.blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = generatedFbdiFile.filename;
      a.click();
      window.URL.revokeObjectURL(url);
    }
  };

  const handleContinueNext = () => {
    setWorkflowStep('process');
  };

  // Show success state with two options
  if (fbdiGenerationComplete && generatedFbdiFile) {
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
              <h2 className="text-2xl font-semibold text-gray-900">FBDI Generated Successfully!</h2>
              <p className="text-gray-600 mt-1">Your FBDI package is ready. Choose your next action.</p>
            </div>
          </div>
        </div>

        {/* Generated File Info */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <Package className="w-6 h-6 text-green-600 mr-3" />
            <h3 className="text-lg font-medium text-green-800">Generated FBDI Package</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                <span className="text-sm font-medium text-gray-700">Project Name</span>
                <span className="text-sm text-gray-900">{generatedFbdiFile.projectName}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                <span className="text-sm font-medium text-gray-700">Template Type</span>
                <span className="text-sm text-gray-900">{generatedFbdiFile.selectedTemplate}</span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                <span className="text-sm font-medium text-gray-700">Environment</span>
                <span className="text-sm text-gray-900">{generatedFbdiFile.envType}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-white rounded-lg">
                <span className="text-sm font-medium text-gray-700">File Name</span>
                <span className="text-sm text-gray-900 font-mono">{generatedFbdiFile.filename}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Download Option */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Download className="w-8 h-8 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Download FBDI</h3>
              <p className="text-gray-600 mb-6">Download the generated FBDI package for manual upload</p>
              <button
                onClick={handleDownloadFBDI}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                <Download className="w-5 h-5 inline mr-2" />
                Download Package
              </button>
            </div>
          </div>

          {/* Continue Option */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Play className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Continue Processing</h3>
              <p className="text-gray-600 mb-6">Automatically proceed to FBDI Operations for Oracle Cloud processing</p>
              <button
                onClick={handleContinueNext}
                className="w-full bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
              >
                <ArrowRight className="w-5 h-5 inline mr-2" />
                Continue Next
              </button>
            </div>
          </div>
        </div>

        {/* Reset Option */}
        <div className="text-center">
          <button
            onClick={() => {
              setFbdiGenerationComplete(false);
              setGeneratedFbdiFile(null);
              setWorkflowStep('generate');
            }}
            className="text-gray-500 hover:text-gray-700 text-sm underline"
          >
            Start Over
          </button>
        </div>
      </div>
    );
  }

  // Original form (when not generated yet)
  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Package className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <div className="ml-4">
            <h2 className="text-2xl font-semibold text-gray-900">Generate FBDI Package</h2>
            <p className="text-gray-600 mt-1">Create a complete FBDI package ready for Oracle Cloud deployment</p>
          </div>
        </div>
      </div>

      {/* Show current configuration */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center mb-4">
          <Settings className="w-5 h-5 text-gray-600 mr-2" />
          <h3 className="text-lg font-medium text-gray-900">Configuration Summary</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Raw Data File</span>
              <div className="flex items-center">
                {rawFile ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span className="text-sm text-gray-900">{rawFile.name}</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-red-500 mr-2" />
                    <span className="text-sm text-gray-500">Not selected</span>
                  </>
                )}
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">FBDI Template</span>
              <div className="flex items-center">
                {selectedTemplate ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span className="text-sm text-gray-900">{selectedTemplate}</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-red-500 mr-2" />
                    <span className="text-sm text-gray-500">Not selected</span>
                  </>
                )}
              </div>
            </div>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Project Name</span>
              <div className="flex items-center">
                {projectName ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span className="text-sm text-gray-900">{projectName}</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-red-500 mr-2" />
                    <span className="text-sm text-gray-500">Not set</span>
                  </>
                )}
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Environment</span>
              <div className="flex items-center">
                {envType ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    <span className="text-sm text-gray-900">{envType}</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-red-500 mr-2" />
                    <span className="text-sm text-gray-500">Not set</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {mappings.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Column Mappings</span>
              <span className="text-sm text-gray-600">
                {mappings.filter(m => m.raw_column).length} of {mappings.length} columns mapped
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Configuration Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">Final Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Raw Data File
            </label>
            <input
              type="file"
              accept=".xlsx"
              onChange={(e) => setRawFile(e.target.files[0])}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              FBDI Template Type
            </label>
            <select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
            >
              {fbdiTemplates.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Project Name
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Enter project identifier"
              className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Environment Type
            </label>
            <select
              value={envType}
              onChange={(e) => setEnvType(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
            >
              <option value="">Select Environment</option>
              <option value="DEV">Development</option>
              <option value="TEST">Test</option>
              <option value="UAT">User Acceptance Testing</option>
              <option value="PROD">Production</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end pt-6 border-t border-gray-200 mt-6">
          <button
            onClick={handleDownload}
            disabled={loading || !rawFile || !selectedTemplate || !projectName || !envType}
            className={`inline-flex items-center px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
              loading || !rawFile || !selectedTemplate || !projectName || !envType
                ? "bg-gray-300 cursor-not-allowed text-gray-500"
                : "bg-green-600 hover:bg-green-700 text-white shadow-sm hover:shadow-md"
            }`}
          >
            <Download className="w-5 h-5 mr-2" />
            {loading ? "Generating..." : "Generate FBDI Package"}
          </button>
        </div>
      </div>

      {/* Information Section */}
      <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
        <div className="flex items-center mb-4">
          <Package className="w-5 h-5 text-blue-600 mr-2" />
          <h3 className="text-lg font-medium text-blue-900">Package Contents</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
            <div className="flex items-center text-blue-800">
              <CheckCircle className="w-4 h-4 mr-3 text-blue-600" />
              <span className="text-sm">Complete FBDI template with mapped data</span>
            </div>
            <div className="flex items-center text-blue-800">
              <CheckCircle className="w-4 h-4 mr-3 text-blue-600" />
              <span className="text-sm">Data validation and formatting applied</span>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center text-blue-800">
              <CheckCircle className="w-4 h-4 mr-3 text-blue-600" />
              <span className="text-sm">Ready-to-upload ZIP package</span>
            </div>
            <div className="flex items-center text-blue-800">
              <CheckCircle className="w-4 h-4 mr-3 text-blue-600" />
              <span className="text-sm">Configuration files and documentation</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DownloadFBDI;

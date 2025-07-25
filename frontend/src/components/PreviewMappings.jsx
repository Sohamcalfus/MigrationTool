import React, { useState } from "react";
import { useFBDI } from "./FBDIGenerator3";
import { Upload, Eye, CheckCircle, AlertCircle, FileText, XCircle } from "lucide-react";

const PreviewMappings = () => {
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
    setMappings,
    fbdiTemplates
  } = useFBDI();

  const [loading, setLoading] = useState(false);

  const handlePreview = async () => {
    if (!rawFile || !selectedTemplate || !projectName || !envType) {
      alert("Please fill all fields before preview.");
      return;
    }

    const formData = new FormData();
    formData.append("raw_file", rawFile);
    formData.append("fbdi_type", selectedTemplate);
    formData.append("project_name", projectName);
    formData.append("env_type", envType);

    setLoading(true);
    try {
      const res = await fetch("http://localhost:5000/preview-mappings", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setMappings(data.mappings || []);
    } catch (err) {
      alert("Failed to preview mappings");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <Eye className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <div className="ml-4">
            <h2 className="text-2xl font-semibold text-gray-900">Column Mapping Preview</h2>
            <p className="text-gray-600 mt-1">Upload your raw data file and preview how columns will be mapped to the FBDI template</p>
          </div>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">Configuration Settings</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">
              Raw Data File
            </label>
            <div className="relative">
              <input
                type="file"
                accept=".xlsx"
                onChange={(e) => setRawFile(e.target.files[0])}
                className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200"
              />
              <Upload className="absolute right-3 top-3 w-5 h-5 text-gray-400" />
            </div>
            {rawFile && (
              <div className="flex items-center mt-2 p-2 bg-green-50 rounded-lg">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                <span className="text-sm text-green-700">{rawFile.name}</span>
              </div>
            )}
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
                  {type} - {type === 'AR' ? 'Accounts Receivable' : type === 'AP' ? 'Accounts Payable' : type === 'GL' ? 'General Ledger' : 'Oracle Module'}
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
            onClick={handlePreview}
            disabled={loading || !rawFile || !selectedTemplate || !projectName || !envType}
            className={`inline-flex items-center px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
              loading || !rawFile || !selectedTemplate || !projectName || !envType
                ? "bg-gray-300 cursor-not-allowed text-gray-500"
                : "bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md"
            }`}
          >
            <Eye className="w-5 h-5 mr-2" />
            {loading ? "Analyzing..." : "Preview Mappings"}
          </button>
        </div>
      </div>

      {/* Mapping Preview */}
      {mappings.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <FileText className="w-6 h-6 text-blue-600 mr-3" />
              <h3 className="text-lg font-medium text-gray-900">Column Mapping Results</h3>
            </div>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                <span className="text-gray-600">Mapped: {mappings.filter(m => m.raw_column && m.raw_column !== "Not Mapped").length}</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                <span className="text-gray-600">Not Mapped: {mappings.filter(m => !m.raw_column || m.raw_column === "Not Mapped").length}</span>
              </div>
            </div>
          </div>
          
          <div className="overflow-hidden rounded-lg border border-gray-200">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Template Column</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Source Column</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {mappings.map((m, i) => {
                  const isMapped = m.raw_column && m.raw_column !== "Not Mapped";
                  
                  return (
                    <tr
                      key={i}
                      className={`${i % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-blue-50 transition-colors duration-150`}
                    >
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {m.template_column}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {isMapped ? m.raw_column : <span className="text-gray-400">Not mapped</span>}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {isMapped ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Mapped
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            <XCircle className="w-3 h-3 mr-1" />
                            Not Mapped
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default PreviewMappings;

import React, { useState } from "react";
import { useFBDI } from "./FBDIGenerator3";

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
    <div className="bg-white rounded-xl shadow-lg p-8 space-y-8">
      <div className="border-b border-gray-200 pb-4">
        <h2 className="text-3xl font-bold text-indigo-700 mb-2">Preview Column Mappings</h2>
        <p className="text-gray-600">Upload your raw data file and preview how columns will be mapped to the FBDI template</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="block font-semibold text-gray-700 text-sm uppercase tracking-wide">
            Raw File
          </label>
          <input
            type="file"
            accept=".xlsx"
            onChange={(e) => setRawFile(e.target.files[0])}
            className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200"
          />
          {rawFile && (
            <p className="text-sm text-green-600 mt-1">Selected: {rawFile.name}</p>
          )}
        </div>

        <div className="space-y-2">
          <label className="block font-semibold text-gray-700 text-sm uppercase tracking-wide">
            FBDI Type
          </label>
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200"
          >
            {fbdiTemplates.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <label className="block font-semibold text-gray-700 text-sm uppercase tracking-wide">
            Project Name
          </label>
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="Enter project name"
            className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200"
          />
        </div>

        <div className="space-y-2">
          <label className="block font-semibold text-gray-700 text-sm uppercase tracking-wide">
            Environment
          </label>
          <input
            type="text"
            value={envType}
            onChange={(e) => setEnvType(e.target.value)}
            placeholder="Enter environment type"
            className="w-full border-2 border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200"
          />
        </div>
      </div>

      <div className="flex justify-center pt-4">
        <button
          onClick={handlePreview}
          disabled={loading}
          className={`px-8 py-3 rounded-lg font-semibold shadow-md transition duration-300 transform hover:scale-105 ${
            loading
              ? "bg-gray-400 cursor-not-allowed text-white"
              : "bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white"
          }`}
        >
          {loading ? "Loading Preview..." : "Preview Column Mappings"}
        </button>
      </div>

      {/* Mapping Preview */}
      {mappings.length > 0 && (
        <div className="mt-8 bg-gray-50 rounded-lg p-6">
          <h3 className="text-2xl font-semibold mb-4 text-indigo-700 flex items-center">
            Column Mappings Preview
          </h3>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full text-sm">
              <thead className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">Template Column</th>
                  <th className="px-4 py-3 text-left font-semibold">Raw Column</th>
                  <th className="px-4 py-3 text-left font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white">
                {mappings.map((m, i) => (
                  <tr
                    key={i}
                    className={`${
                      i % 2 === 0 ? "bg-white" : "bg-indigo-50"
                    } hover:bg-indigo-100 transition duration-200`}
                  >
                    <td className="px-4 py-3 border-b border-gray-200 font-medium">
                      {m.template_column}
                    </td>
                    <td className="px-4 py-3 border-b border-gray-200 text-gray-600">
                      {m.raw_column || "—"}
                    </td>
                    <td className="px-4 py-3 border-b border-gray-200">
                      {m.raw_column ? (
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                          Mapped
                        </span>
                      ) : (
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
                          Not Mapped
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 text-sm text-gray-600">
            <p>
              <strong>Mapped:</strong> {mappings.filter(m => m.raw_column).length} columns | 
              <strong> Not Mapped:</strong> {mappings.filter(m => !m.raw_column).length} columns
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default PreviewMappings;

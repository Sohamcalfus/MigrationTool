import React, { useState } from "react";

const FBDIGenerator3 = () => {
  const [rawFile, setRawFile] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState("AR");
  const [projectName, setProjectName] = useState("");
  const [envType, setEnvType] = useState("");
  const [mappings, setMappings] = useState([]);
  const [loading, setLoading] = useState(false);

  const fbdiTemplates = [
    "AR", "AP", "GL", "FA", "CM", "EX", "TX", "INV", "PO",
    "OM", "PIM", "MF", "CST", "WMS", "HR", "PY", "WFM", "TM", "CMP"
  ];

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

    try {
      const res = await fetch("http://localhost:5000/preview-mappings", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setMappings(data.mappings || []);
    } catch (err) {
      alert("Failed to preview mappings");
    }
  };

  const handleDownload = async () => {
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
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "fbdi_output.zip";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to generate FBDI");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-xl font-bold">FBDI Generator</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block font-medium mb-1">Raw File</label>
          <input type="file" accept=".xlsx" onChange={(e) => setRawFile(e.target.files[0])} />
        </div>

        <div>
          <label className="block font-medium mb-1">FBDI Type</label>
          <select
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            className="w-full border p-2 rounded"
          >
            {fbdiTemplates.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block font-medium mb-1">Project Name</label>
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            className="w-full border p-2 rounded"
          />
        </div>

        <div>
          <label className="block font-medium mb-1">Environment</label>
          <input
            type="text"
            value={envType}
            onChange={(e) => setEnvType(e.target.value)}
            className="w-full border p-2 rounded"
          />
        </div>
      </div>

      <div className="flex space-x-4 mt-4">
        <button
          onClick={handlePreview}
          className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded"
        >
          Preview Mappings
        </button>
        <button
          onClick={handleDownload}
          disabled={loading}
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
        >
          {loading ? "Generating..." : "Download FBDI"}
        </button>
      </div>

      {/* Mapping Preview */}
      {mappings.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-2">Column Mappings</h3>
          <table className="w-full border text-sm">
            <thead>
              <tr className="bg-gray-200">
                <th className="border px-2 py-1">Template Column</th>
                <th className="border px-2 py-1">Raw Column</th>
              </tr>
            </thead>
            <tbody>
              {mappings.map((m, i) => (
                <tr key={i}>
                  <td className="border px-2 py-1">{m.template_column}</td>
                  <td className="border px-2 py-1">{m.raw_column || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default FBDIGenerator3;

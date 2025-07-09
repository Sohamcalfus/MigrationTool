import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Download, Loader2 } from 'lucide-react';

const FBDIUploader = () => {
  const [templateFile, setTemplateFile] = useState(null);
  const [rawFile, setRawFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [processingMode, setProcessingMode] = useState('new');
  const [mappingsGenerated, setMappingsGenerated] = useState(false);
  const [lastMappingResult, setLastMappingResult] = useState(null);

  const handleGenerateMappings = async (e) => {
    e.preventDefault();
    if (!templateFile || !rawFile) {
      alert('Please upload both files.');
      return;
    }

    const formData = new FormData();
    formData.append('template_file', templateFile);
    formData.append('raw_file', rawFile);

    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/generate-mappings-only', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate mappings');
      }

      const result = await response.json();
      setMappingsGenerated(true);
      setLastMappingResult(result);
     
      alert(`✓ Mappings generated successfully!
      - ${result.successful_mappings} columns mapped
      - ${result.failed_mappings} columns unmapped
     
      Please review the mappings in the "View Mappings" tab before downloading.`);

    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadFBDI = async (e) => {
    e.preventDefault();
    if (!templateFile || !rawFile) {
      alert('Please upload both files.');
      return;
    }

    const formData = new FormData();
    formData.append('template_file', templateFile);
    formData.append('raw_file', rawFile);

    setLoading(true);
    try {
      const endpoint = processingMode === 'new'
        ? 'http://localhost:5000/generate-fbdi'
        : 'http://localhost:5000/generate-fbdi-from-table';

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate FBDI file');
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = processingMode === 'new'
        ? 'fbdi_output.zip'
        : 'fbdi_output_from_table.zip';
      document.body.appendChild(a);
      a.click();
      a.remove();

      alert('✓ FBDI file downloaded successfully!');

    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const FileUploadCard = ({ title, file, setFile, accept, icon: Icon }) => (
    <div className="card p-6">
      <div className="flex items-center mb-4">
        <Icon className="h-6 w-6 text-primary-600 mr-2" />
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      </div>
      <input
        type="file"
        accept={accept}
        onChange={(e) => setFile(e.target.files[0])}
        className="input-field"
      />
      {file && (
        <div className="mt-3 flex items-center text-green-600">
          <CheckCircle className="h-4 w-4 mr-2" />
          <span className="text-sm">Selected: {file.name}</span>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-8">
      {/* Processing Mode Selection */}
      <div className="card p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Processing Mode</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <label className={`cursor-pointer p-4 rounded-lg border-2 transition-all ${
            processingMode === 'new'
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-200 hover:border-gray-300'
          }`}>
            <input
              type="radio"
              name="processingMode"
              value="new"
              checked={processingMode === 'new'}
              onChange={(e) => setProcessingMode(e.target.value)}
              className="sr-only"
            />
            <div className="flex items-start">
              <div className={`w-4 h-4 rounded-full border-2 mr-3 mt-1 ${
                processingMode === 'new' ? 'border-primary-500 bg-primary-500' : 'border-gray-300'
              }`}>
                {processingMode === 'new' && (
                  <div className="w-full h-full rounded-full bg-white scale-50"></div>
                )}
              </div>
              <div>
                <h3 className="font-medium text-gray-900">Create New Mapping</h3>
                <p className="text-sm text-gray-600">Discover and store new column mappings</p>
              </div>
            </div>
          </label>

          <label className={`cursor-pointer p-4 rounded-lg border-2 transition-all ${
            processingMode === 'fromTable'
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-200 hover:border-gray-300'
          }`}>
            <input
              type="radio"
              name="processingMode"
              value="fromTable"
              checked={processingMode === 'fromTable'}
              onChange={(e) => setProcessingMode(e.target.value)}
              className="sr-only"
            />
            <div className="flex items-start">
              <div className={`w-4 h-4 rounded-full border-2 mr-3 mt-1 ${
                processingMode === 'fromTable' ? 'border-primary-500 bg-primary-500' : 'border-gray-300'
              }`}>
                {processingMode === 'fromTable' && (
                  <div className="w-full h-full rounded-full bg-white scale-50"></div>
                )}
              </div>
              <div>
                <h3 className="font-medium text-gray-900">Use Stored Mappings</h3>
                <p className="text-sm text-gray-600">Apply existing mappings from database</p>
              </div>
            </div>
          </label>
        </div>
      </div>

      {/* File Upload Section */}
      <div className="grid md:grid-cols-2 gap-6">
        <FileUploadCard
          title="Template File (.xlsm)"
          file={templateFile}
          setFile={setTemplateFile}
          accept=".xlsm"
          icon={FileText}
        />
        <FileUploadCard
          title="Raw Data File (.xlsx)"
          file={rawFile}
          setFile={setRawFile}
          accept=".xlsx"
          icon={Upload}
        />
      </div>

      {/* Action Buttons */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Step 1: Generate Mappings */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <div className="w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-semibold mr-3">
              1
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Generate Mappings</h3>
          </div>
          <p className="text-gray-600 mb-4">
            {processingMode === 'new'
              ? 'Create new column mappings and store them in the database.'
              : 'This step is not needed when using stored mappings.'
            }
          </p>
          <button
            onClick={handleGenerateMappings}
            disabled={loading || processingMode === 'fromTable'}
            className={`w-full flex items-center justify-center py-3 px-4 rounded-lg font-medium transition-all ${
              processingMode === 'fromTable'
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'btn-primary hover:shadow-lg'
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                Generating Mappings...
              </>
            ) : (
              <>
                <CheckCircle className="h-5 w-5 mr-2" />
                Generate Mappings
              </>
            )}
          </button>
          {mappingsGenerated && lastMappingResult && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center text-green-800">
                <CheckCircle className="h-4 w-4 mr-2" />
                <span className="text-sm font-medium">Mappings Generated!</span>
              </div>
              <div className="text-sm text-green-700 mt-1">
                ✓ {lastMappingResult.successful_mappings} mapped,
                ✗ {lastMappingResult.failed_mappings} unmapped
              </div>
            </div>
          )}
        </div>

        {/* Step 2: Download FBDI */}
        <div className="card p-6">
          <div className="flex items-center mb-4">
            <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-semibold mr-3">
              2
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Download FBDI</h3>
          </div>
          <p className="text-gray-600 mb-4">
            {processingMode === 'new'
              ? 'Download the FBDI file using generated mappings.'
              : 'Download the FBDI file using stored mappings from database.'
            }
          </p>
          <button
            onClick={handleDownloadFBDI}
            disabled={loading || (processingMode === 'new' && !mappingsGenerated)}
            className={`w-full flex items-center justify-center py-3 px-4 rounded-lg font-medium transition-all ${
              (processingMode === 'new' && !mappingsGenerated)
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700 text-white hover:shadow-lg'
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                Generating File...
              </>
            ) : (
              <>
                <Download className="h-5 w-5 mr-2" />
                Download FBDI File
              </>
            )}
          </button>
          {processingMode === 'new' && !mappingsGenerated && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center text-yellow-800">
                <AlertCircle className="h-4 w-4 mr-2" />
                <span className="text-sm">Generate mappings first before downloading.</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Workflow Instructions */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Workflow Instructions</h3>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          {processingMode === 'new' ? (
            <ol className="list-decimal list-inside space-y-2 text-blue-800">
              <li>Upload your template and raw files</li>
              <li>Click "Generate Mappings" to create column mappings</li>
              <li>Go to "View Mappings" tab to review the mappings</li>
              <li>Return here and click "Download FBDI File" to get your processed file</li>
            </ol>
          ) : (
            <ol className="list-decimal list-inside space-y-2 text-blue-800">
              <li>Upload your template and raw files</li>
              <li>Click "Download FBDI File" to apply stored mappings and download</li>
              <li>Use "View Mappings" tab to see which mappings were applied</li>
            </ol>
          )}
        </div>
      </div>
    </div>
  );
};

export default FBDIUploader;
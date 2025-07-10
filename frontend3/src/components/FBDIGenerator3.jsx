import React, { createContext, useContext, useState } from 'react';

const FBDIContext = createContext();

export const useFBDI = () => {
  const context = useContext(FBDIContext);
  if (!context) {
    throw new Error('useFBDI must be used within FBDIProvider');
  }
  return context;
};

export const FBDIProvider = ({ children }) => {
  const [rawFile, setRawFile] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState("AR");
  const [projectName, setProjectName] = useState("");
  const [envType, setEnvType] = useState("");
  const [mappings, setMappings] = useState([]);

  const fbdiTemplates = [
    "AR", "AP", "GL", "FA", "CM", "EX", "TX", "INV", "PO",
    "OM", "PIM", "MF", "CST", "WMS", "HR", "PY", "WFM", "TM", "CMP"
  ];

  const value = {
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
  };

  return (
    <FBDIContext.Provider value={value}>
      {children}
    </FBDIContext.Provider>
  );
};

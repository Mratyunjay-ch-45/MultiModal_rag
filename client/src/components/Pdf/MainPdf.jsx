import React, { useState, lazy, Suspense } from 'react';
import axios from 'axios';
import { Worker } from '@react-pdf-viewer/core';
import { Viewer } from '@react-pdf-viewer/core';
import { highlightPlugin } from '@react-pdf-viewer/highlight';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/highlight/lib/styles/index.css';

const MainPdf = () => {
  const [file, setFile] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [isUploaded, setIsUploaded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [highlights, setHighlights] = useState([]);

  // Initialize the highlight plugin
  const highlightPluginInstance = highlightPlugin();
  const { jumpToHighlightArea } = highlightPluginInstance;

  // Handle file selection
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPdfUrl(URL.createObjectURL(selectedFile));
      setFileId(null);
      setIsUploaded(false);
      setHighlights([]);
    }
  };

  // Upload the selected PDF to the backend
  const handleUpload = async () => {
    if (!file) {
      alert('Please select a PDF file first.');
      return;
    }

    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post('http://localhost:8000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      console.log('Upload response:', res.data);

      if (res.data.file_id) {
        setFileId(res.data.file_id);
        setIsUploaded(true);
        alert('File uploaded successfully!');
      } else {
        alert('Upload successful, but no file ID returned.');
      }
    } catch (error) {
      console.error('Upload error:', error.response?.data || error.message);
      alert('Error uploading PDF.');
    } finally {
      setIsLoading(false);
    }
  };

  // Submit a query to the backend
  const handleQuery = async () => {
    if (!query.trim()) {
      alert('Please enter a query.');
      return;
    }

    if (!isUploaded) {
      alert('Please upload a PDF before submitting a query.');
      return;
    }

    setIsLoading(true);
    try {
      const res = await axios.post(
        'http://localhost:8000/query',
        { query, file_id: fileId },
        { headers: { 'Content-Type': 'application/json' } }
      );

      setResponse(res.data);

      // Map relevant documents to highlights
      const newHighlights = res.data.relevant_docs.map((doc) => ({
        pageIndex: doc.page - 1, // Page index starts at 0
        content: doc.preview,
        highlightAreas: [
          // You need to calculate these bounding boxes based on your PDF content.
          // For now, we'll assume some placeholder values.
          { top: 10, left: 10, height: 20, width: 200 },
        ],
      }));

      setHighlights(newHighlights);

      // Jump to the first highlight automatically
      if (newHighlights.length > 0) {
        jumpToHighlightArea(newHighlights[0].pageIndex, newHighlights[0].highlightAreas[0]);
      }
    } catch (error) {
      console.error('Query error:', error.response?.data || error.message);
      alert(error.response?.data?.detail || 'Error querying PDF.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>AI PDF Query System</h1>

      {/* File Upload Section */}
      <div className="upload-section">
        <input type="file" accept="application/pdf" onChange={handleFileChange} />
        <button onClick={handleUpload} disabled={isLoading || !file}>
          {isLoading ? 'Uploading...' : 'Upload PDF'}
        </button>
        {isUploaded && <span>File uploaded successfully!</span>}
      </div>

      {/* Query Submission Section */}
      <div className="query-section">
        <input
          type="text"
          placeholder="Enter your query..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button onClick={handleQuery} disabled={isLoading || !isUploaded}>
          {isLoading ? 'Querying...' : 'Submit Query'}
        </button>
      </div>

      {/* AI Response Section */}
      {response && (
        <div className="response-section">
          <h2>AI Answer:</h2>
          <p>{response.answer}</p>
          <h3>Relevant Documents:</h3>
          {response.relevant_docs.map((doc, index) => (
            <div key={index} className="document-preview">
              <strong>Page {doc.page}:</strong> {doc.preview}
            </div>
          ))}
        </div>
      )}

      {/* PDF Preview Section */}
      {pdfUrl && (
        <div className="pdf-viewer-section" style={{ height: '100vh' }}>
          <h2>PDF Preview</h2>
          <Suspense fallback={<div>Loading PDF Viewer...</div>}>
            <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
              <Viewer
                fileUrl={pdfUrl}
                plugins={[
                  highlightPluginInstance,
                ]}
              />
            </Worker>
          </Suspense>
        </div>
      )}
    </div>
  );
};

export default MainPdf;

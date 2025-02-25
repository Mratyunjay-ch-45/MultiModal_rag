// App.js
import React, { useState, lazy, Suspense } from 'react';
import axios from 'axios';


// Lazy load the Worker and Viewer components from @react-pdf-viewer/core
const Worker = lazy(() =>
  import('@react-pdf-viewer/core').then((mod) => ({ default: mod.Worker }))
);
const Viewer = lazy(() =>
  import('@react-pdf-viewer/core').then((mod) => ({ default: mod.Viewer }))
);

const MainPdf = () => {
  const [file, setFile] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [highlightedPages, setHighlightedPages] = useState([]);

  // Handle file selection from the file input
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    if (selectedFile) {
      // Create a local URL for PDF preview
      setPdfUrl(URL.createObjectURL(selectedFile));
    }
  };

  // Upload the selected PDF to the backend
  const handleUpload = async () => {
    if (!file) {
      alert('Please select a PDF file first.');
      return;
    }
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post('http://localhost:8000/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      alert('File uploaded and processed successfully!');
      console.log('Upload response:', res.data);
    } catch (error) {
      console.error('Upload error:', error);
      alert('Error uploading PDF.');
    }
  };

  // Submit the query to the backend and update the response state
  const handleQuery = async () => {
    if (!query) {
      alert('Please enter a query.');
      return;
    }
    const formData = new FormData();
    formData.append('query', query);

    try {
      const res = await axios.post('http://localhost:8000/query/', formData);
      setResponse(res.data);
      // Assuming backend returns response.documents with a "page" property
      const pages = res.data.documents.map((doc) => doc.page);
      setHighlightedPages(pages);
    } catch (error) {
      console.error('Query error:', error);
      alert('Error querying PDF.');
    }
  };

  return (
    <div className="App">
      <h1>AI PDF Query System</h1>

      {/* File Upload Section */}
      <div className="upload-section">
        <input type="file" accept="application/pdf" onChange={handleFileChange} />
        <button onClick={handleUpload}>Upload PDF</button>
      </div>

      {/* Query Submission Section */}
      <div className="query-section">
        <input
          type="text"
          placeholder="Enter your query..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button onClick={handleQuery}>Submit Query</button>
      </div>

      {/* AI Response Section */}
      {response && (
        <div className="response-section">
          <h2>AI Answer:</h2>
          <p>{response.answer}</p>
          <h3>Relevant Pages:</h3>
          {response.documents.map((doc, index) => (
            <div key={index} className="document-preview">
              <strong>Page {doc.page}:</strong> {doc.content.substring(0, 200)}...
            </div>
          ))}
        </div>
      )}

      {/* PDF Preview Section */}
      {pdfUrl && (
        <div className="pdf-viewer-section">
          <h2>PDF Preview</h2>
          <Suspense fallback={<div>Loading PDF Viewer...</div>}>
            {/* The Worker component sets up the PDF.js worker */}
            <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
              {/* The Viewer component displays the PDF */}
              <Viewer fileUrl={pdfUrl} />
            </Worker>
          </Suspense>
        </div>
      )}
    </div>
  );
};

export default MainPdf;

import React, { useState } from 'react';
import FileUploader from '../../components/upload/FileUploader';
import DocumentList from '../../components/upload/DocumentList';
import { Document } from '../../services/api/documentService';

const UploadPage: React.FC = () => {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [uploadMode, setUploadMode] = useState<'single' | 'bulk'>('single');

  const handleUploadComplete = (success: boolean) => {
    if (success) {
      setRefreshTrigger(prev => prev + 1);
    }
  };

  const handleDocumentSelect = (document: Document) => {
    setSelectedDocument(document);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Document Upload</h1>
        <p className="text-gray-600">
          Upload PDF documents for processing. Both scanned and searchable PDFs are supported.
        </p>
      </div>

      <div className="bg-white shadow rounded-lg p-6 mb-8">
        <div className="mb-4">
          <div className="flex space-x-4 mb-4">
            <button
              className={`px-4 py-2 rounded-md ${
                uploadMode === 'single'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              onClick={() => setUploadMode('single')}
            >
              Single Upload
            </button>
            <button
              className={`px-4 py-2 rounded-md ${
                uploadMode === 'bulk'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              onClick={() => setUploadMode('bulk')}
            >
              Bulk Upload
            </button>
          </div>
          
          <FileUploader 
            onUploadComplete={handleUploadComplete} 
            multiple={uploadMode === 'bulk'} 
          />
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Documents</h2>
        <DocumentList 
          onDocumentSelect={handleDocumentSelect} 
          refreshTrigger={refreshTrigger} 
        />
      </div>

      {selectedDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Document Details
                </h3>
                <button
                  onClick={() => setSelectedDocument(null)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <span className="sr-only">Close</span>
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-500">Name</h4>
                  <p className="mt-1">{selectedDocument.name}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">File Type</h4>
                    <p className="mt-1 capitalize">{selectedDocument.file_type}</p>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Status</h4>
                    <p className="mt-1 capitalize">{selectedDocument.status}</p>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Pages</h4>
                    <p className="mt-1">{selectedDocument.page_count}</p>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-500">Uploaded</h4>
                    <p className="mt-1">{new Date(selectedDocument.created_at).toLocaleString()}</p>
                  </div>
                </div>
                
                <div className="pt-4 flex justify-end">
                  <button
                    onClick={() => setSelectedDocument(null)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadPage;

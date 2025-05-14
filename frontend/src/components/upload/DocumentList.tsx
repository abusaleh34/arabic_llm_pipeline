import React, { useState, useEffect } from 'react';
import documentService, { Document } from '../../services/api/documentService';

interface DocumentListProps {
  onDocumentSelect?: (document: Document) => void;
  refreshTrigger?: number;
}

const DocumentList: React.FC<DocumentListProps> = ({ 
  onDocumentSelect,
  refreshTrigger = 0
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const limit = 10;

  const loadDocuments = async (reset = false) => {
    try {
      setLoading(true);
      setError(null);
      
      const newPage = reset ? 0 : page;
      const response = await documentService.listDocuments(newPage * limit, limit);
      
      if (reset) {
        setDocuments(response.items);
      } else {
        setDocuments(prev => [...prev, ...response.items]);
      }
      
      setHasMore(response.items.length === limit);
      if (!reset) {
        setPage(prev => prev + 1);
      } else {
        setPage(1);
      }
    } catch (err) {
      console.error('Error loading documents:', err);
      setError('Failed to load documents. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments(true);
  }, [refreshTrigger]);

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }
    
    try {
      await documentService.deleteDocument(id);
      setDocuments(prev => prev.filter(doc => doc.id !== id));
    } catch (err) {
      console.error('Error deleting document:', err);
      alert('Failed to delete document. Please try again.');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusBadgeColor = (status: string): string => {
    switch (status) {
      case 'uploaded':
        return 'bg-blue-100 text-blue-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'processed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="w-full">
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}

      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
        <table className="min-w-full divide-y divide-gray-300">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                Name
              </th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                Size
              </th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                Pages
              </th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                Type
              </th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                Status
              </th>
              <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                Uploaded
              </th>
              <th scope="col" className="relative px-3 py-3.5">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {documents.length === 0 && !loading ? (
              <tr>
                <td colSpan={7} className="px-3 py-4 text-sm text-gray-500 text-center">
                  No documents found. Upload some documents to get started.
                </td>
              </tr>
            ) : (
              documents.map(doc => (
                <tr 
                  key={doc.id} 
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => onDocumentSelect && onDocumentSelect(doc)}
                >
                  <td className="whitespace-nowrap px-3 py-4 text-sm font-medium text-gray-900">
                    {doc.name}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                    {formatFileSize(doc.file_size)}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                    {doc.page_count}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 capitalize">
                    {doc.file_type}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm">
                    <span className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${getStatusBadgeColor(doc.status)} capitalize`}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-right">
                    <button
                      onClick={(e) => handleDelete(doc.id, e)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {loading && (
        <div className="flex justify-center my-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      )}

      {hasMore && !loading && (
        <div className="flex justify-center mt-4">
          <button
            onClick={() => loadDocuments()}
            className="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Load More
          </button>
        </div>
      )}
    </div>
  );
};

export default DocumentList;

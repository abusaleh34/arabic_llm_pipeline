import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_ENDPOINT = `${API_URL}/api/documents`;

export interface Document {
  id: number;
  name: string;
  file_path: string;
  file_size: number;
  file_type: 'scanned' | 'searchable' | 'unknown';
  page_count: number;
  status: 'uploaded' | 'processing' | 'processed' | 'failed';
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  items: Document[];
  total: number;
}

const documentService = {
  uploadDocument: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API_ENDPOINT}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },
  
  bulkUploadDocuments: async (files: File[]): Promise<Document[]> => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    const response = await axios.post(`${API_ENDPOINT}/bulk-upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },
  
  getDocument: async (id: number): Promise<Document> => {
    const response = await axios.get(`${API_ENDPOINT}/${id}`);
    return response.data;
  },
  
  listDocuments: async (skip = 0, limit = 100): Promise<DocumentListResponse> => {
    const response = await axios.get(`${API_ENDPOINT}?skip=${skip}&limit=${limit}`);
    return response.data;
  },
  
  deleteDocument: async (id: number): Promise<boolean> => {
    const response = await axios.delete(`${API_ENDPOINT}/${id}`);
    return response.data.success;
  },
};

export default documentService;

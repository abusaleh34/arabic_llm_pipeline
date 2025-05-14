import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import documentService from '../../services/api/documentService';

interface FileUploaderProps {
  onUploadComplete: (success: boolean) => void;
  multiple?: boolean;
}

const FileUploader: React.FC<FileUploaderProps> = ({ 
  onUploadComplete, 
  multiple = false 
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const invalidFiles = acceptedFiles.filter(
      file => file.type !== 'application/pdf'
    );

    if (invalidFiles.length > 0) {
      setError('Only PDF files are allowed');
      return;
    }

    setUploading(true);
    setError(null);
    
    try {
      if (multiple) {
        await documentService.bulkUploadDocuments(acceptedFiles);
      } else {
        await documentService.uploadDocument(acceptedFiles[0]);
      }
      
      onUploadComplete(true);
    } catch (err) {
      console.error('Upload error:', err);
      setError('Failed to upload file(s). Please try again.');
      onUploadComplete(false);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  }, [multiple, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple
  });

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
        }`}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center justify-center space-y-2">
          <svg
            className="w-12 h-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          
          <p className="text-lg font-medium text-gray-700">
            {isDragActive
              ? 'Drop the files here...'
              : multiple
              ? 'Drag & drop PDF files here, or click to select files'
              : 'Drag & drop a PDF file here, or click to select a file'}
          </p>
          
          <p className="text-sm text-gray-500">
            Only PDF files are supported
          </p>
        </div>
      </div>

      {uploading && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-600 h-2.5 rounded-full"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600 mt-1">Uploading...</p>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}
    </div>
  );
};

export default FileUploader;

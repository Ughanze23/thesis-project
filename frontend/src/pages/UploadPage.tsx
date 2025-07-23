import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  DocumentArrowUpIcon, 
  CheckCircleIcon, 
  ExclamationCircleIcon,
  ClockIcon,
  ChartBarIcon,
  PlayCircleIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';
import { useAudit, UploadData } from '../context/AuditContext';
import { apiService } from '../services/api';

export function UploadPage() {
  const { state, actions } = useAudit();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStage, setProcessingStage] = useState('');
  const [recentUpload, setRecentUpload] = useState<UploadData | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (selectedFile: File) => {
    // Validate file type
    if (!selectedFile.name.toLowerCase().endsWith('.csv')) {
      actions.setError('Please upload a CSV file');
      return;
    }
    
    if (selectedFile.size > 1000 * 1024 * 1024) {
      actions.setError('File size must be less than 1000MB');
      return;
    }

    setFile(selectedFile);
    actions.setError(null);
  };

  const processUpload = async () => {
    if (!file) return;

    setUploadStatus('processing');
    setUploadProgress(0);
    actions.setLoading(true);

    try {
      // Stage 1: Starting upload
      setProcessingStage('Starting upload...');
      setUploadProgress(10);
      await new Promise(resolve => setTimeout(resolve, 500));

      // Stage 2: Uploading to backend
      setProcessingStage('Uploading file to backend...');
      setUploadProgress(30);
      
      const response = await apiService.uploadDataset(file);
      
      // Stage 3: Backend processing
      setProcessingStage('Backend processing file...');
      setUploadProgress(60);
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Stage 4: Finalizing
      setProcessingStage('Finalizing upload...');
      setUploadProgress(90);
      await new Promise(resolve => setTimeout(resolve, 500));

      // Complete
      setUploadProgress(100);
      setProcessingStage('Upload complete!');

      // Convert API response to UploadData format
      const uploadData: UploadData = {
        uploadId: response.upload_data.upload_id,
        userId: response.upload_data.user_id,
        fileName: response.upload_data.filename,
        totalBlocks: response.upload_data.total_blocks,
        dataBlocks: response.upload_data.data_blocks,
        rootHash: response.upload_data.root_hash,
        timestamp: response.upload_data.timestamp,
        sizeMB: response.upload_data.file_size_mb,
      };

      actions.addUpload(uploadData);
      setRecentUpload(uploadData);
      setUploadStatus('success');
      
      // Reset after 5 seconds (extended to give time for audit button)
      setTimeout(() => {
        setUploadStatus('idle');
        setFile(null);
        setUploadProgress(0);
        setProcessingStage('');
        setRecentUpload(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }, 5000);

    } catch (error) {
      console.error('Upload failed:', error);
      actions.setError(`Upload failed: ${error}`);
      setUploadStatus('error');
    } finally {
      actions.setLoading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <DocumentArrowUpIcon className="h-12 w-12 text-blue-600 mx-auto mb-4" />
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Upload Dataset
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Upload your CSV dataset to prepare it for zero-knowledge integrity auditing.
          Files will be split into secure blocks and prepared for verification.
        </p>
      </div>

      {/* Upload Area */}
      <div className="audit-card">
        <div
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive 
              ? 'border-blue-500 bg-blue-50' 
              : uploadStatus === 'success'
              ? 'border-green-500 bg-green-50'
              : uploadStatus === 'error'
              ? 'border-red-500 bg-red-50'
              : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileSelect}
            className="hidden"
          />

          {uploadStatus === 'idle' && (
            <>
              <DocumentArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {file ? file.name : 'Choose a CSV file or drag it here'}
              </h3>
              <p className="text-gray-600 mb-4">
                {file 
                  ? `File size: ${formatFileSize(file.size)}`
                  : ''
                }
              </p>
              <div className="space-x-4">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Choose File
                </button>
                {file && (
                  <button
                    onClick={processUpload}
                    className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Process Upload
                  </button>
                )}
              </div>
            </>
          )}

          {uploadStatus === 'processing' && (
            <div className="space-y-4">
              <div className="loading-spinner mx-auto"></div>
              <h3 className="text-lg font-semibold text-blue-900">
                {processingStage}
              </h3>
              <div className="progress-bar">
                <div 
                  className="progress-bar-fill"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-600">
                {uploadProgress}% complete
              </p>
            </div>
          )}

          {uploadStatus === 'success' && (
            <div className="space-y-4">
              <CheckCircleIcon className="h-12 w-12 text-green-600 mx-auto" />
              <h3 className="text-lg font-semibold text-green-900">
                Upload Successful!
              </h3>
              <p className="text-gray-600 mb-4">
                Your dataset has been processed and is ready for auditing.
              </p>
              {recentUpload && (
                <div className="flex flex-col sm:flex-row items-center justify-center space-y-2 sm:space-y-0 sm:space-x-4">
                  <button
                    onClick={() => navigate('/audit')}
                    className="flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-md"
                  >
                    <PlayCircleIcon className="h-5 w-5" />
                    <span>Start Audit</span>
                    <ArrowRightIcon className="h-4 w-4" />
                  </button>
                  <span className="text-gray-500 text-sm">or</span>
                  <button
                    onClick={() => navigate('/upload')}
                    className="text-blue-600 hover:text-blue-700 text-sm font-medium underline"
                  >
                    Upload Another File
                  </button>
                </div>
              )}
            </div>
          )}

          {uploadStatus === 'error' && (
            <div className="space-y-4">
              <ExclamationCircleIcon className="h-12 w-12 text-red-600 mx-auto" />
              <h3 className="text-lg font-semibold text-red-900">
                Upload Failed
              </h3>
              <p className="text-gray-600">
                {state.error || 'An error occurred during upload.'}
              </p>
              <button
                onClick={() => setUploadStatus('idle')}
                className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Upload Requirements */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="metric-card">
          <div className="flex items-center space-x-3 mb-3">
            <DocumentArrowUpIcon className="h-6 w-6 text-blue-600" />
            <h3 className="font-semibold text-gray-900">File Format</h3>
          </div>
          <p className="text-sm text-gray-600">
            CSV files with transaction or financial data.
            Headers will be preserved during block splitting.
          </p>
        </div>

        <div className="metric-card">
          <div className="flex items-center space-x-3 mb-3">
            <ChartBarIcon className="h-6 w-6 text-blue-600" />
            <h3 className="font-semibold text-gray-900">Block Size</h3>
          </div>
          <p className="text-sm text-gray-600">
            Files are split into 2MB blocks automatically.
            Total blocks rounded to next power of 2.
          </p>
        </div>

        <div className="metric-card">
          <div className="flex items-center space-x-3 mb-3">
            <ClockIcon className="h-6 w-6 text-blue-600" />
            <h3 className="font-semibold text-gray-900">Processing Time</h3>
          </div>
          <p className="text-sm text-gray-600">
            Typical processing: less than 1 minute for files up to 50MB.
            Merkle tree generation is the longest step.
          </p>
        </div>
      </div>

      {/* Recent Uploads */}
      {state.uploads.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Recent Uploads
          </h2>
          <div className="space-y-4">
            {state.uploads.slice(-5).reverse().map((upload) => (
              <div key={upload.uploadId} className="audit-card">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {upload.fileName}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {upload.totalBlocks} blocks • {upload.sizeMB.toFixed(2)} MB • Root: {upload.rootHash}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="status-success">
                      Ready
                    </div>
                    <p className="text-sm text-gray-500 mt-1">
                      {new Date(upload.timestamp).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
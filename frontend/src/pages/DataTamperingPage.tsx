import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAudit } from '../context/AuditContext';
import { apiService } from '../services/api';
import { DataViewer } from '../components/DataViewer';
import { DataEditor } from '../components/DataEditor';

interface BlockInfo {
  block_id: string;
  file_path: string;
  size_bytes: number;
  modified: string;
}

interface BlockData {
  upload_id: string;
  block_id: string;
  columns: string[];
  data: Record<string, any>[];
  row_count: number;
  file_path: string;
}

export function DataTamperingPage() {
  const { state, actions } = useAudit();
  const navigate = useNavigate();
  const [selectedUpload, setSelectedUpload] = useState<string>('');
  const [blocks, setBlocks] = useState<BlockInfo[]>([]);
  const [selectedBlock, setSelectedBlock] = useState<string>('');
  const [blockData, setBlockData] = useState<BlockData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [isStartingAudit, setIsStartingAudit] = useState(false);

  // Load blocks when upload is selected
  useEffect(() => {
    if (selectedUpload) {
      loadBlocks();
    }
  }, [selectedUpload]);

  // Load block data when block is selected
  useEffect(() => {
    if (selectedUpload && selectedBlock) {
      loadBlockData();
    }
  }, [selectedUpload, selectedBlock]);

  const loadBlocks = async () => {
    if (!selectedUpload) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiService.getUploadBlocks(selectedUpload);
      setBlocks(response.blocks || []);
    } catch (err: any) {
      setError(`Failed to load blocks: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const loadBlockData = async () => {
    if (!selectedUpload || !selectedBlock) return;
    
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiService.getBlockData(selectedUpload, selectedBlock);
      setBlockData(data);
      setHasChanges(false);
    } catch (err: any) {
      setError(`Failed to load block data: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDataChange = (newData: Record<string, any>[]) => {
    if (blockData) {
      setBlockData({
        ...blockData,
        data: newData
      });
      setHasChanges(true);
    }
  };

  const handleSaveChanges = async () => {
    if (!blockData || !hasChanges) return;
    
    setIsLoading(true);
    setError(null);
    try {
      await apiService.updateBlockData(selectedUpload, selectedBlock, blockData.data);
      setHasChanges(false);
      setIsEditMode(false);
      // Reload block data to confirm changes
      await loadBlockData();
    } catch (err: any) {
      setError(`Failed to save changes: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditMode(false);
    setHasChanges(false);
    // Reload original data
    loadBlockData();
  };

  const handleTestTampering = async () => {
    if (!selectedUpload) return;
    
    setIsStartingAudit(true);
    setError(null);
    try {
      // Start a new audit to test tampering detection
      const auditRequest = {
        upload_id: selectedUpload,
        confidence_level: 95,
        min_corruption_rate: 5
      };
      
      const response = await apiService.startAudit(auditRequest);
      
      // Add the new audit to the context
      const newAudit = {
        auditId: response.audit_data.audit_id,
        uploadId: response.audit_data.upload_id,
        selectedBlocks: response.audit_data.selected_blocks_display || response.audit_data.selected_blocks || [],
        sampleSize: response.audit_data.sample_size,
        samplePercentage: response.audit_data.sample_percentage,
        confidence: `${response.audit_data.confidence_level}%`,
        status: 'running' as const,
        startTime: response.audit_data.start_time
      };
      
      actions.addAudit(newAudit);
      actions.setCurrentAudit(newAudit);
      
      // Redirect to audit page instead of polling here
      navigate('/audit');
      
    } catch (err: any) {
      setError(`Failed to start tampering test: ${err.message}`);
      setIsStartingAudit(false);
    }
  };


  return (
    <div className="max-w-7xl mx-auto">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Data Tampering Tool</h1>
          <p className="text-gray-600">
            Edit data blocks directly to test zero-knowledge proof tampering detection on the same uploaded dataset.
          </p>
        </div>

        {/* Upload Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Upload
          </label>
          <select
            value={selectedUpload}
            onChange={(e) => {
              setSelectedUpload(e.target.value);
              setSelectedBlock('');
              setBlockData(null);
              setIsEditMode(false);
              setHasChanges(false);
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select an upload...</option>
            {state.uploads.map((upload) => (
              <option key={upload.uploadId} value={upload.uploadId}>
                {upload.fileName} ({upload.totalBlocks} blocks, {upload.sizeMB}MB)
              </option>
            ))}
          </select>
        </div>

        {/* Instructions */}
        {selectedUpload && (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">🧪 How Tampering Detection Works</h3>
            <div className="text-sm text-blue-800 space-y-1">
              <p><strong>1.</strong> Select a data block below and edit its contents</p>
              <p><strong>2.</strong> Save your changes to tamper with the stored data</p>
              <p><strong>3.</strong> Run "Test Tampering Detection" to see if the system catches your modifications</p>
              <p><strong>💡</strong> The audit compares current blocks against the original Merkle commitment</p>
            </div>
          </div>
        )}

        {/* Block Selection */}
        {selectedUpload && (
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Block to Edit
            </label>
            <select
              value={selectedBlock}
              onChange={(e) => {
                setSelectedBlock(e.target.value);
                setIsEditMode(false);
                setHasChanges(false);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            >
              <option value="">Select a block...</option>
              {blocks.map((block) => (
                <option key={block.block_id} value={block.block_id}>
                  {block.block_id} ({(block.size_bytes / 1024).toFixed(1)} KB)
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Loading...</span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  {error}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Data Display/Edit Section */}
        {blockData && !isLoading && (
          <div className="space-y-4">
            {/* Block Info */}
            <div className="bg-gray-50 rounded-md p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Block Information</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Block ID:</span>
                  <span className="ml-2 font-medium">{blockData.block_id}</span>
                </div>
                <div>
                  <span className="text-gray-500">Rows:</span>
                  <span className="ml-2 font-medium">{blockData.row_count}</span>
                </div>
                <div>
                  <span className="text-gray-500">Columns:</span>
                  <span className="ml-2 font-medium">{blockData.columns.length}</span>
                </div>
                <div>
                  <span className="text-gray-500">Mode:</span>
                  <span className="ml-2 font-medium">{isEditMode ? 'Edit' : 'View'}</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between items-center">
              <div className="flex space-x-3">
                {!isEditMode ? (
                  <>
                    <button
                      onClick={() => setIsEditMode(true)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      Edit Data
                    </button>
                    <button
                      onClick={handleTestTampering}
                      disabled={isStartingAudit}
                      className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isStartingAudit ? 'Starting Audit...' : 'Test Tampering Detection'}
                    </button>
                  </>
                ) : (
                  <div className="flex space-x-3">
                    <button
                      onClick={handleSaveChanges}
                      disabled={!hasChanges || isLoading}
                      className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Save Changes
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500"
                    >
                      Cancel
                    </button>
                  </div>
                )}
              </div>
              
              <div className="flex items-center space-x-4">
                {hasChanges && (
                  <div className="text-sm text-amber-600 font-medium">
                    ⚠️ Unsaved changes
                  </div>
                )}
                {!isEditMode && selectedUpload && (
                  <div className="text-sm text-gray-600">
                    💡 Make changes, save them, then test tampering detection
                  </div>
                )}
              </div>
            </div>

            {/* Data Display/Editor */}
            {isEditMode ? (
              <DataEditor
                data={blockData.data}
                columns={blockData.columns}
                onChange={handleDataChange}
              />
            ) : (
              <DataViewer
                data={blockData.data}
                columns={blockData.columns}
              />
            )}
          </div>
        )}

        {/* Instructions */}
        {!selectedUpload && (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Get Started</h3>
            <p className="text-gray-600 max-w-md mx-auto">
              Select an upload from the dropdown above to view and edit its data blocks. 
              You can modify individual cells to test how the zero-knowledge proof system detects tampering.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
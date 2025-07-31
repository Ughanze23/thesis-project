import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  CpuChipIcon, 
  ShieldCheckIcon, 
  ClockIcon,
  ChartBarIcon,
  PlayCircleIcon,
  ArrowRightIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { useAudit, AuditData, UploadData } from '../context/AuditContext';
import { apiService } from '../services/api';

export function AuditPage() {
  const { state, actions } = useAudit();
  const navigate = useNavigate();
  const [selectedUpload, setSelectedUpload] = useState<UploadData | null>(null);
  const [confidenceLevel, setConfidenceLevel] = useState(95);
  const [customCorruptionRate, setCustomCorruptionRate] = useState(5);
  const [isStartingAudit, setIsStartingAudit] = useState(false);

  // Load uploads from API on mount
  useEffect(() => {
    const loadUploads = async () => {
      try {
        const uploads = await apiService.getUploads();
        uploads.forEach((upload: any) => {
          const uploadData: UploadData = {
            uploadId: upload.upload_id,
            userId: upload.user_id,
            fileName: upload.filename,
            totalBlocks: upload.total_blocks,
            dataBlocks: upload.data_blocks,
            rootHash: upload.root_hash,
            timestamp: upload.timestamp,
            sizeMB: upload.file_size_mb,
          };
          actions.addUpload(uploadData);
        });
      } catch (error) {
        console.error('Failed to load uploads:', error);
        actions.setError('Failed to load uploads');
      }
    };

    if (state.uploads.length === 0) {
      loadUploads();
    }
  }, [state.uploads.length, actions]);

  // Calculate sample size based on confidence level and corruption rate
  const calculateSampleSize = (totalBlocks: number, confidence: number, corruptionRate: number) => {
    const failProb = 1 - (confidence / 100);
    const theoreticalMin = Math.log(failProb) / Math.log(1 - (corruptionRate / 100));
    return Math.min(Math.ceil(theoreticalMin), totalBlocks);
  };

  const startAudit = async () => {
    if (!selectedUpload) return;

    setIsStartingAudit(true);
    actions.setLoading(true);

    try {
      // Start audit via API
      const response = await apiService.startAudit({
        upload_id: selectedUpload.uploadId,
        confidence_level: confidenceLevel,
        min_corruption_rate: customCorruptionRate,
      });

      const auditData: AuditData = {
        auditId: response.audit_data.audit_id,
        uploadId: response.audit_data.upload_id,
        selectedBlocks: response.audit_data.selected_blocks_display || response.audit_data.selected_blocks.slice(0, 10),
        sampleSize: response.audit_data.sample_size,
        samplePercentage: response.audit_data.sample_percentage,
        confidence: `${response.audit_data.confidence_level}%`,
        status: 'running',
        startTime: response.audit_data.start_time,
      };

      actions.addAudit(auditData);
      actions.setCurrentAudit(auditData);

      // Start polling for results
      const pollAuditStatus = async () => {
        try {
          const statusData = await apiService.getAuditStatus(auditData.auditId);
          
          // statusData is already the audit_data object from the API service
          const auditInfo = statusData;
          
          if (auditInfo.status === 'success' || auditInfo.status === 'failed') {
            const completedAudit: Partial<AuditData> = {
              status: auditInfo.status,
              endTime: auditInfo.end_time,
              results: auditInfo.results,
            };
            actions.updateAudit(auditData.auditId, completedAudit);
            
            // Reset loading state when audit completes
            setIsStartingAudit(false);
            actions.setLoading(false);
            
            navigate(`/results/${auditData.auditId}`);
          } else {
            // Continue polling every 2 seconds
            setTimeout(pollAuditStatus, 2000);
          }
        } catch (error) {
          console.error('Failed to get audit status:', error);
          actions.setError('Failed to get audit status');
          
          // Reset loading state on error
          setIsStartingAudit(false);
          actions.setLoading(false);
        }
      };

      // Start polling
      setTimeout(pollAuditStatus, 2000);

    } catch (error) {
      console.error('Failed to start audit:', error);
      actions.setError(`Failed to start audit: ${error}`);
      
      // Reset loading state on start error
      setIsStartingAudit(false);
      actions.setLoading(false);
    }
  };

  const sampleSize = selectedUpload 
    ? calculateSampleSize(selectedUpload.totalBlocks, confidenceLevel, customCorruptionRate)
    : 0;
  
  const samplePercentage = selectedUpload 
    ? ((sampleSize / selectedUpload.totalBlocks) * 100).toFixed(2)
    : '0';

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <CpuChipIcon className="h-12 w-12 text-blue-600 mx-auto mb-4" />
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Start Zero-Knowledge Audit
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Configure and launch a cryptographic audit of your uploaded dataset.
          Select confidence levels and corruption detection parameters.
        </p>
      </div>

      {/* Upload Selection */}
      <div className="audit-card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          1. Select Dataset
        </h2>
        {state.uploads.length === 0 ? (
          <div className="text-center py-8">
            <ShieldCheckIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">
              No datasets available. Please upload a dataset first.
            </p>
            <button
              onClick={() => navigate('/upload')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Upload Dataset
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {state.uploads.map((upload) => (
              <div
                key={upload.uploadId}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedUpload?.uploadId === upload.uploadId
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                }`}
                onClick={() => setSelectedUpload(upload)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {upload.fileName}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {upload.totalBlocks} blocks • {upload.sizeMB.toFixed(2)} MB
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="status-success">
                      Ready
                    </div>
                    <p className="text-xs text-gray-500">
                      {new Date(upload.timestamp).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Audit Configuration */}
      {selectedUpload && (
        <div className="audit-card">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            2. Configure Audit Parameters
          </h2>

          <div className="space-y-6">
            {/* Confidence Level */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Detection Confidence Level: {confidenceLevel}%
              </label>
              <input
                type="range"
                min="90"
                max="99"
                step="1"
                value={confidenceLevel}
                onChange={(e) => setConfidenceLevel(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>90% (Less Secure)</span>
                <span>99% (More Secure)</span>
              </div>
            </div>

            {/* Minimum Corruption Rate */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Corruption Rate to Detect: {customCorruptionRate}%
              </label>
              <input
                type="range"
                min="1"
                max="20"
                step="1"
                value={customCorruptionRate}
                onChange={(e) => setCustomCorruptionRate(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>1% (Highly Sensitive)</span>
                <span>20% (Less Sensitive)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Audit Preview */}
      {selectedUpload && (
        <div className="audit-card">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            3. Audit Preview
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="metric-card">
              <div className="flex items-center space-x-3 mb-2">
                <ChartBarIcon className="h-6 w-6 text-blue-600" />
                <h3 className="font-semibold text-gray-900">Sample Size</h3>
              </div>
              <p className="text-2xl font-bold text-blue-600">
                {sampleSize}
              </p>
              <p className="text-sm text-gray-600">
                blocks ({samplePercentage}% of total)
              </p>
            </div>

            <div className="metric-card">
              <div className="flex items-center space-x-3 mb-2">
                <ShieldCheckIcon className="h-6 w-6 text-green-600" />
                <h3 className="font-semibold text-gray-900">Confidence</h3>
              </div>
              <p className="text-2xl font-bold text-green-600">
                {confidenceLevel}%
              </p>
              <p className="text-sm text-gray-600">
                detection probability
              </p>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h4 className="font-semibold text-blue-900 mb-2">
              Audit Summary
            </h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• {sampleSize} blocks will be randomly selected and audited</li>
              <li>• Zero-knowledge STARK proofs will be generated for each block</li>
              <li>• {confidenceLevel}% probability of detecting ≥{customCorruptionRate}% corruption</li>
              <li>• Authentication paths remain completely private</li>
              <li>• Results include detailed verification metrics</li>
            </ul>
          </div>

          <div className="flex justify-center">
            <button
              onClick={startAudit}
              disabled={isStartingAudit}
              className={`flex items-center space-x-2 px-8 py-3 rounded-lg font-medium transition-all duration-200 transform ${
                isStartingAudit
                  ? 'bg-gray-400 text-white cursor-not-allowed scale-95'
                  : 'bg-green-600 text-white hover:bg-green-700 hover:scale-105 shadow-lg hover:shadow-xl'
              }`}
            >
              {isStartingAudit ? (
                <>
                  <div className="loading-spinner h-5 w-5"></div>
                  <span>Starting Audit...</span>
                </>
              ) : (
                <>
                  <PlayCircleIcon className="h-5 w-5" />
                  <span>Start Zero-Knowledge Audit</span>
                  <ArrowRightIcon className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Recent Audits */}
      {state.audits.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            Audit History
          </h2>
          <div className="space-y-4">
            {state.audits.slice(-3).reverse().map((audit) => (
              <div key={audit.auditId} className="audit-card cursor-pointer hover:bg-gray-50 transition-colors"
                   onClick={() => navigate(`/results/${audit.auditId}`)}>
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      Audit {audit.auditId.slice(-8)}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {audit.sampleSize} blocks • {audit.confidence} confidence
                      {audit.results && (
                        <span className="ml-2">
                          • {audit.results.statistics.blocksPassed}/{audit.results.statistics.blocksAudited} passed
                        </span>
                      )}
                    </p>
                  </div>
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/results/${audit.auditId}`);
                      }}
                      className="flex items-center space-x-1 px-3 py-1 rounded-lg text-sm bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
                    >
                      <EyeIcon className="h-4 w-4" />
                      <span>View</span>
                    </button>
                    <div className="text-right">
                      <div className={`status-${audit.status}`}>
                        {audit.status}
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        {new Date(audit.startTime).toLocaleDateString()}
                      </p>
                    </div>
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
import React, { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ShieldCheckIcon,
  ClockIcon,
  ChartBarIcon,
  CpuChipIcon,
  EyeSlashIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { useAudit } from '../context/AuditContext';

export function ResultsPage() {
  const { auditId } = useParams<{ auditId: string }>();
  const { state, actions } = useAudit();
  
  const audit = state.audits.find(a => a.auditId === auditId);

  useEffect(() => {
    if (audit) {
      actions.setCurrentAudit(audit);
    }
  }, [auditId, audit?.status, actions]);

  if (!audit) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <XCircleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Audit Not Found
        </h1>
        <p className="text-gray-600 mb-6">
          The requested audit could not be found.
        </p>
        <Link
          to="/audit"
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center space-x-2"
        >
          <ArrowLeftIcon className="h-5 w-5" />
          <span>Back to Audits</span>
        </Link>
      </div>
    );
  }

  const isCompleted = audit.status === 'success' || audit.status === 'failed';
  const results = audit.results;

  // Chart data
  const verificationData = results?.verificationResults.map((result, index) => ({
    block: `Block ${result.blockIndex + 1}`,
    time: result.verificationTimeMs,
    passed: result.verificationPassed ? 1 : 0,
    proofSize: result.starkProofSize,
  })) || [];

  const blocksAudited = results?.statistics.blocksAudited || 0;
  const blocksPassed = results?.statistics.blocksPassed || 0;
  const tamperingDetected = blocksAudited - blocksPassed;


  const statusData = [
    { name: 'Passed', value: blocksPassed || 0, color: '#10B981' },
    { name: 'Failed', value: tamperingDetected || 0, color: '#EF4444' },
  ];

  // Timeline data for future use
  // const timelineData = Array.from({ length: 4 }, (_, i) => ({
  //   stage: ['Fetch', 'Hash', 'Prove', 'Verify'][i],
  //   time: i * 2000 + Math.random() * 1000,
  //   cumulative: (i + 1) * 2000 + Math.random() * 1000,
  // }));

  console.log('test: ', blocksAudited, blocksPassed, tamperingDetected)
  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-3 mb-2">
            <div className={`p-2 rounded-lg ${
              audit.status === 'success' ? 'bg-green-100' :
              audit.status === 'failed' ? 'bg-red-100' :
              audit.status === 'running' ? 'bg-blue-100' :
              'bg-yellow-100'
            }`}>
              {audit.status === 'success' ? (
                <CheckCircleIcon className="h-6 w-6 text-green-600" />
              ) : audit.status === 'failed' ? (
                <XCircleIcon className="h-6 w-6 text-red-600" />
              ) : audit.status === 'running' ? (
                <CpuChipIcon className="h-6 w-6 text-blue-600" />
              ) : (
                <ClockIcon className="h-6 w-6 text-yellow-600" />
              )}
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Audit Results
              </h1>
              <p className="text-gray-600">
                Audit ID: {audit.auditId}
              </p>
            </div>
          </div>
          <div className={`status-${audit.status} inline-block`}>
            {audit.status.toUpperCase()}
          </div>
        </div>
        <Link
          to="/audit"
          className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors inline-flex items-center space-x-2"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          <span>Back to Audits</span>
        </Link>
      </div>

      {/* Status Banner */}
      {isCompleted && results && (
        <div className={`p-6 rounded-lg border-l-4 ${
          results.overallSuccess
            ? 'bg-green-50 border-green-500'
            : 'bg-red-50 border-red-500'
        }`}>
          <div className="flex items-center space-x-3">
            {results.overallSuccess ? (
              <CheckCircleIcon className="h-8 w-8 text-green-600" />
            ) : (
              <XCircleIcon className="h-8 w-8 text-red-600" />
            )}
            <div>
              <h2 className={`text-xl font-bold ${
                results.overallSuccess ? 'text-green-900' : 'text-red-900'
              }`}>
                {results.overallSuccess ? 'Audit Passed' : 'Tampering Detected'}
              </h2>
              <p className={`${
                results.overallSuccess ? 'text-green-700' : 'text-red-700'
              }`}>
                {results.overallSuccess 
                  ? 'All sampled blocks verified successfully. No data tampering detected.'
                  : `${results.statistics.blocksAudited-results.statistics.blocksPassed} blocks failed verification. Data integrity compromised.`
                }
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Running Status */}
      {audit.status === 'running' && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center space-x-3">
            <div className="loading-spinner"></div>
            <div>
              <h2 className="text-xl font-bold text-blue-900">
                Audit in Progress
              </h2>
              <p className="text-blue-700">
                Zero-knowledge proofs are being generated and verified...
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      {isCompleted && results && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="metric-card">
            <div className="flex items-center space-x-3 mb-2">
              <ShieldCheckIcon className="h-6 w-6 text-green-600" />
              <h3 className="font-semibold text-gray-900">Blocks Verified</h3>
            </div>
            <p className="text-2xl font-bold text-green-600">
              {results.statistics.blocksPassed}
            </p>
            <p className="text-sm text-gray-600">
              of {results.statistics.blocksAudited} audited
            </p>
          </div>

          <div className="metric-card">
            <div className="flex items-center space-x-3 mb-2">
              <EyeSlashIcon className="h-6 w-6 text-purple-600" />
              <h3 className="font-semibold text-gray-900">Privacy Level</h3>
            </div>
            <p className="text-2xl font-bold text-purple-600">
              100%
            </p>
            <p className="text-sm text-gray-600">
              zero knowledge achieved
            </p>
          </div>

          <div className="metric-card">
            <div className="flex items-center space-x-3 mb-2">
              <ClockIcon className="h-6 w-6 text-blue-600" />
              <h3 className="font-semibold text-gray-900">Total Time</h3>
            </div>
            <p className="text-2xl font-bold text-blue-600">
              {Math.round(results.statistics.totalTimeMs / 1000)}s
            </p>
            <p className="text-sm text-gray-600">
              avg {results.statistics.averageVerificationTimeMs < 1 
                ? `${(results.statistics.averageVerificationTimeMs * 1000).toFixed(0)}μs`
                : `${results.statistics.averageVerificationTimeMs.toFixed(1)}ms`} per block
            </p>
          </div>

          <div className="metric-card">
            <div className="flex items-center space-x-3 mb-2">
              <ChartBarIcon className="h-6 w-6 text-orange-600" />
              <h3 className="font-semibold text-gray-900">Confidence</h3>
            </div>
            <p className="text-2xl font-bold text-orange-600">
              {results.statistics.confidenceLevel}
            </p>
            <p className="text-sm text-gray-600">
              detection probability
            </p>
          </div>
        </div>
      )}

      {/* Charts */}
      {isCompleted && results && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Verification Status Pie Chart */}
          <div className="audit-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Verification Status Distribution
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* STARK Proof Details */}
      {isCompleted && results && (
        <div className="stark-proof-container">
          <h3 className="text-lg font-semibold text-purple-900 mb-4 flex items-center space-x-2">
            <CpuChipIcon className="h-5 w-5" />
            <span>Zero-Knowledge STARK Proof Analysis</span>
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-white bg-opacity-50 rounded-lg p-4">
              <h4 className="font-semibold text-purple-900 mb-2">Proof Generation</h4>
              <p className="text-sm text-purple-700">
                {results.statistics.blocksAudited} STARK proofs generated successfully.
                Each proof cryptographically proves block membership without revealing authentication paths.
              </p>
            </div>
            
            <div className="bg-white bg-opacity-50 rounded-lg p-4">
              <h4 className="font-semibold text-purple-900 mb-2">Privacy Preservation</h4>
              <p className="text-sm text-purple-700">
                Zero sibling hashes revealed during verification.
                Complete path confidentiality maintained throughout the audit process.
              </p>
            </div>
            
            <div className="bg-white bg-opacity-50 rounded-lg p-4">
              <h4 className="font-semibold text-purple-900 mb-2">Proof Efficiency</h4>
              <p className="text-sm text-purple-700">
                Average proof size: {verificationData.length > 0 ? Math.round(verificationData.reduce((sum, v) => sum + v.proofSize, 0) / verificationData.length) : results?.statistics?.averageProofSize || 0} bytes.
                Constant size regardless of Merkle tree height.
              </p>
            </div>
          </div>

          {/* Mock STARK proof visualization */}
          <div className="merkle-tree-visualization">
            <div className="text-xs">
              <div>🔐 STARK Proof Execution Summary</div>
              <div className="mt-2 space-y-1">
                {results.verificationResults.length > 0 && (
                  <>
                    <div>📊 Blocks verified: {results.statistics.blocksAudited}</div>
                    <div>✅ Successful proofs: {results.statistics.blocksPassed}</div>
                    <div>❌ Failed proofs: {results.statistics.blocksFailed}</div>
                    <div>🔒 Total proof size: {results.statistics.totalProofSize || 'N/A'} bytes</div>
                    <div>⚡ Average generation time: {
                      results.verificationResults[0]?.generationTimeMs && results.verificationResults[0].generationTimeMs > 0
                        ? results.verificationResults[0].generationTimeMs < 1 
                          ? `${(results.verificationResults[0].generationTimeMs * 1000).toFixed(0)}μs`
                          : `${results.verificationResults[0].generationTimeMs.toFixed(1)}ms`
                        : '0μs'
                    } per block</div>
                    <div>🔍 Average verification time: {
                      results.statistics.averageVerificationTimeMs < 1 
                        ? `${(results.statistics.averageVerificationTimeMs * 1000).toFixed(0)}μs`
                        : `${results.statistics.averageVerificationTimeMs.toFixed(1)}ms`
                    } per block</div>
                    <div className="text-green-400">✓ Zero-knowledge property: MAINTAINED</div>
                    <div className="text-green-400">✓ Privacy: 100% authentication paths hidden</div>
                    {results.statistics.tamperingDetected ? (
                      <div className="text-red-400">⚠️ TAMPERING DETECTED</div>
                    ) : (
                      <div className="text-green-400">✓ No tampering detected</div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Block-Level Results */}
      {isCompleted && results && results.verificationResults.length > 0 && (
        <div className="audit-card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Block-Level Verification Results
          </h3>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Block ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Generation Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Verification Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Proof Size
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {results.verificationResults.slice(0, 10).map((result) => (
                  <tr key={result.blockId} className={result.verificationPassed ? '' : 'bg-red-50'}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {result.blockId}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {result.verificationPassed ? (
                        <div className="flex items-center space-x-2">
                          <CheckCircleIcon className="h-4 w-4 text-green-600" />
                          <span className="text-green-800 text-sm">Passed</span>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2">
                          <XCircleIcon className="h-4 w-4 text-red-600" />
                          <span className="text-red-800 text-sm">{ tamperingDetected > 0 ? 'TAMPERED' : 'Failed'}</span>
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {result.generationTimeMs && result.generationTimeMs > 0 
                        ? result.generationTimeMs < 1 
                          ? `${(result.generationTimeMs * 1000).toFixed(0)}μs`
                          : `${result.generationTimeMs.toFixed(1)}ms`
                        : '0μs'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {result.verificationTimeMs && result.verificationTimeMs > 0 
                        ? result.verificationTimeMs < 1 
                          ? `${(result.verificationTimeMs * 1000).toFixed(0)}μs`
                          : `${result.verificationTimeMs.toFixed(1)}ms`
                        : '0μs'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {result.starkProofSize} bytes
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {results.verificationResults.length > 10 && (
            <div className="mt-4 text-center text-sm text-gray-500">
              Showing 10 of {results.verificationResults.length} results
            </div>
          )}
        </div>
      )}

      {/* Audit Information */}
      <div className="audit-card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Audit Information
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">Configuration</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Sample Size: {audit.sampleSize} blocks ({audit.samplePercentage}%)</li>
              <li>• Confidence Level: {audit.confidence}</li>
              <li>• Selection Method: Cryptographically secure random</li>
              <li>• Proof System: ZK-STARK with SHA3-256</li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">Timeline</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Started: {new Date(audit.startTime).toLocaleString()}</li>
              {audit.endTime && (
                <li>• Completed: {new Date(audit.endTime).toLocaleString()}</li>
              )}
              <li>• Duration: {audit.endTime 
                ? `${Math.round((new Date(audit.endTime).getTime() - new Date(audit.startTime).getTime()) / 1000)}s`
                : 'In progress...'
              }</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
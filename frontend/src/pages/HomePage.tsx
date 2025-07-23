import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldCheckIcon, 
  EyeSlashIcon, 
  ClockIcon, 
  ChartBarIcon,
  DocumentArrowUpIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline';
import { useAudit } from '../context/AuditContext';

export function HomePage() {
  const { state } = useAudit();

  const features = [
    {
      icon: ShieldCheckIcon,
      title: 'Zero-Knowledge Proofs',
      description: 'Verify data integrity without revealing sensitive information using STARK proofs.',
      color: 'from-blue-500 to-blue-600'
    },
    {
      icon: EyeSlashIcon,
      title: 'Privacy Preserving',
      description: 'Authentication paths remain hidden while still proving block membership.',
      color: 'from-purple-500 to-purple-600'
    },
    {
      icon: ClockIcon,
      title: 'Efficient Auditing',
      description: 'Sample only a fraction of blocks while maintaining 95% confidence detection.',
      color: 'from-green-500 to-green-600'
    },
    {
      icon: ChartBarIcon,
      title: 'Statistical Guarantees',
      description: 'Cryptographically secure random sampling with provable confidence levels.',
      color: 'from-orange-500 to-orange-600'
    }
  ];

  const stats = [
    {
      label: 'Total Uploads',
      value: state.uploads.length,
      icon: DocumentArrowUpIcon,
    },
    {
      label: 'Audits Completed',
      value: state.audits.filter(audit => audit.status === 'success').length,
      icon: ShieldCheckIcon,
    },
    {
      label: 'Active Audits',
      value: state.audits.filter(audit => audit.status === 'running').length,
      icon: CpuChipIcon,
    },
    {
      label: 'Success Rate',
      value: state.audits.length > 0 
        ? `${Math.round((state.audits.filter(audit => audit.status === 'success').length / state.audits.length) * 100)}%`
        : '0%',
      icon: ChartBarIcon,
    }
  ];

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center py-12 bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl">
        <div className="max-w-3xl mx-auto px-6">
          <div className="flex justify-center mb-6">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-4 rounded-2xl">
              <ShieldCheckIcon className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Zero-Knowledge Data Integrity Audit System
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Verify blockchain data integrity with cryptographic proofs that preserve privacy.
            Detect tampering with 95% confidence while revealing zero sensitive information.
          </p>
          <div className="flex justify-center space-x-4">
            <Link
              to="/upload"
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Upload Data
            </Link>
            <Link
              to="/audit"
              className="bg-white text-blue-600 px-6 py-3 rounded-lg font-medium border-2 border-blue-600 hover:bg-blue-50 transition-colors"
            >
              Start Audit
            </Link>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="audit-card text-center">
            <div className="flex justify-center mb-4">
              <div className="bg-blue-100 p-3 rounded-lg">
                <stat.icon className="h-8 w-8 text-blue-600" />
              </div>
            </div>
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {stat.value}
            </div>
            <div className="text-sm text-gray-600">
              {stat.label}
            </div>
          </div>
        ))}
      </div>

      {/* Features */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          How It Works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((feature, index) => (
            <div key={index} className="audit-card group">
              <div className="flex items-start space-x-4">
                <div className={`bg-gradient-to-r ${feature.color} p-3 rounded-lg group-hover:scale-110 transition-transform`}>
                  <feature.icon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600">
                    {feature.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      {state.audits.length > 0 && (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              Recent Audits
            </h2>
            <Link 
              to="/audit" 
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              View All →
            </Link>
          </div>
          <div className="space-y-4">
            {state.audits.slice(0, 3).map((audit) => (
              <div key={audit.auditId} className="audit-card">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      Audit {audit.auditId.slice(0, 8)}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {audit.sampleSize} blocks sampled • {audit.confidence} confidence
                    </p>
                  </div>
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
            ))}
          </div>
        </div>
      )}

      {/* Getting Started */}
      {state.uploads.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-xl">
          <DocumentArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Get Started
          </h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Upload your first dataset to begin using the ZK audit system.
            Your data will be split into blocks and prepared for secure verification.
          </p>
          <Link
            to="/upload"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors inline-flex items-center space-x-2"
          >
            <DocumentArrowUpIcon className="h-5 w-5" />
            <span>Upload Dataset</span>
          </Link>
        </div>
      )}
    </div>
  );
}
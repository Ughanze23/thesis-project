// API service for connecting frontend to local or cloud backend
import axios from 'axios';

// Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// API types
export interface UploadResponse {
  success: boolean;
  upload_id: string;
  upload_data: {
    upload_id: string;
    user_id: string;
    filename: string;
    file_size_mb: number;
    total_blocks: number;
    data_blocks: number;
    root_hash: string;
    timestamp: string;
    status: string;
  };
  error?: string;
}

export interface AuditStartRequest {
  upload_id: string;
  confidence_level: number;
  min_corruption_rate: number;
}

export interface AuditStartResponse {
  success: boolean;
  audit_id: string;
  audit_data: {
    audit_id: string;
    upload_id: string;
    user_id: string;
    selected_blocks: number[];
    selected_blocks_display?: number[];
    sample_size: number;
    sample_percentage: string;
    confidence_level: number;
    min_corruption_rate: number;
    status: string;
    start_time: string;
  };
  error?: string;
}

// API functions
export const apiService = {
  // Health check
  async healthCheck() {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  },

  // Upload dataset
  async uploadDataset(file: File): Promise<UploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response.data;
    } catch (error: any) {
      console.error('Upload failed:', error);
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error);
      }
      throw new Error('Upload failed. Please try again.');
    }
  },

  // Get all uploads
  async getUploads() {
    try {
      const response = await api.get('/uploads');
      return response.data.uploads;
    } catch (error) {
      console.error('Failed to get uploads:', error);
      throw error;
    }
  },

  // Start audit
  async startAudit(request: AuditStartRequest): Promise<AuditStartResponse> {
    try {
      const response = await api.post('/audit/start', request);
      return response.data;
    } catch (error: any) {
      console.error('Failed to start audit:', error);
      if (error.response?.data?.error) {
        throw new Error(error.response.data.error);
      }
      throw new Error('Failed to start audit. Please try again.');
    }
  },

  // Get audit status
  async getAuditStatus(auditId: string) {
    try {
      const response = await api.get(`/audit/${auditId}/status`);
      return response.data.audit_data;
    } catch (error) {
      console.error('Failed to get audit status:', error);
      throw error;
    }
  },

  // Get all audits
  async getAudits() {
    try {
      const response = await api.get('/audits');
      return response.data.audits;
    } catch (error) {
      console.error('Failed to get audits:', error);
      throw error;
    }
  },
};

export default apiService;
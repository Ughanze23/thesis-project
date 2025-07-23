import React, { createContext, useContext, useReducer, ReactNode, useMemo } from 'react';

// Types
export interface AuditState {
  uploads: UploadData[];
  audits: AuditData[];
  currentAudit: AuditData | null;
  isLoading: boolean;
  error: string | null;
}

export interface UploadData {
  uploadId: string;
  userId: string;
  fileName: string;
  totalBlocks: number;
  dataBlocks: number;
  rootHash: string;
  timestamp: string;
  sizeMB: number;
}

export interface AuditData {
  auditId: string;
  uploadId: string;
  selectedBlocks: number[];
  sampleSize: number;
  samplePercentage: string;
  confidence: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  results?: AuditResults;
  startTime: string;
  endTime?: string;
  error?: string;
}

export interface AuditResults {
  overallSuccess: boolean;
  tamperingDetected: boolean;
  verificationResults: BlockVerificationResult[];
  statistics: AuditStatistics;
}

export interface BlockVerificationResult {
  blockId: string;
  blockIndex: number;
  verificationPassed: boolean;
  verificationTimeMs: number;
  starkProofSize: number;
  errorMessage?: string;
}

export interface AuditStatistics {
  totalBlocks: number;
  blocksAudited: number;
  blocksPassed: number;
  blocksFailed: number;
  totalTimeMs: number;
  averageVerificationTimeMs: number;
  confidenceLevel: string;
  tamperingDetected: boolean;
}

type AuditAction = 
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'ADD_UPLOAD'; payload: UploadData }
  | { type: 'ADD_AUDIT'; payload: AuditData }
  | { type: 'UPDATE_AUDIT'; payload: { auditId: string; updates: Partial<AuditData> } }
  | { type: 'SET_CURRENT_AUDIT'; payload: AuditData | null }
  | { type: 'CLEAR_DATA' };

const initialState: AuditState = {
  uploads: [],
  audits: [],
  currentAudit: null,
  isLoading: false,
  error: null,
};

function auditReducer(state: AuditState, action: AuditAction): AuditState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    
    case 'ADD_UPLOAD':
      return { ...state, uploads: [...state.uploads, action.payload] };
    
    case 'ADD_AUDIT':
      return { ...state, audits: [...state.audits, action.payload] };
    
    case 'UPDATE_AUDIT':
      return {
        ...state,
        audits: state.audits.map(audit =>
          audit.auditId === action.payload.auditId
            ? { ...audit, ...action.payload.updates }
            : audit
        ),
        currentAudit: state.currentAudit?.auditId === action.payload.auditId
          ? { ...state.currentAudit, ...action.payload.updates }
          : state.currentAudit
      };
    
    case 'SET_CURRENT_AUDIT':
      return { ...state, currentAudit: action.payload };
    
    case 'CLEAR_DATA':
      return initialState;
    
    default:
      return state;
  }
}

const AuditContext = createContext<{
  state: AuditState;
  dispatch: React.Dispatch<AuditAction>;
  actions: {
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    addUpload: (upload: UploadData) => void;
    addAudit: (audit: AuditData) => void;
    updateAudit: (auditId: string, updates: Partial<AuditData>) => void;
    setCurrentAudit: (audit: AuditData | null) => void;
    clearData: () => void;
  };
} | null>(null);

export function AuditProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(auditReducer, initialState);

  const actions = useMemo(() => ({
    setLoading: (loading: boolean) => dispatch({ type: 'SET_LOADING', payload: loading }),
    setError: (error: string | null) => dispatch({ type: 'SET_ERROR', payload: error }),
    addUpload: (upload: UploadData) => dispatch({ type: 'ADD_UPLOAD', payload: upload }),
    addAudit: (audit: AuditData) => dispatch({ type: 'ADD_AUDIT', payload: audit }),
    updateAudit: (auditId: string, updates: Partial<AuditData>) => 
      dispatch({ type: 'UPDATE_AUDIT', payload: { auditId, updates } }),
    setCurrentAudit: (audit: AuditData | null) => 
      dispatch({ type: 'SET_CURRENT_AUDIT', payload: audit }),
    clearData: () => dispatch({ type: 'CLEAR_DATA' }),
  }), [dispatch]);

  return (
    <AuditContext.Provider value={{ state, dispatch, actions }}>
      {children}
    </AuditContext.Provider>
  );
}

export function useAudit() {
  const context = useContext(AuditContext);
  if (!context) {
    throw new Error('useAudit must be used within an AuditProvider');
  }
  return context;
}
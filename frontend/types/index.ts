// API Types
export interface AnalysisTask {
  id: string;
  user_id?: string;
  product_url: string;
  asin: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface Product {
  id: string;
  asin: string;
  title: string;
  price?: number;
  currency: string;
  rating?: number;
  review_count: number;
  availability?: string;
  seller?: string;
  category?: string;
  features: string[];
  images: string[];
  raw_data: Record<string, any>;
  scraped_at: string;
}

export interface Competitor {
  id: string;
  main_product_asin: string;
  competitor_asin: string;
  title: string;
  price?: number;
  rating?: number;
  review_count?: number;
  brand?: string;
  source_section?: string;
  confidence_score: number;
  discovered_at: string;
}

export interface AnalysisReport {
  id: string;
  task_id: string;
  asin: string;
  report_type: 'full' | 'market' | 'optimization';
  content: string;
  report_metadata: Record<string, any>;
  created_at: string;
}

// WebSocket Types
export interface WebSocketMessage {
  type: 'progress_update' | 'agent_status' | 'analysis_complete' | 'error';
  task_id: string;
  data: any;
}

export interface ProgressUpdate {
  task_id: string;
  progress: number;
  status: string;
  agent_name?: string;
  message?: string;
}

export interface AgentStatus {
  agent_name: string;
  status: 'running' | 'completed' | 'failed';
  message?: string;
  timestamp: string;
}

// UI Types
export interface AnalysisFormData {
  productUrl: string;
}

export interface AnalysisState {
  task?: AnalysisTask;
  isLoading: boolean;
  progress: number;
  currentAgent?: string;
  error?: string;
  report?: AnalysisReport;
  product?: Product;
  competitors?: Competitor[];
}
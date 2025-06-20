import axios from 'axios';
import { AnalysisTask, AnalysisReport, Product, Competitor } from '@/types';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Service
export class ApiService {
  // Health check
  static async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await apiClient.get('/health');
    return response.data;
  }

  // Analysis endpoints
  static async startAnalysis(productUrl: string): Promise<AnalysisTask> {
    const response = await apiClient.post('/api/v1/product-analysis/analyze', {
      product_url: productUrl,
    });
    return response.data;
  }

  static async getAnalysisStatus(taskId: string): Promise<AnalysisTask> {
    const response = await apiClient.get(`/api/v1/product-analysis/tasks/${taskId}/status`);
    return response.data;
  }

  static async getAnalysisReport(taskId: string): Promise<AnalysisTask> {
    const response = await apiClient.get(`/api/v1/product-analysis/tasks/${taskId}`);
    return response.data;
  }

  static async getProduct(asin: string): Promise<Product> {
    const response = await apiClient.get(`/api/v1/products/${asin}`);
    return response.data;
  }

  static async getCompetitors(asin: string): Promise<Competitor[]> {
    const response = await apiClient.get(`/api/v1/products/${asin}/competitors`);
    return response.data;
  }

  // Database stats
  static async getDatabaseStats(): Promise<{
    tasks: number;
    products: number;
    competitors: number;
    reports: number;
    agent_executions: number;
  }> {
    const response = await apiClient.get('/api/v1/stats/database');
    return response.data;
  }
}

export default ApiService;
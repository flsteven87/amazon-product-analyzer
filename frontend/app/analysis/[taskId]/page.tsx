'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Header } from '@/components/layout/header';
import { Footer } from '@/components/layout/footer';
import { NotionReport } from '@/components/ui/notion-report';
import { ApiService } from '@/services/api';
import { wsService } from '@/services/websocket_native';
import { AnalysisTask, AnalysisReport } from '@/types';

export default function AnalysisPage() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.taskId as string;

  const [task, setTask] = useState<AnalysisTask | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [productTitle, setProductTitle] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [useWebSocket, setUseWebSocket] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  // Fetch task status and report
  const fetchTaskData = async () => {
    try {
      setIsLoading(true);
      const taskData = await ApiService.getAnalysisStatus(taskId);
      setTask(taskData);
      
      // Try to get full task data if completed or if we don't have a product title yet
      if (taskData.status === 'completed' || !productTitle) {
        try {
          const fullTaskData = await ApiService.getAnalysisReport(taskId);
          
          // Extract product title if available
          if (fullTaskData.product && fullTaskData.product.title) {
            setProductTitle(fullTaskData.product.title);
          }
          
          // Extract the first report from the reports array (only if completed)
          if (taskData.status === 'completed' && fullTaskData.reports && fullTaskData.reports.length > 0) {
            setReport(fullTaskData.reports[0]);
          }
        } catch (reportError) {
          // If getting full data fails, continue with basic status only
          console.warn('Failed to fetch full task data:', reportError);
        }
      }
    } catch (err) {
      console.error('Failed to fetch task data:', err);
      setError('Failed to load analysis data');
    } finally {
      setIsLoading(false);
    }
  };

  // Try to establish WebSocket connection first, fallback to polling
  const setupRealtimeUpdates = async () => {
    // Add a small delay to let the page load first
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    try {
      // Try WebSocket connection
      await wsService.connect();
      wsService.subscribeToTask(taskId);
      setWsConnected(true);
      setUseWebSocket(true);
      
      // Set up WebSocket event handlers
      wsService.onProgressUpdate((update) => {
        console.log('WebSocket progress update:', update);
        setTask(prev => prev ? {
          ...prev,
          progress: update.progress,
          status: update.status as 'pending' | 'processing' | 'completed' | 'failed'
        } : null);
      });
      
      wsService.onAnalysisComplete((data) => {
        console.log('WebSocket analysis complete:', data);
        if (data.report) {
          setReport(data.report);
        }
        setTask(prev => prev ? { ...prev, status: 'completed' } : null);
      });
      
      wsService.onError((error) => {
        console.info('WebSocket error, gracefully falling back to polling:', error);
        setUseWebSocket(false);
        setWsConnected(false);
      });
      
      console.log('✅ WebSocket connected successfully');
      
    } catch {
      console.info('ℹ️ WebSocket unavailable, using polling (this is normal)');
      setUseWebSocket(false);
      setWsConnected(false);
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchTaskData();
  }, [taskId]);

  // WebSocket setup
  useEffect(() => {
    setupRealtimeUpdates();
    
    return () => {
      // Clean up WebSocket connection
      if (wsConnected) {
        wsService.unsubscribeFromTask(taskId);
        wsService.disconnect();
      }
    };
  }, [taskId]);

  // Polling setup for when WebSocket is not available
  useEffect(() => {
    const interval = setInterval(() => {
      // Only poll if WebSocket is not working and task is still processing
      if (!useWebSocket && task && (task.status === 'processing' || task.status === 'pending')) {
        fetchTaskData();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [useWebSocket, task?.status]);

  if (isLoading && !task) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading analysis...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!task) {
    return (
      <div className="min-h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto text-center">
            <p className="text-red-600">Analysis not found</p>
            <button
              onClick={() => router.push('/')}
              className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Back to Home
            </button>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {productTitle || 'Product Analysis'}
            </h1>
            <p className="text-gray-600">Task ID: {taskId}</p>
            <p className="text-gray-600">URL: {task.product_url}</p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Status</h2>
              <div className="flex items-center text-sm">
                {wsConnected ? (
                  <span className="flex items-center text-green-600" title="Connected via WebSocket for real-time updates">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                    Real-time
                  </span>
                ) : (
                  <span className="flex items-center text-blue-500" title="Using polling for updates (WebSocket unavailable)">
                    <div className="w-2 h-2 bg-blue-400 rounded-full mr-2"></div>
                    Auto-refresh
                  </span>
                )}
              </div>
            </div>
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Status: {task.status}</span>
                <span>{task.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${task.progress}%` }}
                ></div>
              </div>
            </div>
            <p className="text-sm text-gray-600">
              {task.status === 'completed' ? 'Analysis completed!' : 
               task.status === 'processing' ? 'Analysis in progress...' :
               task.status === 'pending' ? 'Analysis queued...' : 'Analysis status unknown'}
            </p>
          </div>

          {task.status === 'completed' && report && (
            <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
              <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-800">📋 Analysis Report</h2>
                <p className="text-sm text-gray-600 mt-1">Comprehensive product and market analysis</p>
              </div>
              <div className="p-6">
                <NotionReport content={report.content} />
              </div>
            </div>
          )}

          {task.status === 'failed' && (
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-xl font-semibold mb-4 text-red-600">Analysis Failed</h2>
              <p className="text-gray-600">
                {task.error_message || 'An error occurred during analysis. Please try again.'}
              </p>
              <button
                onClick={() => router.push('/')}
                className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Start New Analysis
              </button>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
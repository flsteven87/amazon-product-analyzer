'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import { Header } from '@/components/layout/header';
import { Footer } from '@/components/layout/footer';
import { ApiService } from '@/services/api';
import { AnalysisTask, AnalysisReport } from '@/types';

export default function AnalysisPage() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.taskId as string;

  const [task, setTask] = useState<AnalysisTask | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch task status and report
  const fetchTaskData = async () => {
    try {
      setIsLoading(true);
      const taskData = await ApiService.getAnalysisStatus(taskId);
      setTask(taskData);
      
      if (taskData.status === 'completed') {
        const reportData = await ApiService.getAnalysisReport(taskId);
        setReport(reportData);
      }
    } catch (err) {
      console.error('Failed to fetch task data:', err);
      setError('Failed to load analysis data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTaskData();
    
    // Poll every 3 seconds if task is still processing
    const interval = setInterval(() => {
      if (task && (task.status === 'processing' || task.status === 'pending')) {
        fetchTaskData();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [taskId, task?.status]);

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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Product Analysis</h1>
            <p className="text-gray-600">Task ID: {taskId}</p>
            <p className="text-gray-600">URL: {task.product_url}</p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
            <h2 className="text-xl font-semibold mb-4">Status</h2>
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
            <div className="bg-white p-6 rounded-lg shadow-sm border">
              <h2 className="text-xl font-semibold mb-4">Analysis Report</h2>
              <div className="prose max-w-none">
                <ReactMarkdown>{report.content}</ReactMarkdown>
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
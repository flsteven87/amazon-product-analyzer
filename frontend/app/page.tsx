'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/header';
import { Footer } from '@/components/layout/footer';
import { ApiService } from '@/services/api';

export default function Home() {
  const [productUrl, setProductUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productUrl.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const task = await ApiService.startAnalysis(productUrl);
      router.push(`/analysis/${task.id}`);
    } catch (err: unknown) {
      console.error('Failed to start analysis:', err);
      const errorMessage = err instanceof Error && 'response' in err && err.response
        ? (err.response as { data?: { detail?: string } }).data?.detail || 'Failed to start analysis. Please try again.'
        : 'Failed to start analysis. Please try again.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-6">
            Amazon Product Analyzer
          </h1>
          <p className="text-xl text-gray-600 mb-12">
            Multi-agent AI system for Amazon product analysis by single product URL
          </p>
          
          <div className="bg-white p-8 rounded-lg shadow-sm border">
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}
            
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label 
                  htmlFor="productUrl" 
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Amazon Product URL
                </label>
                <input
                  type="url"
                  id="productUrl"
                  value={productUrl}
                  onChange={(e) => setProductUrl(e.target.value)}
                  placeholder="https://www.amazon.com/dp/XXXXXXXXXX"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
                  required
                  disabled={isLoading}
                />
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Starting Analysis...' : 'Start Analysis'}
              </button>
            </form>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}

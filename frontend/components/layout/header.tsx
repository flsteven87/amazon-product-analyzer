import Link from 'next/link';

export function Header() {
  return (
    <header className="border-b bg-white">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-blue-600">
            Amazon Product Analyzer
          </Link>
          <nav className="flex items-center space-x-4">
            <Link 
              href="/analysis" 
              className="text-gray-600 hover:text-blue-600 transition-colors"
            >
              New Analysis
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { TrendingUp } from 'lucide-react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F5E6D3] via-[#D4C4B0] to-[#5D4037]">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-[#D4C4B0]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link to="/" className="flex items-center space-x-2">
              <TrendingUp className="h-8 w-8 text-[#556B2F]" />
              <span className="text-2xl font-bold text-[#5D4037]">SpendSense</span>
            </Link>
            <nav className="flex space-x-4">
              <Link
                to="/"
                className="text-[#5D4037] hover:text-[#556B2F] px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Dashboard
              </Link>
              <Link
                to="/operator"
                className="text-[#5D4037] hover:text-[#556B2F] px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Operator
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  )
}


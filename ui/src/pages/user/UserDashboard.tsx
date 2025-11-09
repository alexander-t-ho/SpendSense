import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { fetchUserDetail } from '../../services/api'
import AccountCard from '../../components/AccountCard'
import TransactionTable from '../../components/TransactionTable'
import FinancialInsightsCarousel from '../../components/FinancialInsightsCarousel'
import UserBudgetDisplay from '../../components/UserBudgetDisplay'
import RecommendationsSection from '../../components/RecommendationsSection'
import ConsentModal from '../../components/ConsentModal'
import { useState, useEffect } from 'react'
import { FileText, BarChart3, Settings, MessageSquare } from 'lucide-react'
import { getConsentStatus } from '../../services/api'

/**
 * User Dashboard - End-user view
 * User can only see their own account data
 */
export default function UserDashboard() {
  const { userId } = useParams<{ userId: string }>()
  const [windowDays, setWindowDays] = useState<number>(30)
  const [activeTab, setActiveTab] = useState<'overview' | 'insights' | 'recommendations'>('overview')
  const [activeSubTab, setActiveSubTab] = useState<'accounts' | 'transactions'>('accounts')
  const [consentModalOpen, setConsentModalOpen] = useState(false)

  const { data: user, isLoading } = useQuery({
    queryKey: ['user', userId, windowDays],
    queryFn: () => fetchUserDetail(userId!, windowDays),
    enabled: !!userId,
  })

  const { data: consent } = useQuery({
    queryKey: ['consent', userId],
    queryFn: () => getConsentStatus(userId!),
    enabled: !!userId,
  })

  // Auto-open consent modal if user hasn't consented
  useEffect(() => {
    if (consent && !consent.consented && !consentModalOpen) {
      setConsentModalOpen(true)
    }
  }, [consent, consentModalOpen])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[#8B6F47]">Loading your financial data...</div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="text-center py-12">
        <p className="text-[#8B6F47]">Unable to load your account. Please try again later.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Name, Email, and Tabs */}
      <div className="bg-white shadow rounded-lg p-6 border border-[#D4C4B0]">
        <div className="flex items-center justify-between mb-4">
      <div>
            <h1 className="text-3xl font-bold text-[#5D4037]">Welcome back, {user.name}</h1>
            <p className="mt-1 text-[#556B2F]">{user.email}</p>
          </div>
          <button
            onClick={() => setConsentModalOpen(true)}
            className="px-4 py-2 text-sm font-medium text-[#556B2F] hover:text-[#5D4037] hover:bg-[#F5E6D3] rounded-md transition-colors border border-[#D4C4B0]"
          >
            <FileText className="inline-block mr-2 h-4 w-4" />
            Consent
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[#D4C4B0]">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'overview'
                ? 'text-[#556B2F] border-b-2 border-[#556B2F]'
                : 'text-[#556B2F] hover:text-[#5D4037] hover:bg-[#F5E6D3]'
            }`}
          >
            <BarChart3 size={18} />
            Overview
          </button>
          <button
            onClick={() => setActiveTab('insights')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'insights'
                ? 'text-[#556B2F] border-b-2 border-[#556B2F]'
                : 'text-[#556B2F] hover:text-[#5D4037] hover:bg-[#F5E6D3]'
            }`}
          >
            <Settings size={18} />
            Financial Insights
          </button>
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'recommendations'
                ? 'text-[#556B2F] border-b-2 border-[#556B2F]'
                : 'text-[#556B2F] hover:text-[#5D4037] hover:bg-[#F5E6D3]'
            }`}
          >
            <MessageSquare size={18} />
            Recommendations
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' ? (
        <>
          {/* Budget Display */}
          {userId && (
            <UserBudgetDisplay userId={userId} />
          )}

          {/* Sub-tabs for Accounts and Transactions */}
          <div className="bg-white shadow rounded-lg p-4 border border-[#D4C4B0]">
            <div className="flex border-b border-[#D4C4B0] mb-4">
              <button
                onClick={() => setActiveSubTab('accounts')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  activeSubTab === 'accounts'
                    ? 'text-[#556B2F] border-b-2 border-[#556B2F]'
                    : 'text-[#556B2F] hover:text-[#5D4037] hover:bg-[#F5E6D3]'
                }`}
              >
                Accounts
              </button>
              <button
                onClick={() => setActiveSubTab('transactions')}
                className={`px-4 py-2 text-sm font-medium transition-colors ${
                  activeSubTab === 'transactions'
                    ? 'text-[#556B2F] border-b-2 border-[#556B2F]'
                    : 'text-[#556B2F] hover:text-[#5D4037] hover:bg-[#F5E6D3]'
                }`}
              >
                Transactions
              </button>
            </div>

            {activeSubTab === 'accounts' ? (
      <div>
                {/* Time Window Selector */}
                <div className="mb-4">
                  <div className="flex items-center space-x-4">
                    <label htmlFor="window-select" className="text-sm font-medium text-[#556B2F]">
                      Transaction Window:
                    </label>
                    <select
                      id="window-select"
                      value={windowDays}
                      onChange={(e) => setWindowDays(Number(e.target.value))}
                      className="block rounded-md border-[#D4C4B0] shadow-sm focus:border-[#556B2F] focus:ring-blue-500 sm:text-sm"
                    >
                      <option value={30}>30 Days</option>
                      <option value={180}>180 Days</option>
                    </select>
                  </div>
                </div>

                {/* Accounts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {user.accounts?.map((account: any) => (
            <AccountCard key={account.id} account={account} />
          ))}
        </div>
      </div>
            ) : (
      <div>
                {/* Time Window Selector */}
                <div className="mb-4">
            <div className="flex items-center space-x-4">
                    <label htmlFor="window-select" className="text-sm font-medium text-[#556B2F]">
                Transaction Window:
              </label>
              <select
                id="window-select"
                value={windowDays}
                onChange={(e) => setWindowDays(Number(e.target.value))}
                      className="block rounded-md border-[#D4C4B0] shadow-sm focus:border-[#556B2F] focus:ring-blue-500 sm:text-sm"
              >
                <option value={30}>30 Days</option>
                <option value={180}>180 Days</option>
              </select>
          </div>
        </div>

                {/* Transactions Table */}
            {user.transactions && user.transactions.length > 0 ? (
              <TransactionTable transactions={user.transactions} />
            ) : (
                  <div className="text-center py-8 text-[#8B6F47]">
                    <p>No transactions found for the selected window.</p>
              </div>
            )}
          </div>
        )}
      </div>
        </>
      ) : activeTab === 'insights' ? (
        /* Financial Insights Tab */
        userId && (
          <div className="space-y-6">
            <FinancialInsightsCarousel userId={userId} />
          </div>
        )
      ) : (
        /* Recommendations Tab */
        userId && (
          <div className="space-y-6">
            <RecommendationsSection userId={userId} windowDays={windowDays} readOnly={false} />
          </div>
        )
      )}

      {/* Consent Modal */}
      {consentModalOpen && (
        <ConsentModal
          userId={userId!}
          isOpen={consentModalOpen}
          onClose={() => setConsentModalOpen(false)}
        />
      )}
    </div>
  )
}

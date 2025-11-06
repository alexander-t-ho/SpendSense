import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { fetchUserDetail } from '../../services/api'
import AccountCard from '../../components/AccountCard'
import FeatureCard from '../../components/FeatureCard'
import TransactionTable from '../../components/TransactionTable'
import FinancialInsightsCarousel from '../../components/FinancialInsightsCarousel'
import RecommendationsSection from '../../components/RecommendationsSection'
// PersonaPieChart hidden from user view
import { useState } from 'react'

/**
 * User Dashboard - End-user view
 * User can only see their own account data
 * Same interface as admin, but restricted to single user
 */
export default function UserDashboard() {
  // In a real app, this would come from authentication context
  // For now, we'll use a query parameter or route param
  const { userId } = useParams<{ userId: string }>()
  const [windowDays, setWindowDays] = useState<number>(30)
  const [transactionsExpanded, setTransactionsExpanded] = useState<boolean>(true)

  // TODO: Get userId from auth context instead of route param
  // For now, if no userId in route, we'd redirect to login
  // const userId = useAuth().user?.id

  const { data: user, isLoading } = useQuery({
    queryKey: ['user', userId, windowDays],
    queryFn: () => fetchUserDetail(userId!, windowDays),
    enabled: !!userId,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading your financial data...</div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Unable to load your account. Please try again later.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Your Financial Dashboard</h1>
        <p className="mt-2 text-gray-600">Welcome back, {user.name}</p>
      </div>

      {/* Accounts Section - Grid Layout */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Accounts</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {user.accounts?.map((account: any) => (
            <AccountCard key={account.id} account={account} />
          ))}
        </div>
      </div>

      {/* Time Window Selector and Transactions Section */}
      <div>
        <div className="bg-white shadow rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <label htmlFor="window-select" className="text-sm font-medium text-gray-700">
                Transaction Window:
              </label>
              <select
                id="window-select"
                value={windowDays}
                onChange={(e) => setWindowDays(Number(e.target.value))}
                className="block rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                <option value={30}>30 Days</option>
                <option value={180}>180 Days</option>
              </select>
            </div>
            <button
              onClick={() => setTransactionsExpanded(!transactionsExpanded)}
              className="flex items-center space-x-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              <span>Your Transactions (Last {windowDays} Days)</span>
              {transactionsExpanded ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Collapsible Transactions */}
        {transactionsExpanded && (
          <div>
            {user.transactions && user.transactions.length > 0 ? (
              <TransactionTable transactions={user.transactions} />
            ) : (
              <div className="bg-white shadow rounded-lg p-6 text-center text-gray-500">
                <p>No transactions found for the last {windowDays} days.</p>
                <p className="text-sm mt-2">Transaction count: {user.transactions?.length || 0}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Suggested Budget - Right below transactions */}
      {userId && (
        <div className="mt-6">
          <SuggestedBudgetCard userId={userId} lookbackMonths={6} />
        </div>
      )}

      {/* Features Section - HIDDEN */}
      {false && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {user.features_30d && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">30-Day Financial Insights</h2>
              <FeatureCard features={user.features_30d} />
            </div>
          )}

          {user.features_180d && (
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">180-Day Financial Insights</h2>
              <FeatureCard features={user.features_180d} />
            </div>
          )}
        </div>
      )}

      {/* Financial Insights Carousel */}
      {userId && (
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold text-gray-900">Financial Insights</h2>
          <FinancialInsightsCarousel userId={userId} />
        </div>
      )}

      {/* Persona & Risk Analysis - HIDDEN FROM USER VIEW */}
      {false && user.persona && user.persona.all_matching_personas && user.persona.all_matching_personas.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Financial Profile</h2>
          {/* ... persona analysis content hidden ... */}
        </div>
      )}

      {/* Recommendations */}
      {userId && (
        <div className="mt-8">
          <RecommendationsSection userId={userId} windowDays={windowDays} readOnly={false} />
        </div>
      )}
    </div>
  )
}


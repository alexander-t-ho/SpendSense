import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchUserDetail } from '../services/api'
import AccountCard from '../components/AccountCard'
import FeatureCard from '../components/FeatureCard'
import TransactionTable from '../components/TransactionTable'
import RecommendationsSection from '../components/RecommendationsSection'
import WeeklyRecapCard from '../components/WeeklyRecapCard'
import SpendingAnalysisCard from '../components/SpendingAnalysisCard'
import SuggestedBudgetCard from '../components/SuggestedBudgetCard'
import BudgetTrackingCard from '../components/BudgetTrackingCard'
import NetWorthRecapCard from '../components/NetWorthRecapCard'

export default function UserDetail() {
  const { userId } = useParams<{ userId: string }>()
  const [windowDays, setWindowDays] = useState<number>(30)
  const [transactionsExpanded, setTransactionsExpanded] = useState<boolean>(true)

  const { data: user, isLoading } = useQuery({
    queryKey: ['user', userId, windowDays],
    queryFn: () => fetchUserDetail(userId!, windowDays),
    enabled: !!userId,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading user data...</div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">User not found</p>
      </div>
    )
  }

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'MODERATE':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'LOW':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'MINIMAL':
        return 'bg-green-100 text-green-800 border-green-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{user.name}</h1>
            <p className="mt-2 text-gray-600">{user.email}</p>
          </div>
        </div>
        
        {/* Persona & Risk Analysis */}
        {user.persona && (
          <div className="mt-4 bg-white shadow rounded-lg p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Persona & Risk Analysis</h2>
            
            {/* Dual Persona Display with Percentages */}
            {user.persona.top_personas && user.persona.top_personas.length > 0 ? (
              <div className="space-y-4">
                {user.persona.top_personas.map((persona: any, idx: number) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <h3 className="text-base font-semibold text-gray-900">
                          {idx === 0 ? 'Primary' : 'Secondary'} Persona: {persona.persona_name}
                        </h3>
                        <p className="text-sm text-gray-600">
                          {persona.matched_criteria}/{persona.total_criteria} criteria matched
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-blue-600">{persona.percentage}%</div>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getRiskColor(persona.risk_level)}`}>
                          {persona.risk_level}
                        </span>
                      </div>
                    </div>
                    {/* Progress bar */}
                    <div className="w-full bg-gray-200 rounded-full h-2.5 mb-3">
                      <div
                        className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                        style={{ width: `${persona.percentage}%` }}
                      ></div>
                    </div>
                    {/* Matched Criteria Details - Always show if available */}
                    {persona.matched_reasons && persona.matched_reasons.length > 0 ? (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-sm font-medium text-gray-700 mb-2">
                          Matched Criteria ({persona.matched_criteria}/{persona.total_criteria}):
                        </p>
                        <ul className="space-y-1">
                          {persona.matched_reasons.map((reason: string, reasonIdx: number) => (
                            <li key={reasonIdx} className="text-sm text-gray-600 flex items-start">
                              <span className="text-green-500 mr-2 mt-0.5">✓</span>
                              <span>{reason}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : (
                      <div className="mt-3 pt-3 border-t border-gray-200">
                        <p className="text-sm text-gray-500 italic">
                          No matched criteria details available. Matched {persona.matched_criteria}/{persona.total_criteria} criteria.
                        </p>
                      </div>
                    )}
                  </div>
                ))}
                
                {/* Combined Percentage Display */}
                {user.persona.top_personas.length === 2 && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-900">
                      Persona Distribution: {user.persona.top_personas[0].persona_name} ({user.persona.top_personas[0].percentage}%) 
                      & {user.persona.top_personas[1].persona_name} ({user.persona.top_personas[1].percentage}%)
                    </p>
                  </div>
                )}
              </div>
            ) : (
              /* Fallback to legacy format */
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Primary Persona</label>
                  <p className="mt-1 text-base font-semibold text-gray-900">{user.persona.primary_persona_name || user.persona.name || 'Not Assigned'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Risk Level</label>
                  <div className="mt-1">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getRiskColor(user.persona.primary_persona_risk_level || user.persona.risk_level)}`}>
                      {user.persona.primary_persona_risk_level || user.persona.risk_level || 'UNKNOWN'}
                    </span>
                  </div>
                </div>
              </div>
            )}
            
            {/* Rationale */}
            {user.persona.rationale && (
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <label className="text-sm font-medium text-gray-700">Analysis Rationale</label>
                <p className="mt-1 text-sm text-gray-600">{user.persona.rationale}</p>
              </div>
            )}
            
            {/* Generate Recommendations Button */}
            <div className="mt-4">
              <GenerateRecommendationsButton userId={userId!} />
            </div>
          </div>
        )}

        {/* Income Information */}
        {user.income && (
          <div className="mt-4 bg-white shadow rounded-lg p-4">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Income Analysis</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">180-Day Income</label>
                <p className="mt-1 text-2xl font-bold text-gray-900">
                  ${user.income['180_day_total']?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {user.income.payroll_count_180d || 0} payroll transaction{user.income.payroll_count_180d !== 1 ? 's' : ''}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Estimated Yearly Income</label>
                <p className="mt-1 text-2xl font-bold text-green-600">
                  ${user.income.yearly_estimated?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                </p>
                <p className="text-xs text-gray-500 mt-1">Based on 180-day average</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-500">Monthly Average</label>
                <p className="mt-1 text-2xl font-bold text-gray-900">
                  ${((user.income.yearly_estimated || 0) / 12).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
                <p className="text-xs text-gray-500 mt-1">Yearly income ÷ 12</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Accounts Section - Grid Layout */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Accounts</h2>
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
              <span>Transactions (Last {windowDays} Days)</span>
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

      {/* Features Section - Show both windows */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {user.features_30d && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">30-Day Features</h2>
            <FeatureCard features={user.features_30d} />
          </div>
        )}

        {user.features_180d && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">180-Day Features</h2>
            <FeatureCard features={user.features_180d} />
          </div>
        )}
      </div>

      {/* Origin-like Insight Components */}
      <div className="mt-8 space-y-6">
        <h2 className="text-2xl font-semibold text-gray-900">Financial Insights</h2>
        
        {/* Weekly Recap */}
        <WeeklyRecapCard userId={user.id} />

        {/* Spending Analysis */}
        <SpendingAnalysisCard userId={user.id} months={6} />

        {/* Suggested Budget */}
        <SuggestedBudgetCard userId={user.id} lookbackMonths={6} />

        {/* Budget Tracking */}
        <BudgetTrackingCard userId={user.id} />

        {/* Net Worth Recap */}
        <NetWorthRecapCard userId={user.id} period="month" />
      </div>

      {/* Recommendations Section */}
      <div className="mt-8">
        <RecommendationsSection userId={user.id} windowDays={windowDays} readOnly={true} />
      </div>
    </div>
  )
}

function GenerateRecommendationsButton({ userId }: { userId: string }) {
  const queryClient = useQueryClient()
  const [isGenerating, setIsGenerating] = useState(false)

  const generateMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/recommendations/generate/${userId}?num_recommendations=8`, {
        method: 'POST',
      })
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to generate recommendations' }))
        const error = new Error(errorData.detail || 'Failed to generate recommendations')
        ;(error as any).response = response
        throw error
      }
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
      alert('Recommendations generated! Please review and approve them in the Recommendation Queue.')
    },
    onError: async (error) => {
      let errorMessage = 'Failed to generate recommendations'
      try {
        const errorData = await (error as any).response?.json()
        errorMessage = errorData?.detail || errorMessage
      } catch {
        errorMessage = (error as Error).message || errorMessage
      }
      alert(`Error generating recommendations: ${errorMessage}`)
    },
  })

  return (
    <button
      onClick={() => generateMutation.mutate()}
      disabled={generateMutation.isPending}
      className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {generateMutation.isPending ? 'Generating...' : 'Generate Recommendations'}
    </button>
  )
}


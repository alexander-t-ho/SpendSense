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
import PersonaPieChart from '../components/PersonaPieChart'

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
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'LOW':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'MINIMAL':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'VERY_LOW':
        return 'bg-gray-100 text-gray-800 border-gray-300'
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
          <div className="mt-4 bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Persona & Risk Analysis</h2>
            
            {/* Risk Summary */}
            <div className="mb-6 p-5 bg-gray-50 rounded-lg border-2 border-gray-200">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Risk Assessment</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-gray-600">Total Risk Points:</span>
                      <span className="text-2xl font-bold text-gray-900">{user.persona.total_risk_points?.toFixed(2) || '0.00'}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-gray-600">Risk Level:</span>
                      <span className={`inline-flex items-center px-4 py-2 rounded-full text-base font-bold border-2 ${getRiskColor(user.persona.risk_level || 'VERY_LOW')}`}>
                        {user.persona.risk_level || 'VERY_LOW'} RISK
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Pie Chart */}
            {user.persona.all_matching_personas && user.persona.all_matching_personas.length > 0 ? (
              <div className="mb-6 p-4 bg-white border border-gray-200 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Persona Distribution</h3>
                <PersonaPieChart 
                  personas={user.persona.all_matching_personas} 
                  totalRiskPoints={user.persona.total_risk_points || 0}
                />
              </div>
            ) : null}

            {/* Detailed Breakdown Table */}
            {user.persona.all_matching_personas && user.persona.all_matching_personas.length > 0 ? (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Persona Breakdown & Criteria</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Persona
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Matched Criteria
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Points/Criterion
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Total Points
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                          Contribution %
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {user.persona.all_matching_personas.map((persona: any, idx: number) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className="text-sm font-semibold text-gray-900">{persona.persona_name}</div>
                          </td>
                          <td className="px-4 py-4">
                            <div className="text-sm text-gray-900 mb-2">
                              <span className="font-semibold text-base">{persona.matched_criteria}/{persona.total_criteria}</span> criteria matched
                            </div>
                            {persona.matched_reasons && persona.matched_reasons.length > 0 && (
                              <div className="mt-3 p-3 bg-gray-50 rounded-md border border-gray-200">
                                <p className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">Criteria Details:</p>
                                <ul className="space-y-2 text-xs text-gray-700">
                                  {persona.matched_reasons.map((reason: string, reasonIdx: number) => (
                                    <li key={reasonIdx} className="flex items-start">
                                      <span className="text-green-600 mr-2 mt-0.5 flex-shrink-0 font-bold">✓</span>
                                      <span>{reason}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className="text-sm font-semibold text-gray-900">{persona.points_per_criterion}</div>
                            <div className="text-xs text-gray-500">per criterion</div>
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className="text-sm font-bold text-gray-900">{persona.total_points?.toFixed(2) || '0.00'}</div>
                            <div className="text-xs text-gray-500">total points</div>
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className="text-sm font-semibold text-gray-900">{persona.percentage}%</div>
                            <div className="text-xs text-gray-500">of total risk</div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-gray-500 text-center py-8">
                No matching personas found
              </div>
            )}
            
            {/* Rationale */}
            {user.persona.rationale && (
              <div className="mt-6 p-3 bg-gray-50 rounded-lg">
                <label className="text-sm font-medium text-gray-700">Analysis Rationale</label>
                <p className="mt-1 text-sm text-gray-600">{user.persona.rationale}</p>
              </div>
            )}
            
            {/* Generate Recommendations Button */}
            <div className="mt-6">
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

      {/* Features Section - HIDDEN */}
      {false && (
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
      )}

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

      {/* Recommendations Section - HIDDEN */}
      {false && (
        <div className="mt-8">
          <RecommendationsSection userId={user.id} windowDays={windowDays} readOnly={true} />
        </div>
      )}
    </div>
  )
}

function GenerateRecommendationsButton({ userId }: { userId: string }) {
  const queryClient = useQueryClient()
  const [generatedRecommendations, setGeneratedRecommendations] = useState<any[] | null>(null)

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
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
      // Store generated recommendations to display below
      setGeneratedRecommendations(data.recommendations || [])
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
      setGeneratedRecommendations(null)
    },
  })

  const approveMutation = useMutation({
    mutationFn: async (recommendationId: string) => {
      const response = await fetch(`/api/operator/recommendations/${recommendationId}/approve`, {
        method: 'PUT',
      })
      if (!response.ok) {
        throw new Error('Failed to approve recommendation')
      }
      return response.json()
    },
    onSuccess: (_, recommendationId) => {
      // Update the recommendation status in local state
      setGeneratedRecommendations((prev) =>
        prev?.map((rec) =>
          rec.id === recommendationId
            ? { ...rec, approved: true, rejected: false, flagged: false, status: 'approved' }
            : rec
        ) || null
      )
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: async (recommendationId: string) => {
      const response = await fetch(`/api/operator/recommendations/${recommendationId}/reject`, {
        method: 'PUT',
      })
      if (!response.ok) {
        throw new Error('Failed to reject recommendation')
      }
      return response.json()
    },
    onSuccess: (_, recommendationId) => {
      // Update the recommendation status in local state
      setGeneratedRecommendations((prev) =>
        prev?.map((rec) =>
          rec.id === recommendationId
            ? { ...rec, approved: false, rejected: true, flagged: false, status: 'rejected' }
            : rec
        ) || null
      )
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  const flagMutation = useMutation({
    mutationFn: async (recommendationId: string) => {
      const response = await fetch(`/api/operator/recommendations/${recommendationId}/flag`, {
        method: 'PUT',
      })
      if (!response.ok) {
        throw new Error('Failed to flag recommendation')
      }
      return response.json()
    },
    onSuccess: (_, recommendationId) => {
      // Update the recommendation status in local state
      setGeneratedRecommendations((prev) =>
        prev?.map((rec) =>
          rec.id === recommendationId
            ? { ...rec, approved: false, rejected: false, flagged: true, status: 'flagged' }
            : rec
        ) || null
      )
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  return (
    <div>
      <button
        onClick={() => generateMutation.mutate()}
        disabled={generateMutation.isPending}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {generateMutation.isPending ? 'Generating...' : 'Generate Recommendations'}
      </button>

      {/* Display generated recommendations below */}
      {generatedRecommendations && generatedRecommendations.length > 0 && (
        <div className="mt-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Generated Recommendations ({generatedRecommendations.length})
          </h3>
          <div className="space-y-3">
            {generatedRecommendations.map((rec: any, idx: number) => {
              const isApproved = rec.approved || rec.status === 'approved'
              const isRejected = rec.rejected || rec.status === 'rejected'
              const isFlagged = rec.flagged || rec.status === 'flagged'
              const isPending = !isApproved && !isRejected && !isFlagged

              return (
                <div
                  key={rec.id || idx}
                  className={`border rounded-lg p-4 ${
                    isApproved
                      ? 'bg-green-50 border-green-200'
                      : isRejected
                      ? 'bg-red-50 border-red-200'
                      : isFlagged
                      ? 'bg-yellow-50 border-yellow-200'
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="text-md font-semibold text-gray-900">{rec.title}</h4>
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            rec.priority === 'high'
                              ? 'bg-red-100 text-red-800'
                              : rec.priority === 'medium'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {rec.priority || 'medium'}
                        </span>
                        {isApproved && (
                          <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                            ✓ Approved
                          </span>
                        )}
                        {isRejected && (
                          <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                            ✗ Rejected
                          </span>
                        )}
                        {isFlagged && (
                          <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">
                            ⚠ Flagged
                          </span>
                        )}
                        {isPending && (
                          <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                            Pending
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 mb-2">
                        {rec.recommendation_text || rec.description}
                      </p>
                      {rec.action_items && rec.action_items.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs font-medium text-gray-600 mb-1">Action Items:</p>
                          <ul className="list-disc list-inside space-y-1">
                            {rec.action_items.slice(0, 3).map((item: string, itemIdx: number) => (
                              <li key={itemIdx} className="text-xs text-gray-600">
                                {item}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {rec.expected_impact && (
                        <p className="text-xs text-gray-500 mt-2">
                          <span className="font-medium">Expected Impact:</span> {rec.expected_impact}
                        </p>
                      )}
                    </div>
                  </div>
                  {isPending && (
                    <div className="mt-4 flex gap-2 pt-3 border-t border-gray-200">
                      <button
                        onClick={() => approveMutation.mutate(rec.id)}
                        disabled={approveMutation.isPending}
                        className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {approveMutation.isPending ? 'Approving...' : '✓ Approve'}
                      </button>
                      <button
                        onClick={() => rejectMutation.mutate(rec.id)}
                        disabled={rejectMutation.isPending}
                        className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {rejectMutation.isPending ? 'Rejecting...' : '✗ Reject'}
                      </button>
                      <button
                        onClick={() => flagMutation.mutate(rec.id)}
                        disabled={flagMutation.isPending}
                        className="px-3 py-1.5 text-sm bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {flagMutation.isPending ? 'Flagging...' : '⚠ Flag'}
                      </button>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}


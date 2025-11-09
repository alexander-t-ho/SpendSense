import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchUserDetail, getConsentStatus } from '../services/api'
import AccountCard from '../components/AccountCard'
import TransactionTable from '../components/TransactionTable'
import FinancialInsightsCarousel from '../components/FinancialInsightsCarousel'
import PersonaPieChart from '../components/PersonaPieChart'
import CustomRecommendationGenerator from '../components/admin/CustomRecommendationGenerator'
import RecommendationsSection from '../components/RecommendationsSection'
import ConsentInfoModal from '../components/admin/ConsentInfoModal'
import { BarChart3, Settings, CheckCircle, XCircle, MessageSquare, Info } from 'lucide-react'

export default function UserDetail() {
  const { userId } = useParams<{ userId: string }>()
  const [windowDays, setWindowDays] = useState<number>(30)
  const [activeTab, setActiveTab] = useState<'overview' | 'insights' | 'recommendations'>('overview')
  const [activeSubTab, setActiveSubTab] = useState<'accounts' | 'transactions'>('accounts')
  const [showConsentInfoModal, setShowConsentInfoModal] = useState(false)

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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[#8B6F47]">Loading user data...</div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="text-center py-12">
        <p className="text-[#8B6F47]">User not found</p>
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
        return 'bg-[#E8F5E9] text-[#5D4037] border-blue-300'
      case 'MINIMAL':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'VERY_LOW':
        return 'bg-[#F5E6D3] text-[#5D4037] border-[#D4C4B0]'
      default:
        return 'bg-[#F5E6D3] text-[#5D4037] border-[#D4C4B0]'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="bg-white shadow rounded-lg p-6 border border-[#D4C4B0]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-[#5D4037]">{user.name}</h1>
              <p className="mt-2 text-[#556B2F]">{user.email}</p>
            </div>
            {/* Consent Status Badge */}
            <div className="flex items-center gap-2">
              {consent?.consented ? (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-green-100 text-green-800 rounded-full border border-green-300">
                  <CheckCircle size={16} />
                  <span className="text-sm font-medium">Consented</span>
                </div>
              ) : (
                <button
                  onClick={() => setShowConsentInfoModal(true)}
                  className="flex items-center gap-2 px-3 py-1.5 bg-red-100 text-red-800 rounded-full border border-red-300 hover:bg-red-200 transition-colors cursor-pointer group"
                  title="Click to see what data is visible"
                >
                  <XCircle size={16} />
                  <span className="text-sm font-medium">Not Consented</span>
                  <Info size={14} className="opacity-60 group-hover:opacity-100 transition-opacity" />
                </button>
              )}
            </div>
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
            {/* Persona & Risk Analysis */}
            {user.persona && (
              <div className="mt-4 bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-[#5D4037] mb-4">Persona & Risk Analysis</h2>
            
            {/* Risk Summary */}
            <div className="mb-6 p-5 bg-[#E8F5E9] rounded-lg border-2 border-[#D4C4B0]">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-[#5D4037] mb-2">Risk Assessment</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-[#556B2F]">Total Risk Points:</span>
                      <span className="text-2xl font-bold text-[#5D4037]">{user.persona.total_risk_points?.toFixed(2) || '0.00'}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-[#556B2F]">Risk Level:</span>
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
              <div className="mb-6 p-4 bg-white border border-[#D4C4B0] rounded-lg">
                <h3 className="text-lg font-semibold text-[#5D4037] mb-4">Persona Distribution</h3>
                <PersonaPieChart 
                  personas={user.persona.all_matching_personas}
                />
              </div>
            ) : null}

            {/* Detailed Breakdown Table */}
            {user.persona.all_matching_personas && user.persona.all_matching_personas.length > 0 ? (
              <div>
                <h3 className="text-lg font-semibold text-[#5D4037] mb-4">Persona Breakdown & Criteria</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 border border-[#D4C4B0] rounded-lg">
                    <thead className="bg-[#F5E6D3]">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-[#556B2F] uppercase tracking-wider">
                          Persona
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-[#556B2F] uppercase tracking-wider">
                          Matched Criteria
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-[#556B2F] uppercase tracking-wider">
                          Points/Criterion
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-[#556B2F] uppercase tracking-wider">
                          Total Points
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-[#556B2F] uppercase tracking-wider">
                          Contribution %
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {user.persona.all_matching_personas.map((persona: any, idx: number) => (
                        <tr key={idx} className="hover:bg-[#E8F5E9]">
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className="text-sm font-semibold text-[#5D4037]">{persona.persona_name}</div>
                          </td>
                          <td className="px-4 py-4">
                            <div className="text-sm text-[#5D4037] mb-2">
                              <span className="font-semibold text-base">{persona.matched_criteria}/{persona.total_criteria}</span> criteria matched
                            </div>
                            {persona.matched_reasons && persona.matched_reasons.length > 0 && (
                              <div className="mt-3 p-3 bg-[#E8F5E9] rounded-md border border-[#D4C4B0]">
                                <p className="text-xs font-semibold text-[#556B2F] mb-2 uppercase tracking-wide">Criteria Details:</p>
                                <ul className="space-y-2 text-xs text-[#556B2F]">
                                  {persona.matched_reasons.map((reason: string, reasonIdx: number) => (
                                    <li key={reasonIdx} className="flex items-start group">
                                      <span className="text-green-600 mr-2 mt-0.5 flex-shrink-0 font-bold">✓</span>
                                      <span className="flex-1">{reason}</span>
                                      <button
                                        onClick={() => {
                                          // Open custom recommendation generator with this context
                                          const generatorElement = document.getElementById('custom-rec-generator')
                                          if (generatorElement) {
                                            generatorElement.scrollIntoView({ behavior: 'smooth' })
                                            // Trigger click to open if it's a button
                                            const button = generatorElement.querySelector('button')
                                            if (button) button.click()
                                          }
                                        }}
                                        className="ml-2 px-2 py-0.5 text-xs bg-[#556B2F] text-white rounded hover:bg-[#6B7A3C] opacity-0 group-hover:opacity-100 transition-opacity"
                                        title="Create recommendation based on this criteria"
                                      >
                                        Create Rec
                                      </button>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className="text-sm font-semibold text-[#5D4037]">{persona.points_per_criterion}</div>
                            <div className="text-xs text-[#8B6F47]">per criterion</div>
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className="text-sm font-bold text-[#5D4037]">{persona.total_points?.toFixed(2) || '0.00'}</div>
                            <div className="text-xs text-[#8B6F47]">total points</div>
                          </td>
                          <td className="px-4 py-4 whitespace-nowrap">
                            <div className="text-sm font-semibold text-[#5D4037]">{persona.percentage}%</div>
                            <div className="text-xs text-[#8B6F47]">of total risk</div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-[#8B6F47] text-center py-8">
                No matching personas found
              </div>
            )}
            
            {/* Rationale */}
            {user.persona.rationale && (
              <div className="mt-6 p-3 bg-[#E8F5E9] rounded-lg">
                <label className="text-sm font-medium text-[#556B2F]">Analysis Rationale</label>
                <p className="mt-1 text-sm text-[#556B2F]">{user.persona.rationale}</p>
              </div>
            )}
            
            {/* Generate Recommendations Button - Only show if consented */}
            {consent?.consented && (
              <div className="mt-6 space-y-4">
                <GenerateRecommendationsButton userId={userId!} />
              </div>
            )}
            
            {/* Custom Recommendation Generator - Always visible for admins */}
            <div className="mt-6 space-y-4">
              <div id="custom-rec-generator">
                <CustomRecommendationGenerator 
                  userId={userId!}
                  contextData={user.persona?.all_matching_personas?.[0]?.matched_reasons?.[0] || undefined}
                  onRecommendationGenerated={(rec) => {
                    // Could add logic to auto-approve or show in a review queue
                    console.log('Generated recommendation:', rec)
                  }}
                />
              </div>
            </div>
          </div>
        )}

            {/* Income Information - Only show if consented */}
            {consent?.consented && user.income && (
              <div className="mt-4 bg-white shadow rounded-lg p-4">
                <h2 className="text-lg font-semibold text-[#5D4037] mb-3">Income Analysis</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm font-medium text-[#8B6F47]">180-Day Income</label>
                    <p className="mt-1 text-2xl font-bold text-[#5D4037]">
                      ${user.income['180_day_total']?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                    </p>
                    <p className="text-xs text-[#8B6F47] mt-1">
                      {user.income.payroll_count_180d || 0} payroll transaction{user.income.payroll_count_180d !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-[#8B6F47]">Estimated Yearly Income</label>
                    <p className="mt-1 text-2xl font-bold text-green-600">
                      ${user.income.yearly_estimated?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                    </p>
                    <p className="text-xs text-[#8B6F47] mt-1">Based on 180-day average</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-[#8B6F47]">Monthly Average</label>
                    <p className="mt-1 text-2xl font-bold text-[#5D4037]">
                      ${((user.income.yearly_estimated || 0) / 12).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                    <p className="text-xs text-[#8B6F47] mt-1">Yearly income ÷ 12</p>
                  </div>
                </div>
              </div>
            )}

            {/* Accounts and Transactions Section with Sub-tabs */}
            <div className="mt-4 bg-white shadow rounded-lg p-4 border border-[#D4C4B0]">
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
          <div className="mt-4">
            <FinancialInsightsCarousel userId={user.id} isAdmin={true} />
          </div>
        ) : (
          /* Recommendations Tab */
          <div className="mt-4">
            <RecommendationsSection userId={user.id} windowDays={windowDays} readOnly={true} />
          </div>
        )}
      </div>
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
        className="w-full px-4 py-2 bg-[#8B6F47] text-white rounded-md hover:bg-[#6B5235] disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {generateMutation.isPending ? 'Generating...' : 'Generate Recommendations'}
      </button>

      {/* Display generated recommendations below - Collapsible */}
      {generatedRecommendations && generatedRecommendations.length > 0 && (
        <CollapsibleRecommendations 
          recommendations={generatedRecommendations}
          approveMutation={approveMutation}
          rejectMutation={rejectMutation}
          flagMutation={flagMutation}
        />
      )}
    </div>
  )
}

function CollapsibleRecommendations({ 
  recommendations, 
  approveMutation, 
  rejectMutation, 
  flagMutation 
}: { 
  recommendations: any[]
  approveMutation: any
  rejectMutation: any
  flagMutation: any
}) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="mt-6 space-y-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full p-4 bg-[#E8F5E9] border border-[#D4C4B0] rounded-lg hover:bg-[#F5E6D3] transition-colors"
      >
        <h3 className="text-lg font-semibold text-[#5D4037]">
          Generated Recommendations ({recommendations.length})
        </h3>
        <svg
          className={`w-5 h-5 text-[#556B2F] transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isExpanded && (
        <div className="space-y-3">
            {recommendations.map((rec: any, idx: number) => {
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
                      : 'bg-[#E8F5E9] border-[#D4C4B0]'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="text-md font-semibold text-[#5D4037]">{rec.title}</h4>
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            rec.priority === 'high'
                              ? 'bg-red-100 text-red-800'
                              : rec.priority === 'medium'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-[#F5E6D3] text-[#5D4037]'
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
                          <span className="px-2 py-1 text-xs bg-[#E8F5E9] text-[#5D4037] rounded">
                            Pending
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-[#556B2F] mb-2">
                        {rec.recommendation_text || rec.description}
                      </p>
                      {rec.action_items && rec.action_items.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs font-medium text-[#556B2F] mb-1">Action Items:</p>
                          <ul className="list-disc list-inside space-y-1">
                            {rec.action_items.slice(0, 3).map((item: string, itemIdx: number) => (
                              <li key={itemIdx} className="text-xs text-[#556B2F]">
                                {item}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {rec.expected_impact && (
                        <p className="text-xs text-[#8B6F47] mt-2">
                          <span className="font-medium">Expected Impact:</span> {rec.expected_impact}
                        </p>
                      )}
                    </div>
                  </div>
                  {isPending && (
                    <div className="mt-4 flex gap-2 pt-3 border-t border-[#D4C4B0]">
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
      )}

      {/* Consent Info Modal */}
      <ConsentInfoModal
        isOpen={showConsentInfoModal}
        onClose={() => setShowConsentInfoModal(false)}
        userName={user?.name}
      />
    </div>
  )
}

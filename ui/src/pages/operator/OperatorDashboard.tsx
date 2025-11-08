import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { Users, DollarSign, CreditCard, TrendingUp, CheckCircle, FileText, BarChart3, Target, Flag, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { fetchUsers, fetchStats } from '../../services/api'
import { useState, useMemo, useEffect } from 'react'
import RecommendationQueue from '../../components/operator/RecommendationQueue'
import SignalReview from '../../components/operator/SignalReview'
import DecisionTraceViewer from '../../components/operator/DecisionTraceViewer'
import EvaluationMetrics from '../../components/EvaluationMetrics'
import UserSearch from '../../components/operator/UserSearch'
import { fetchRecommendationQueue, approveRecommendation, flagRecommendation, rejectRecommendation, OperatorRecommendation } from '../../services/operatorApi'

/**
 * Operator Dashboard - Admin view
 * Operator can see all users and their data
 * Includes recommendation approval queue, signal review, and decision trace viewer
 */
export default function OperatorDashboard() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'overview' | 'recommendations' | 'signals' | 'traces' | 'evaluation'>('overview')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedUserId, setSelectedUserId] = useState<string>('')
  
  // Listen for tab change events from child components
  useEffect(() => {
    const handleTabChange = (e: CustomEvent) => {
      setActiveTab(e.detail as any)
    }
    window.addEventListener('operator-tab-change', handleTabChange as EventListener)
    return () => {
      window.removeEventListener('operator-tab-change', handleTabChange as EventListener)
    }
  }, [])
  
  const { data: users, isLoading: usersLoading, error: usersError } = useQuery({
    queryKey: ['users'],
    queryFn: fetchUsers,
  })

  // Filter users for Overview tab
  const filteredUsers = useMemo(() => {
    if (!users) return []
    if (!searchQuery.trim()) return users
    
    const query = searchQuery.toLowerCase()
    return users.filter(
      (user: any) =>
        user.name.toLowerCase().includes(query) ||
        user.email.toLowerCase().includes(query)
    )
  }, [users, searchQuery])

  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
  })

  if (usersLoading || statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[#8B6F47]">Loading...</div>
      </div>
    )
  }

  if (usersError || statsError) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">
          <p className="font-semibold">Error loading data</p>
          <p className="text-sm mt-2">{usersError?.message || statsError?.message}</p>
          <p className="text-xs mt-2 text-[#8B6F47]">Make sure the backend API is running on http://localhost:8000</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-[#5D4037]">Dashboard</h1>
          <p className="mt-2 text-[#556B2F]">System overview and user management</p>
        </div>
        
        {/* User Search - Visible on all tabs, more prominent */}
        <div className="w-96">
          <UserSearch
            users={users || []}
            selectedUserId={selectedUserId}
            onSelectUser={(userId) => {
              setSelectedUserId(userId)
              // If user is selected, navigate to their detail page
              if (userId) {
                navigate(`/user/${userId}`)
              }
            }}
            placeholder="Search users by name or email..."
          />
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-[#D4C4B0]">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`${
              activeTab === 'overview'
                ? 'border-[#556B2F] text-[#556B2F]'
                : 'border-transparent text-[#8B6F47] hover:text-[#556B2F] hover:border-[#D4C4B0]'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <Users className="h-4 w-4" />
            Overview
          </button>
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`${
              activeTab === 'recommendations'
                ? 'border-[#556B2F] text-[#556B2F]'
                : 'border-transparent text-[#8B6F47] hover:text-[#556B2F] hover:border-[#D4C4B0]'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <CheckCircle className="h-4 w-4" />
            Recommendations
          </button>
          <button
            onClick={() => setActiveTab('signals')}
            className={`${
              activeTab === 'signals'
                ? 'border-[#556B2F] text-[#556B2F]'
                : 'border-transparent text-[#8B6F47] hover:text-[#556B2F] hover:border-[#D4C4B0]'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <BarChart3 className="h-4 w-4" />
            Signals
          </button>
          <button
            onClick={() => setActiveTab('traces')}
            className={`${
              activeTab === 'traces'
                ? 'border-[#556B2F] text-[#556B2F]'
                : 'border-transparent text-[#8B6F47] hover:text-[#556B2F] hover:border-[#D4C4B0]'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <FileText className="h-4 w-4" />
            Decision Traces
          </button>
          <button
            onClick={() => setActiveTab('evaluation')}
            className={`${
              activeTab === 'evaluation'
                ? 'border-[#556B2F] text-[#556B2F]'
                : 'border-transparent text-[#8B6F47] hover:text-[#556B2F] hover:border-[#D4C4B0]'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <Target className="h-4 w-4" />
            Evaluation Metrics
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard
          title="Total Users"
          value={stats?.total_users || 0}
          icon={<Users className="h-6 w-6" />}
          color="blue"
        />
        <StatCard
          title="Total Accounts"
          value={stats?.total_accounts || 0}
          icon={<CreditCard className="h-6 w-6" />}
          color="green"
        />
        <StatCard
          title="Total Transactions"
          value={stats?.total_transactions || 0}
          icon={<DollarSign className="h-6 w-6" />}
          color="purple"
        />
        <StatCard
          title="Total Liabilities"
          value={stats?.total_liabilities || 0}
          icon={<TrendingUp className="h-6 w-6" />}
          color="orange"
        />
      </div>

      {/* Users Table */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-[#D4C4B0]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-[#5D4037]">
                All Users {users && `(${users.length})`}
                {searchQuery && filteredUsers && ` - Showing ${filteredUsers.length} results`}
              </h2>
              <p className="text-sm text-[#556B2F] mt-1">Click on any user to view their details and manage their account</p>
            </div>
            <div className="w-80">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search users by name or email..."
                className="w-full px-4 py-2 border border-[#D4C4B0] rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-[#556B2F]"
              />
            </div>
          </div>
        </div>
        {!users || users.length === 0 ? (
          <div className="px-6 py-12 text-center text-[#8B6F47]">
            <p>No users found. Make sure the backend API is running.</p>
            <p className="text-sm mt-2">Backend should be at: http://localhost:8000</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-[#E8F5E9]">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#8B6F47] uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#8B6F47] uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#8B6F47] uppercase tracking-wider">
                    Risk Level
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#8B6F47] uppercase tracking-wider">
                    Accounts
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#8B6F47] uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#8B6F47] uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredUsers.map((user: any) => {
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
                  
                  const riskLevel = user.persona?.risk_level || 'VERY_LOW'
                  const riskPoints = user.persona?.total_risk_points || 0
                  
                  return (
                    <tr key={user.id} className="hover:bg-[#E8F5E9]">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-[#5D4037]">
                        {user.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[#8B6F47]">
                        {user.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col gap-1">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getRiskColor(riskLevel)}`}>
                            {riskLevel}
                          </span>
                          <span className="text-xs text-[#8B6F47]">
                            {riskPoints.toFixed(2)} pts
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[#8B6F47]">
                        {user.account_count || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[#8B6F47]">
                        {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <Link
                          to={`/user/${user.id}`}
                          className="text-[#556B2F] hover:text-[#5D4037]"
                        >
                          View Details
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pending Recommendations Section */}
      <PendingRecommendationsSection />

        </div>
      )}

      {activeTab === 'recommendations' && (
        <div>
          <RecommendationQueue />
        </div>
      )}

      {activeTab === 'signals' && (
        <div>
          <SignalReview />
        </div>
      )}

      {activeTab === 'traces' && (
        <div>
          <DecisionTraceViewer />
        </div>
      )}

      {activeTab === 'evaluation' && (
        <div>
          <EvaluationMetrics latencySampleSize={5} />
        </div>
      )}
    </div>
  )
}

function PendingRecommendationsSection() {
  const queryClient = useQueryClient()
  const [isExpanded, setIsExpanded] = useState(false)
  const [expandedRecs, setExpandedRecs] = useState<Set<string>>(new Set())

  const { data, isLoading } = useQuery({
    queryKey: ['operator-recommendations', 'pending'],
    queryFn: () => fetchRecommendationQueue('pending', undefined, 10), // Limit to 10 for overview
    enabled: isExpanded, // Only fetch when expanded
  })

  const approveMutation = useMutation({
    mutationFn: approveRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  const flagMutation = useMutation({
    mutationFn: flagRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: rejectRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  const toggleExpand = (recId: string) => {
    setExpandedRecs(prev => {
      const newSet = new Set(prev)
      if (newSet.has(recId)) {
        newSet.delete(recId)
      } else {
        newSet.add(recId)
      }
      return newSet
    })
  }

  const recommendations = data?.recommendations || []
  const pendingCount = recommendations.length

  return (
    <div className="bg-white shadow rounded-lg">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 border-b border-[#D4C4B0] hover:bg-[#E8F5E9] transition-colors"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isExpanded ? (
              <ChevronUp className="h-5 w-5 text-[#556B2F]" />
            ) : (
              <ChevronDown className="h-5 w-5 text-[#556B2F]" />
            )}
            <div className="text-left">
              <h2 className="text-lg font-semibold text-[#5D4037]">
                Pending Recommendations
                {!isExpanded && pendingCount > 0 && (
                  <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                    {pendingCount}
                  </span>
                )}
              </h2>
              <p className="text-sm text-[#556B2F] mt-1">
                {isExpanded 
                  ? "Review and approve recommendations from the main dashboard"
                  : "Click to expand and review pending recommendations"
                }
              </p>
            </div>
          </div>
          {isExpanded && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                const event = new CustomEvent('operator-tab-change', { detail: 'recommendations' })
                window.dispatchEvent(event)
              }}
              className="text-sm text-[#556B2F] hover:text-[#5D4037] underline"
            >
              View All →
            </button>
          )}
        </div>
      </button>
      
      {isExpanded && (
        <>
          {isLoading ? (
            <div className="px-6 py-12 text-center text-[#8B6F47]">
              Loading pending recommendations...
            </div>
          ) : pendingCount === 0 ? (
            <div className="px-6 py-12 text-center text-[#8B6F47]">
              No pending recommendations
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
        {recommendations.map((rec: OperatorRecommendation) => {
          const isExpanded = expandedRecs.has(rec.id)
          return (
            <div key={rec.id} className="px-6 py-4 hover:bg-[#E8F5E9]">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 flex-wrap">
                    <button
                      onClick={() => toggleExpand(rec.id)}
                      className="flex items-center gap-2 text-left hover:text-[#556B2F] transition-colors"
                    >
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4 text-[#556B2F]" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-[#556B2F]" />
                      )}
                      <h3 className="text-base font-medium text-[#5D4037]">{rec.title}</h3>
                    </button>
                    {rec.priority && (
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                        rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-[#F5E6D3] text-[#5D4037]'
                      }`}>
                        {rec.priority.toUpperCase()}
                      </span>
                    )}
                  </div>
                  <div className="mt-2 text-sm text-[#556B2F]">
                    <p>
                      <span className="font-medium">User:</span> {rec.user_name} ({rec.user_email})
                    </p>
                  </div>
                  
                  {isExpanded && (
                    <div className="mt-4 space-y-3">
                      {rec.description && (
                        <div className="p-3 bg-[#E8F5E9] rounded-md">
                          <p className="text-sm font-medium text-[#5D4037] mb-1">Recommendation:</p>
                          <p className="text-sm text-[#556B2F]">{rec.description}</p>
                        </div>
                      )}
                      {rec.action_items && rec.action_items.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-[#5D4037] mb-1">Action Items:</p>
                          <ul className="list-disc list-inside text-sm text-[#556B2F] space-y-1">
                            {rec.action_items.map((item: string, idx: number) => (
                              <li key={idx}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {rec.expected_impact && (
                        <div className="p-2 bg-green-50 rounded-md">
                          <p className="text-xs font-medium text-green-900">Expected Impact:</p>
                          <p className="text-xs text-green-800 mt-1">{rec.expected_impact}</p>
                        </div>
                      )}
                      {rec.rationale && (
                        <div className="p-3 bg-blue-50 rounded-md">
                          <p className="text-sm font-medium text-blue-900">Rationale:</p>
                          <p className="text-sm text-[#5D4037] mt-1">{rec.rationale}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div className="ml-4 flex gap-2 flex-shrink-0">
                  <button
                    onClick={() => approveMutation.mutate(rec.id)}
                    disabled={approveMutation.isPending || flagMutation.isPending || rejectMutation.isPending}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Approve"
                  >
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Approve
                  </button>
                  <button
                    onClick={() => rejectMutation.mutate(rec.id)}
                    disabled={approveMutation.isPending || flagMutation.isPending || rejectMutation.isPending}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-orange-600 hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Reject"
                  >
                    <AlertCircle className="h-3 w-3 mr-1" />
                    Reject
                  </button>
                  <button
                    onClick={() => flagMutation.mutate(rec.id)}
                    disabled={approveMutation.isPending || flagMutation.isPending || rejectMutation.isPending}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md text-white bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Flag"
                  >
                    <Flag className="h-3 w-3 mr-1" />
                    Flag
                  </button>
                </div>
              </div>
            </div>
          )
        })}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function StatCard({ title, value, icon, color }: { title: string; value: number; icon: React.ReactNode; color: 'blue' | 'green' | 'purple' | 'orange' }) {
  const colorClasses: Record<string, string> = {
    blue: 'bg-[#E8F5E9] text-[#556B2F]',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600',
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`${colorClasses[color] || colorClasses.blue} p-3 rounded-lg`}>{icon}</div>
        <div className="ml-4">
          <p className="text-sm font-medium text-[#556B2F]">{title}</p>
          <p className="text-2xl font-semibold text-[#5D4037]">{value.toLocaleString()}</p>
        </div>
      </div>
    </div>
  )
}


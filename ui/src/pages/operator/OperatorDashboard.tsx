import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Users, DollarSign, CreditCard, TrendingUp, CheckCircle, FileText, BarChart3, Target } from 'lucide-react'
import { fetchUsers, fetchStats } from '../../services/api'
import { useState } from 'react'
import RecommendationQueue from '../../components/operator/RecommendationQueue'
import SignalReview from '../../components/operator/SignalReview'
import DecisionTraceViewer from '../../components/operator/DecisionTraceViewer'
import EvaluationMetrics from '../../components/EvaluationMetrics'

/**
 * Operator Dashboard - Admin view
 * Operator can see all users and their data
 * Includes recommendation approval queue, signal review, and decision trace viewer
 */
export default function OperatorDashboard() {
  const [activeTab, setActiveTab] = useState<'overview' | 'recommendations' | 'signals' | 'traces' | 'evaluation'>('overview')
  const { data: users, isLoading: usersLoading, error: usersError } = useQuery({
    queryKey: ['users'],
    queryFn: fetchUsers,
  })

  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
  })

  if (usersLoading || statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    )
  }

  if (usersError || statsError) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">
          <p className="font-semibold">Error loading data</p>
          <p className="text-sm mt-2">{usersError?.message || statsError?.message}</p>
          <p className="text-xs mt-2 text-gray-500">Make sure the backend API is running on http://localhost:8000</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Operator Dashboard</h1>
        <p className="mt-2 text-gray-600">System overview and user management</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <Users className="h-4 w-4" />
            Overview
          </button>
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`${
              activeTab === 'recommendations'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <CheckCircle className="h-4 w-4" />
            Recommendations
          </button>
          <button
            onClick={() => setActiveTab('signals')}
            className={`${
              activeTab === 'signals'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <BarChart3 className="h-4 w-4" />
            Signals
          </button>
          <button
            onClick={() => setActiveTab('traces')}
            className={`${
              activeTab === 'traces'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2`}
          >
            <FileText className="h-4 w-4" />
            Decision Traces
          </button>
          <button
            onClick={() => setActiveTab('evaluation')}
            className={`${
              activeTab === 'evaluation'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
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
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            All Users {users && `(${users.length})`}
          </h2>
          <p className="text-sm text-gray-600 mt-1">Click on any user to view their details and manage their account</p>
        </div>
        {!users || users.length === 0 ? (
          <div className="px-6 py-12 text-center text-gray-500">
            <p>No users found. Make sure the backend API is running.</p>
            <p className="text-sm mt-2">Backend should be at: http://localhost:8000</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Accounts
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user: any) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {user.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.account_count || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <Link
                        to={`/user/${user.id}`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        View Details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

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

function StatCard({ title, value, icon, color }: { title: string; value: number; icon: React.ReactNode; color: 'blue' | 'green' | 'purple' | 'orange' }) {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600',
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`${colorClasses[color] || colorClasses.blue} p-3 rounded-lg`}>{icon}</div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value.toLocaleString()}</p>
        </div>
      </div>
    </div>
  )
}


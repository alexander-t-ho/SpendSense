import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Users, DollarSign, CreditCard, TrendingUp } from 'lucide-react'
import { fetchUsers, fetchStats } from '../../services/api'

/**
 * Operator Dashboard - Admin view
 * Operator can see all users and their data
 * Same interface as user dashboard, but with access to all users
 */
export default function OperatorDashboard() {
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

      {/* TODO: Add operator-specific features */}
      {/* - Signal summary view */}
      {/* - Recommendation approval queue */}
      {/* - Decision trace viewer */}
      {/* - System health metrics */}
    </div>
  )
}

function StatCard({ title, value, icon, color }: any) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600',
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`${colorClasses[color]} p-3 rounded-lg`}>{icon}</div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value.toLocaleString()}</p>
        </div>
      </div>
    </div>
  )
}


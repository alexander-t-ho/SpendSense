import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Users, DollarSign, CreditCard, TrendingUp } from 'lucide-react'
import { fetchUsers, fetchStats } from '../services/api'

export default function Dashboard() {
  const { data: users, isLoading: usersLoading, error: usersError } = useQuery({
    queryKey: ['users'],
    queryFn: () => fetchUsers(0, 50, false), // Fast: no persona computation, paginated
  })

  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
  })

  if (usersLoading || statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[#556B2F]">Loading...</div>
      </div>
    )
  }

  if (usersError || statsError) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-600">
          <p className="font-semibold">Error loading data</p>
          <p className="text-sm mt-2">{usersError?.message || statsError?.message}</p>
          <p className="text-xs mt-2 text-[#556B2F]">Make sure the backend API is running on http://localhost:8001</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-[#5D4037]">Dashboard</h1>
        <p className="mt-2 text-[#556B2F]">Financial insights for all users</p>
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
      <div className="bg-white shadow rounded-lg border border-[#D4C4B0]">
        <div className="px-6 py-4 border-b border-[#D4C4B0]">
          <h2 className="text-lg font-semibold text-[#5D4037]">
            Users {users && `(${users.length})`}
          </h2>
        </div>
        {!users || users.length === 0 ? (
          <div className="px-6 py-12 text-center text-[#556B2F]">
            <p>No users found. Make sure the backend API is running.</p>
            <p className="text-sm mt-2">Backend should be at: http://localhost:8001</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-[#D4C4B0]">
              <thead className="bg-[#E8F5E9]">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#5D4037] uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-amber-900 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-amber-900 uppercase tracking-wider">
                    Persona & Risk
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-amber-900 uppercase tracking-wider">
                    Accounts
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-amber-900 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-amber-900 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-amber-200">
                {users.map((user: any) => {
                  const persona = user.persona || {}
                  
                  // Handle missing persona (when include_persona=false for performance)
                  if (!persona || Object.keys(persona).length === 0) {
                    return (
                      <tr key={user.id} className="hover:bg-[#E8F5E9]">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-[#5D4037]">
                          {user.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[#556B2F]">
                          {user.email}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[#556B2F]">
                          <span className="text-xs text-gray-500">Click to view persona</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[#556B2F]">
                          {user.account_count || 0}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-[#556B2F]">
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
                  }
                  
                  // Check for dual persona format
                  const topPersonas = persona.top_personas || []
                  const primaryPersona = topPersonas[0] || persona
                  const secondaryPersona = topPersonas[1]
                  
                  const primaryName = primaryPersona.persona_name || primaryPersona.name || 'Not Assigned'
                  const primaryRisk = primaryPersona.risk_level || persona.risk_level || 'MINIMAL'
                  const primaryRiskColor = getRiskColor(primaryRisk)
                  
                  return (
                    <tr key={user.id} className="hover:bg-[#E8F5E9]">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-[#5D4037]">
                        {user.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[#556B2F]">
                        {user.email}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex flex-col gap-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-[#5D4037]">
                              {primaryName}
                            </span>
                            {primaryPersona.percentage && (
                              <span className="text-xs font-semibold text-[#556B2F]">
                                {primaryPersona.percentage}%
                              </span>
                            )}
                          </div>
                          {secondaryPersona && (
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-[#556B2F]">
                                {secondaryPersona.persona_name}
                              </span>
                              {secondaryPersona.percentage && (
                                <span className="text-xs font-semibold text-[#556B2F]">
                                  {secondaryPersona.percentage}%
                                </span>
                              )}
                            </div>
                          )}
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${primaryRiskColor}`}>
                            {primaryRisk} Risk
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[#556B2F]">
                        {user.account_count || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[#556B2F]">
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
    </div>
  )
}

function getRiskColor(riskLevel: string): string {
  switch (riskLevel) {
    case 'CRITICAL':
      return 'bg-red-100 text-red-800'
    case 'HIGH':
      return 'bg-orange-100 text-orange-800'
    case 'MEDIUM':
      return 'bg-yellow-100 text-yellow-800'
    case 'LOW':
      return 'bg-[#E8F5E9] text-[#5D4037]'
    case 'MINIMAL':
      return 'bg-green-100 text-green-800'
    default:
      return 'bg-[#F5E6D3] text-[#5D4037]'
  }
}

function StatCard({ title, value, icon, color }: { title: string; value: number; icon: React.ReactNode; color: 'blue' | 'green' | 'purple' | 'orange' }) {
  const colorClasses: Record<string, string> = {
    blue: 'bg-[#E8F5E9] text-[#556B2F]',
    green: 'bg-[#E8F5E9] text-[#556B2F]',
    purple: 'bg-[#E8F5E9] text-[#556B2F]',
    orange: 'bg-[#F5E6D3] text-[#8B6F47]',
  }

  return (
    <div className="bg-white rounded-lg shadow border border-[#D4C4B0] p-6">
      <div className="flex items-center">
        <div className={`${colorClasses[color] || colorClasses.green} p-3 rounded-lg`}>{icon}</div>
        <div className="ml-4">
          <p className="text-sm font-medium text-[#556B2F]">{title}</p>
          <p className="text-2xl font-semibold text-[#5D4037]">{value.toLocaleString()}</p>
        </div>
      </div>
    </div>
  )
}


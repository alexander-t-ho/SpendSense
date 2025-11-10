import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { fetchUsers } from '../../services/api'
import { fetchUserSignals, UserSignals } from '../../services/operatorApi'
import { AlertCircle } from 'lucide-react'

export default function SignalReview() {
  const [selectedUserId, setSelectedUserId] = useState<string>('')
  const [windowDays, setWindowDays] = useState<number>(180)

  const { data: users } = useQuery({
    queryKey: ['users'],
    queryFn: () => fetchUsers(0, 50, false), // Fast: no persona computation, paginated
  })

  const { data: signals, isLoading, error } = useQuery({
    queryKey: ['operator-signals', selectedUserId, windowDays],
    queryFn: () => fetchUserSignals(selectedUserId, windowDays),
    enabled: !!selectedUserId,
  })

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-[#D4C4B0]">
        <h2 className="text-lg font-semibold text-[#5D4037]">Signal Review</h2>
        <p className="text-sm text-[#556B2F] mt-1">View all behavioral signals for a specific user</p>
      </div>

      <div className="px-6 py-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-[#556B2F] mb-2">Select User</label>
            <select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              className="w-full px-3 py-2 border border-[#D4C4B0] rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-[#556B2F]"
            >
              <option value="">-- Select a user --</option>
              {users?.map((user: any) => (
                <option key={user.id} value={user.id}>
                  {user.name} ({user.email})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-[#556B2F] mb-2">Time Window</label>
            <select
              value={windowDays}
              onChange={(e) => setWindowDays(Number(e.target.value))}
              className="w-full px-3 py-2 border border-[#D4C4B0] rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-[#556B2F]"
            >
              <option value={30}>30 days</option>
              <option value={180}>180 days</option>
            </select>
          </div>
        </div>

        {!selectedUserId && (
          <div className="text-center py-12 text-[#8B6F47]">
            <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p>Please select a user to view their behavioral signals</p>
          </div>
        )}

        {selectedUserId && isLoading && (
          <div className="text-center py-12 text-[#8B6F47]">Loading signals...</div>
        )}

        {selectedUserId && error && (
          <div className="text-center py-12 text-red-600">
            Error loading signals: {(error as Error).message}
          </div>
        )}

        {selectedUserId && signals && <SignalsDisplay signals={signals} />}
      </div>
    </div>
  )
}

function SignalsDisplay({ signals }: { signals: UserSignals }) {
  const signalData = signals.signals || {}

  const formatValue = (value: any): string => {
    if (value === null || value === undefined) return 'N/A'
    if (typeof value === 'boolean') return value ? 'Yes' : 'No'
    if (typeof value === 'number') {
      if (value >= 1000) return `$${value.toLocaleString()}`
      if (value < 1 && value > 0) return `${(value * 100).toFixed(1)}%`
      return value.toLocaleString()
    }
    if (Array.isArray(value)) return value.join(', ')
    if (typeof value === 'object') return JSON.stringify(value, null, 2)
    return String(value)
  }

  const getSignalCategory = (key: string): string => {
    if (key.includes('subscription')) return 'Subscriptions'
    if (key.includes('savings')) return 'Savings'
    if (key.includes('credit') || key.includes('utilization')) return 'Credit'
    if (key.includes('income') || key.includes('payroll')) return 'Income'
    return 'Other'
  }

  const categories = {
    Subscriptions: [] as Array<[string, any]>,
    Savings: [] as Array<[string, any]>,
    Credit: [] as Array<[string, any]>,
    Income: [] as Array<[string, any]>,
    Other: [] as Array<[string, any]>,
  }

  Object.entries(signalData).forEach(([key, value]) => {
    const category = getSignalCategory(key)
    categories[category as keyof typeof categories].push([key, value])
  })

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <p className="text-sm font-medium text-blue-900">
          User: {signals.user_id} | Window: {signals.window_days} days | Computed: {new Date(signals.timestamp).toLocaleString()}
        </p>
      </div>

      {Object.entries(categories).map(([categoryName, signals]) => {
        if (signals.length === 0) return null

        return (
          <div key={categoryName} className="border border-[#D4C4B0] rounded-lg">
            <div className="px-4 py-3 bg-[#E8F5E9] border-b border-[#D4C4B0]">
              <h3 className="text-md font-semibold text-[#5D4037]">{categoryName}</h3>
            </div>
            <div className="divide-y divide-gray-200">
              {signals.map(([key, value]) => (
                <div key={key} className="px-4 py-3">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-[#5D4037]">{key.replace(/_/g, ' ')}</p>
                    </div>
                    <div className="ml-4 text-right">
                      <p className="text-sm text-[#556B2F] font-mono">{formatValue(value)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}


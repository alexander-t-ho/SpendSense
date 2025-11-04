import { CreditCard, Home, GraduationCap, Wallet } from 'lucide-react'

interface AccountCardProps {
  account: {
    id: string
    account_id: string
    name: string
    type: string
    subtype: string
    current: number
    available?: number
    limit?: number
    amount_due?: number
    minimum_payment_due?: number
    interest_rate?: number
    next_payment_due_date?: string
  }
}

function maskAccountId(accountId: string): string {
  // Mask all but last 4 digits
  if (!accountId || accountId.length < 4) return accountId
  const last4 = accountId.slice(-4)
  return `********${last4}`
}

export default function AccountCard({ account }: AccountCardProps) {
  const getIcon = () => {
    if (account.type === 'credit') return <CreditCard className="h-5 w-5" />
    if (account.subtype === 'mortgage') return <Home className="h-5 w-5" />
    if (account.subtype === 'student_loan') return <GraduationCap className="h-5 w-5" />
    return <Wallet className="h-5 w-5" />
  }

  const getTypeColor = () => {
    if (account.type === 'credit') {
      // Color based on utilization
      if (account.limit && account.current) {
        const utilization = (Math.abs(account.current) / account.limit) * 100
        if (utilization >= 80) return 'border-red-300 bg-red-50'
        if (utilization >= 50) return 'border-yellow-300 bg-yellow-50'
        if (utilization >= 30) return 'border-green-300 bg-green-50'
      }
      return 'border-gray-200 bg-gray-50'
    }
    if (account.type === 'loan') return 'border-orange-200 bg-orange-50'
    return 'border-blue-200 bg-blue-50'
  }

  const formatCurrency = (amount: number | null | undefined) => {
    if (amount === null || amount === undefined) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(Math.abs(amount))
  }

  return (
    <div className={`border rounded-lg p-4 ${getTypeColor()}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-2">
          <div className="text-gray-600">{getIcon()}</div>
          <div>
            <h3 className="font-semibold text-gray-900">{account.name}</h3>
            <p className="text-sm text-gray-600 capitalize">{account.subtype || account.type}</p>
            <p className="text-xs text-gray-500 font-mono">{maskAccountId(account.account_id)}</p>
          </div>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {account.type === 'credit' && (
          <>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Balance:</span>
              <span className="font-medium">{formatCurrency(account.current)}</span>
            </div>
            {account.limit && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Limit:</span>
                <span className="font-medium">{formatCurrency(account.limit)}</span>
              </div>
            )}
            {account.amount_due !== undefined && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Amount Due:</span>
                <span className="font-medium">{formatCurrency(account.amount_due)}</span>
              </div>
            )}
            {account.minimum_payment_due !== undefined && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Minimum Payment:</span>
                <span className="font-medium">{formatCurrency(account.minimum_payment_due)}</span>
              </div>
            )}
            {account.limit && account.current && (() => {
              const utilization = (Math.abs(account.current) / account.limit) * 100
              let utilizationColor = 'text-gray-900'
              if (utilization >= 80) utilizationColor = 'text-red-600 font-bold'
              else if (utilization >= 50) utilizationColor = 'text-yellow-600 font-semibold'
              else if (utilization >= 30) utilizationColor = 'text-green-600'
              
              return (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Utilization:</span>
                  <span className={`font-medium ${utilizationColor}`}>
                    {utilization.toFixed(1)}%
                  </span>
                </div>
              )
            })()}
          </>
        )}

        {account.type === 'loan' && (
          <>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Balance:</span>
              <span className="font-medium">{formatCurrency(account.current)}</span>
            </div>
            {account.interest_rate && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Interest Rate:</span>
                <span className="font-medium">{account.interest_rate.toFixed(2)}%</span>
              </div>
            )}
            {account.next_payment_due_date && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Next Payment:</span>
                <span className="font-medium">
                  {new Date(account.next_payment_due_date).toLocaleDateString()}
                </span>
              </div>
            )}
          </>
        )}

        {account.type === 'depository' && (
          <>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <div>
                  <span className="text-gray-600 font-medium">Available Balance:</span>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Immediate usable funds for transactions
                  </p>
                </div>
                <span className="font-semibold text-green-600">
                  {formatCurrency(account.available)}
                </span>
              </div>
              <div className="flex justify-between text-sm border-t pt-2">
                <div>
                  <span className="text-gray-600 font-medium">Current Balance:</span>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Total including pending transactions
                  </p>
                </div>
                <span className="font-medium text-gray-900">
                  {formatCurrency(account.current)}
                </span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}


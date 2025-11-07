import { useState } from 'react'
import { CreditCard, Home, GraduationCap, Wallet, ChevronDown, ChevronUp } from 'lucide-react'
import TransactionTable from './TransactionTable'

interface AccountCardWithTransactionsProps {
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
  transactions?: Array<{
    id: string
    account_id?: string
    date: string
    amount: number
    merchant_name?: string | null
    primary_category?: string | null
    detailed_category?: string | null
  }>
}

function maskAccountId(accountId: string): string {
  if (!accountId || accountId.length < 4) return accountId
  const last4 = accountId.slice(-4)
  return `********${last4}`
}

export default function AccountCardWithTransactions({ account, transactions = [] }: AccountCardWithTransactionsProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const getIcon = () => {
    if (account.type === 'credit') return <CreditCard className="h-5 w-5" />
    if (account.subtype === 'mortgage') return <Home className="h-5 w-5" />
    if (account.subtype === 'student_loan') return <GraduationCap className="h-5 w-5" />
    return <Wallet className="h-5 w-5" />
  }

  const getTypeColor = () => {
    if (account.type === 'credit') {
      if (account.limit && account.current) {
        const utilization = (Math.abs(account.current) / account.limit) * 100
        if (utilization >= 80) return 'border-red-300 bg-red-50'
        if (utilization >= 50) return 'border-yellow-300 bg-yellow-50'
        if (utilization >= 30) return 'border-green-300 bg-green-50'
      }
      return 'border-[#D4C4B0] bg-[#E8F5E9]'
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

  const accountTransactions = transactions.filter((tx: any) => tx.account_id === account.id)

  return (
    <div className="space-y-0">
      <div 
        className={`border rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow ${getTypeColor()}`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-2 flex-1">
            <div className="text-[#556B2F]">{getIcon()}</div>
            <div className="flex-1">
              <h3 className="font-semibold text-[#5D4037]">{account.name}</h3>
              <p className="text-sm text-[#556B2F] capitalize">{account.subtype || account.type}</p>
              <p className="text-xs text-[#8B6F47] font-mono">{maskAccountId(account.account_id)}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {accountTransactions.length > 0 && (
              <span className="text-xs text-[#556B2F] bg-white px-2 py-1 rounded">
                {accountTransactions.length} transactions
              </span>
            )}
            {accountTransactions.length > 0 && (
              isExpanded ? (
                <ChevronUp className="h-5 w-5 text-[#556B2F]" />
              ) : (
                <ChevronDown className="h-5 w-5 text-[#556B2F]" />
              )
            )}
          </div>
        </div>

        <div className="mt-4 space-y-2">
          {account.type === 'credit' && (
            <>
              <div className="flex justify-between text-sm">
                <span className="text-[#556B2F]">Balance:</span>
                <span className="font-medium">{formatCurrency(account.current)}</span>
              </div>
              {account.limit && (
                <div className="flex justify-between text-sm">
                  <span className="text-[#556B2F]">Limit:</span>
                  <span className="font-medium">{formatCurrency(account.limit)}</span>
                </div>
              )}
              {account.amount_due !== undefined && (
                <div className="flex justify-between text-sm">
                  <span className="text-[#556B2F]">Amount Due:</span>
                  <span className="font-medium">{formatCurrency(account.amount_due)}</span>
                </div>
              )}
              {account.minimum_payment_due !== undefined && (
                <div className="flex justify-between text-sm">
                  <span className="text-[#556B2F]">Minimum Payment:</span>
                  <span className="font-medium">{formatCurrency(account.minimum_payment_due)}</span>
                </div>
              )}
              {account.limit && account.current && (() => {
                const utilization = (Math.abs(account.current) / account.limit) * 100
                let utilizationColor = 'text-[#5D4037]'
                if (utilization >= 80) utilizationColor = 'text-red-600 font-bold'
                else if (utilization >= 50) utilizationColor = 'text-yellow-600 font-semibold'
                else if (utilization >= 30) utilizationColor = 'text-green-600'
                
                return (
                  <div className="flex justify-between text-sm">
                    <span className="text-[#556B2F]">Utilization:</span>
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
                <span className="text-[#556B2F]">Balance:</span>
                <span className="font-medium">{formatCurrency(account.current)}</span>
              </div>
              {account.interest_rate && (
                <div className="flex justify-between text-sm">
                  <span className="text-[#556B2F]">Interest Rate:</span>
                  <span className="font-medium">{account.interest_rate.toFixed(2)}%</span>
                </div>
              )}
              {account.next_payment_due_date && (
                <div className="flex justify-between text-sm">
                  <span className="text-[#556B2F]">Next Payment:</span>
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
                    <span className="text-[#556B2F] font-medium">Available Balance:</span>
                    <p className="text-xs text-[#8B6F47] mt-0.5">
                      Immediate usable funds for transactions
                    </p>
                  </div>
                  <span className="font-semibold text-green-600">
                    {formatCurrency(account.available)}
                  </span>
                </div>
                <div className="flex justify-between text-sm border-t pt-2">
                  <div>
                    <span className="text-[#556B2F] font-medium">Current Balance:</span>
                    <p className="text-xs text-[#8B6F47] mt-0.5">
                      Total including pending transactions
                    </p>
                  </div>
                  <span className="font-medium text-[#5D4037]">
                    {formatCurrency(account.current)}
                  </span>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Transactions below account */}
      {isExpanded && accountTransactions.length > 0 && (
        <div className="mt-2 ml-4 border-l-2 border-[#D4C4B0] pl-4">
          <TransactionTable transactions={accountTransactions.map((tx: any) => ({
            account_id: tx.account_id || account.id,
            account_type: account.type,
            account_subtype: account.subtype || null,
            account_name: account.name,
            date: tx.date,
            amount: tx.amount,
            merchant_name: tx.merchant_name || null,
            merchant_entity_id: null,
            payment_channel: null,
            primary_category: tx.primary_category || null,
            detailed_category: tx.detailed_category || null,
            pending: false,
            id: tx.id
          }))} />
        </div>
      )}
    </div>
  )
}


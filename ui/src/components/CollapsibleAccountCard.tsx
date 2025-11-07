import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import AccountCard from './AccountCard'
import TransactionTable from './TransactionTable'

interface CollapsibleAccountCardProps {
  account: any
  transactions: any[]
  windowDays: number
}

export default function CollapsibleAccountCard({ 
  account, 
  transactions, 
  windowDays 
}: CollapsibleAccountCardProps) {
  const [isExpanded, setIsExpanded] = useState(true)
  
  // Filter transactions for this account
  const accountTransactions = transactions.filter(
    (tx) => tx.account_id === account.account_id
  )

  const formatCurrency = (amount: number | null | undefined) => {
    if (amount === null || amount === undefined) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(Math.abs(amount))
  }

  return (
    <div className="border rounded-lg overflow-hidden bg-white shadow-sm">
      {/* Header - always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 bg-[#E8F5E9] hover:bg-[#F5E6D3] transition-colors text-left"
      >
        <div className="flex items-center space-x-3 flex-1">
          {isExpanded ? (
            <ChevronUp className="h-5 w-5 text-[#8B6F47] flex-shrink-0" />
          ) : (
            <ChevronDown className="h-5 w-5 text-[#8B6F47] flex-shrink-0" />
          )}
          <div className="flex-1">
            <h3 className="font-semibold text-[#5D4037]">{account.name}</h3>
            <div className="flex items-center space-x-4 mt-1">
              <p className="text-sm text-[#556B2F]">
                {accountTransactions.length} transactions ({windowDays} days)
              </p>
              {account.type === 'depository' && account.current && (
                <p className="text-sm font-medium text-[#5D4037]">
                  Balance: {formatCurrency(account.current)}
                </p>
              )}
              {account.type === 'credit' && account.current && account.limit && (
                <p className="text-sm font-medium text-[#5D4037]">
                  {formatCurrency(account.current)} / {formatCurrency(account.limit)}
                </p>
              )}
            </div>
          </div>
        </div>
      </button>

      {/* Content - collapsible */}
      {isExpanded && (
        <div className="p-4 bg-white border-t">
          <AccountCard account={account} />
          {accountTransactions.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-semibold text-[#556B2F] mb-2">
                Transactions for this account
              </h4>
              <TransactionTable transactions={accountTransactions} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}


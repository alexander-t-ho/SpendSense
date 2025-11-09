import { ArrowUpCircle, ArrowDownCircle } from 'lucide-react'

interface Transaction {
  account_id: string
  account_type: string
  account_subtype: string | null
  account_name: string
  date: string
  amount: number
  merchant_name: string | null
  merchant_entity_id: string | null
  payment_channel: string | null
  primary_category: string | null
  detailed_category: string | null
  pending: boolean
}

interface TransactionTableProps {
  transactions: Transaction[]
}

function maskAccountId(accountId: string): string {
  if (!accountId || accountId.length < 4) return accountId
  const last4 = accountId.slice(-4)
  return last4  // Just show last 4 digits
}

function getAccountTypeLabel(accountType: string, accountSubtype: string | null): string {
  if (accountType === 'credit') return 'Credit Card'
  if (accountType === 'depository') {
    if (accountSubtype === 'checking') return 'Checking'
    if (accountSubtype === 'savings') return 'Savings'
    return 'Banking'
  }
  if (accountType === 'loan') {
    if (accountSubtype === 'mortgage') return 'Mortgage'
    if (accountSubtype === 'student_loan') return 'Student Loan'
    return 'Loan'
  }
  return accountType.charAt(0).toUpperCase() + accountType.slice(1)
}

export default function TransactionTable({ transactions }: TransactionTableProps) {
  if (!transactions || transactions.length === 0) {
    return (
<<<<<<< HEAD
      <div className="bg-white shadow-lg rounded-xl p-6 text-center text-[#8B6F47] ring-1 ring-[#D4C4B0]">
=======
      <div className="bg-white shadow rounded-lg p-6 text-center text-[#8B6F47]">
>>>>>>> 8fa267a461e5ea19895459dde8fa79dd393d6af3
        <p>No transactions to display</p>
      </div>
    )
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(Math.abs(amount))
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  // Group transactions by account and sort: pending first, then by date
  const transactionsByAccount = transactions.reduce((acc, tx) => {
    if (!acc[tx.account_id]) {
      acc[tx.account_id] = {
        transactions: [],
        account_type: tx.account_type,
        account_subtype: tx.account_subtype,
        account_name: tx.account_name,
      }
    }
    acc[tx.account_id].transactions.push(tx)
    return acc
  }, {} as Record<string, { transactions: Transaction[], account_type: string, account_subtype: string | null, account_name: string }>)
  
  // Sort transactions: pending first, then by date descending
  for (const accountData of Object.values(transactionsByAccount)) {
    accountData.transactions.sort((a, b) => {
      // Pending transactions first
      if (a.pending && !b.pending) return -1
      if (!a.pending && b.pending) return 1
      // Then by date descending
      return new Date(b.date).getTime() - new Date(a.date).getTime()
    })
  }

  return (
    <div className="space-y-6">
      {Object.entries(transactionsByAccount).map(([accountId, accountData]) => {
        const accountTypeLabel = getAccountTypeLabel(accountData.account_type, accountData.account_subtype)
        return (
<<<<<<< HEAD
        <div key={accountId} className="bg-white shadow-lg rounded-xl overflow-hidden ring-1 ring-[#D4C4B0]">
          <div className="px-6 py-4 border-b border-[#D4C4B0] bg-gradient-to-r from-[#F5E6D3] to-white">
=======
        <div key={accountId} className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-[#D4C4B0] bg-[#E8F5E9]">
>>>>>>> 8fa267a461e5ea19895459dde8fa79dd393d6af3
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-[#5D4037]">
                  {accountData.account_name}
                </h3>
                <p className="text-sm text-[#556B2F]">
                  {accountTypeLabel} • ...{maskAccountId(accountId)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-[#5D4037]">{accountData.transactions.length} transactions</p>
                <p className="text-xs text-[#8B6F47]">Last 30 days</p>
              </div>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
<<<<<<< HEAD
              <thead className="bg-gradient-to-r from-[#F5E6D3] to-white">
=======
              <thead className="bg-[#E8F5E9]">
>>>>>>> 8fa267a461e5ea19895459dde8fa79dd393d6af3
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#8B6F47] uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#8B6F47] uppercase tracking-wider">
                    Merchant
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#8B6F47] uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-[#8B6F47] uppercase tracking-wider">
                    Channel
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-[#8B6F47] uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-[#8B6F47] uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
<<<<<<< HEAD
              <tbody className="bg-white divide-y divide-[#D4C4B0]">
=======
              <tbody className="bg-white divide-y divide-gray-200">
>>>>>>> 8fa267a461e5ea19895459dde8fa79dd393d6af3
                {accountData.transactions.map((tx, index) => {
                  const isExpense = tx.amount < 0
                  
                  return (
<<<<<<< HEAD
                    <tr key={index} className="hover:bg-[#F5E6D3]/50">
=======
                    <tr key={index} className="hover:bg-[#E8F5E9]">
>>>>>>> 8fa267a461e5ea19895459dde8fa79dd393d6af3
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[#5D4037]">
                        {formatDate(tx.date)}
                      </td>
                      <td className="px-6 py-4 text-sm text-[#5D4037]">
                        <div>
                          <div className="font-medium">
                            {tx.merchant_name || tx.merchant_entity_id || 'Unknown'}
                          </div>
                          {tx.merchant_entity_id && tx.merchant_name && (
                            <div className="text-xs text-[#8B6F47]">ID: {tx.merchant_entity_id}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-[#556B2F]">
                        <div>
                          <div>{tx.primary_category || 'N/A'}</div>
                          {tx.detailed_category && tx.detailed_category !== tx.primary_category && (
                            <div className="text-xs text-[#8B6F47]">{tx.detailed_category}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-[#8B6F47] capitalize">
                        {tx.payment_channel || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                        <div className="flex items-center justify-end space-x-1">
                          {isExpense ? (
<<<<<<< HEAD
                            <ArrowDownCircle className="h-4 w-4 text-[#5D4037]" />
                          ) : (
                            <ArrowUpCircle className="h-4 w-4 text-[#556B2F]" />
                          )}
                          <span className={isExpense ? 'text-[#5D4037] font-medium' : 'text-[#556B2F] font-medium'}>
=======
                            <ArrowDownCircle className="h-4 w-4 text-red-500" />
                          ) : (
                            <ArrowUpCircle className="h-4 w-4 text-green-500" />
                          )}
                          <span className={isExpense ? 'text-red-600 font-medium' : 'text-green-600 font-medium'}>
>>>>>>> 8fa267a461e5ea19895459dde8fa79dd393d6af3
                            {isExpense ? '-' : '+'}{formatCurrency(tx.amount)}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        {tx.pending ? (
<<<<<<< HEAD
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#F5E6D3] text-[#8B6F47] border border-[#D4C4B0]">
                            Pending
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#556B2F]/20 text-[#556B2F] border border-[#556B2F]/30">
=======
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            Pending
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
>>>>>>> 8fa267a461e5ea19895459dde8fa79dd393d6af3
                            Posted
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
        )
      })}
    </div>
  )
}


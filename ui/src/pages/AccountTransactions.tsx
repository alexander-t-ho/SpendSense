import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchUserDetail } from '../services/api'
import TransactionTable from '../components/TransactionTable'
import { ArrowLeft, Wallet, CreditCard, Building2, ChevronDown } from 'lucide-react'

export default function AccountTransactions() {
  const { userId, accountId } = useParams<{ userId: string; accountId: string }>()
  const navigate = useNavigate()
  const [transactionWindow, setTransactionWindow] = useState<30 | 180>(30)
  const [showDropdown, setShowDropdown] = useState(false)

  const { data: user, isLoading } = useQuery({
    queryKey: ['user', userId, transactionWindow],
    queryFn: () => fetchUserDetail(userId!, transactionWindow),
    enabled: !!userId,
  })

  if (isLoading) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-[#F5E6D3] via-[#D4C4B0] to-[#5D4037]">
        <div className="flex items-center justify-center h-screen">
          <div className="text-[#8B6F47]">Loading transactions...</div>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-[#F5E6D3] via-[#D4C4B0] to-[#5D4037]">
        <div className="flex items-center justify-center h-screen">
          <div className="text-[#8B6F47]">User not found</div>
        </div>
      </div>
    )
  }

  // Find the account
  const account = user.accounts?.find((acc: any) => acc.id === accountId)
  
  if (!account) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-[#F5E6D3] via-[#D4C4B0] to-[#5D4037]">
        <div className="flex items-center justify-center h-screen">
          <div className="text-[#8B6F47]">Account not found</div>
        </div>
      </div>
    )
  }

  // Filter transactions for this account
  const accountTransactions = (user.transactions || []).filter((tx: any) => 
    tx.account_id === account.account_id
  )

  const getAccountIcon = (type: string, subtype: string) => {
    if (type === "credit") {
      return <CreditCard className="h-6 w-6" />;
    } else if (type === "depository") {
      if (subtype === "checking") {
        return <Wallet className="h-6 w-6" />;
      }
      return <Building2 className="h-6 w-6" />;
    }
    return <Wallet className="h-6 w-6" />;
  };

  const formatBalance = (amount: number | null | undefined) => {
    if (amount === null || amount === undefined) return "$0.00";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-[#F5E6D3] via-[#D4C4B0] to-[#5D4037]">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Back button */}
        <button
          onClick={() => navigate(-1)}
          className="mb-6 flex items-center gap-2 text-[#5D4037] hover:text-[#556B2F] transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
          <span>Back</span>
        </button>

        {/* Account Header */}
        <div className="mb-6 rounded-3xl bg-white p-6 shadow-lg ring-1 ring-[#D4C4B0]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-[#556B2F]/20 p-3">
                <div className="text-[#556B2F]">
                  {getAccountIcon(account.type, account.subtype)}
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-[#5D4037]">{account.name || "Unnamed Account"}</h1>
                <p className="text-sm text-[#8B6F47]">
                  {account.type === "credit" ? "Credit Card" : account.subtype ? account.subtype.charAt(0).toUpperCase() + account.subtype.slice(1) : "Account"}
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-[#8B6F47]">Balance</div>
              <div className="text-2xl font-semibold text-[#5D4037]">
                {account.type === "credit" 
                  ? formatBalance(account.current ? Math.abs(account.current) : 0)
                  : formatBalance(account.available ?? account.current ?? 0)
                }
              </div>
              {account.type === "credit" && account.limit && (
                <div className="text-xs text-[#8B6F47] mt-1">
                  Limit: {formatBalance(account.limit)}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Transactions */}
        <div className="rounded-3xl bg-white p-6 shadow-lg ring-1 ring-[#D4C4B0]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-[#5D4037]">
              Transactions ({accountTransactions.length})
            </h2>
            <div className="relative">
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-[#5D4037] bg-[#F5E6D3] hover:bg-[#D4C4B0] rounded-lg transition-colors border border-[#D4C4B0]"
              >
                <span>Last {transactionWindow} days</span>
                <ChevronDown className={`h-4 w-4 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
              </button>
              {showDropdown && (
                <>
                  <div 
                    className="fixed inset-0 z-10" 
                    onClick={() => setShowDropdown(false)}
                  />
                  <div className="absolute right-0 mt-2 w-40 bg-white rounded-lg shadow-lg ring-1 ring-[#D4C4B0] z-20">
                    <button
                      onClick={() => {
                        setTransactionWindow(30)
                        setShowDropdown(false)
                      }}
                      className={`w-full text-left px-4 py-2 text-sm ${
                        transactionWindow === 30 
                          ? 'bg-[#F5E6D3] text-[#5D4037] font-medium' 
                          : 'text-[#8B6F47] hover:bg-[#F5E6D3]'
                      } rounded-t-lg transition-colors`}
                    >
                      Last 30 days
                    </button>
                    <button
                      onClick={() => {
                        setTransactionWindow(180)
                        setShowDropdown(false)
                      }}
                      className={`w-full text-left px-4 py-2 text-sm ${
                        transactionWindow === 180 
                          ? 'bg-[#F5E6D3] text-[#5D4037] font-medium' 
                          : 'text-[#8B6F47] hover:bg-[#F5E6D3]'
                      } rounded-b-lg transition-colors`}
                    >
                      Last 180 days
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
          {accountTransactions.length === 0 ? (
            <div className="text-center py-12 text-[#8B6F47]">
              No transactions found for this account
            </div>
          ) : (
            <TransactionTable transactions={accountTransactions.map((tx: any) => ({
              account_id: tx.account_id || account.account_id,
              account_type: account.type,
              account_subtype: account.subtype || null,
              account_name: account.name,
              date: tx.date,
              amount: tx.amount,
              merchant_name: tx.merchant_name || null,
              merchant_entity_id: tx.merchant_entity_id || null,
              payment_channel: tx.payment_channel || null,
              primary_category: tx.primary_category || null,
              detailed_category: tx.detailed_category || null,
              pending: tx.pending || false,
              id: tx.id || tx.transaction_id
            }))} />
          )}
        </div>
      </div>
    </div>
  )
}


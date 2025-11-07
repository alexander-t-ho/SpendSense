import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { useEffect } from 'react'
import { X, CheckCircle2, CheckCircle, Calendar } from 'lucide-react'
import { SubscriptionWebSocket, SubscriptionCancellationUpdate } from '../services/subscriptionWebSocket'

interface Subscription {
  merchant_name: string
  average_amount: number
  cadence: string
  occurrences: number
  last_transaction: string
  cancelled?: boolean
}

interface ActionableRecommendationProps {
  recommendation: {
    id: string
    title: string
    recommendation_text: string
    expected_impact: string
    action_items?: string[]
    priority?: string
    content_id?: string
  }
  userId: string
}

export default function ActionableRecommendation({ recommendation, userId }: ActionableRecommendationProps) {
  const queryClient = useQueryClient()
  
  // Get cancelled subscriptions from query cache (shared across all instances)
  const { data: cancelledSubsData } = useQuery({
    queryKey: ['cancelled-subscriptions', userId],
    queryFn: async () => {
      const response = await fetch(`/api/user/${userId}/subscriptions/cancelled`)
      if (!response.ok) {
        if (response.status === 404) {
          return { cancelled_merchants: [], total: 0 }
        }
        throw new Error('Failed to fetch cancelled subscriptions')
      }
      return response.json()
    },
    enabled: !!userId,
    retry: false,
  })

  // Initialize cancelled subscriptions from API and mark already-cancelled ones
  const cancelledMerchantNames = new Set(
    (cancelledSubsData?.cancelled_merchants || []).map((m: { merchant_name: string }) => m.merchant_name)
  )

  // Extract savings amount from expected_impact (e.g., "Save $300/year")
  const extractSavings = (impactText: string): { yearly?: number; monthly?: number } => {
    const yearlyMatch = impactText.match(/Save\s+\$?([\d,]+)\/year/)
    const monthlyMatch = impactText.match(/reduce monthly expenses by\s+\$?([\d,]+)/i)
    
    return {
      yearly: yearlyMatch ? parseFloat(yearlyMatch[1].replace(/,/g, '')) : undefined,
      monthly: monthlyMatch ? parseFloat(monthlyMatch[1].replace(/,/g, '')) : undefined,
    }
  }

  const savings = extractSavings(recommendation.expected_impact || '')

  // Check if this is a subscription-related recommendation
  const isSubscriptionRecommendation = 
    recommendation.content_id === 'audit_subscriptions' ||
    recommendation.title.toLowerCase().includes('subscription') ||
    recommendation.recommendation_text?.toLowerCase().includes('subscription')

  // Fetch user subscriptions if this is a subscription recommendation
  const { data: subscriptionsData, isLoading: isLoadingSubs } = useQuery({
    queryKey: ['user-subscriptions', userId],
    queryFn: async () => {
      const response = await fetch(`/api/user/${userId}/subscriptions`)
      if (!response.ok) {
        if (response.status === 404) {
          // User might not have subscriptions, return empty array
          return { subscriptions: [], total: 0 }
        }
        throw new Error('Failed to fetch subscriptions')
      }
      return response.json()
    },
    enabled: isSubscriptionRecommendation && !!userId,
    retry: false,
  })

  // WebSocket connection for real-time cancellation updates
  useEffect(() => {
    if (!isSubscriptionRecommendation || !userId) return

    const ws = new SubscriptionWebSocket(userId, (update: SubscriptionCancellationUpdate) => {
      console.log('Subscription cancellation update received:', update)
      
      // Update the cancelled subscriptions cache
      queryClient.setQueryData(['cancelled-subscriptions', userId], (oldData: any) => {
        if (!oldData) {
          return {
            cancelled_merchants: update.cancelled 
              ? [{ merchant_name: update.merchant_name, cancelled_at: update.timestamp }]
              : [],
            total: update.cancelled ? 1 : 0
          }
        }

        const merchants = [...(oldData.cancelled_merchants || [])]
        
        if (update.cancelled) {
          // Add to cancelled list if not already there
          if (!merchants.find((m: any) => m.merchant_name === update.merchant_name)) {
            merchants.push({
              merchant_name: update.merchant_name,
              cancelled_at: update.timestamp
            })
          }
        } else {
          // Remove from cancelled list
          const index = merchants.findIndex((m: any) => m.merchant_name === update.merchant_name)
          if (index !== -1) {
            merchants.splice(index, 1)
          }
        }

        return {
          ...oldData,
          cancelled_merchants: merchants,
          total: merchants.length
        }
      })

      // Invalidate subscriptions query to refresh the cancelled status
      queryClient.invalidateQueries({ queryKey: ['user-subscriptions', userId] })
    })

    ws.connect()

    return () => {
      ws.disconnect()
    }
  }, [userId, isSubscriptionRecommendation, queryClient])

  // Cancel subscription mutation
  const cancelMutation = useMutation({
    mutationFn: async (merchantName: string) => {
      const response = await fetch(`/api/user/${userId}/subscriptions/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ merchant_name: merchantName }),
      })
      if (!response.ok) {
        throw new Error('Failed to cancel subscription')
      }
      return response.json()
    },
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['cancelled-subscriptions', userId] })
      queryClient.invalidateQueries({ queryKey: ['user-subscriptions', userId] })
    },
  })

  // Uncancel subscription mutation
  const uncancelMutation = useMutation({
    mutationFn: async (merchantName: string) => {
      const response = await fetch(`/api/user/${userId}/subscriptions/uncancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ merchant_name: merchantName }),
      })
      if (!response.ok) {
        throw new Error('Failed to uncancel subscription')
      }
      return response.json()
    },
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['cancelled-subscriptions', userId] })
      queryClient.invalidateQueries({ queryKey: ['user-subscriptions', userId] })
    },
  })

  const handleCancel = (merchantName: string) => {
    cancelMutation.mutate(merchantName)
  }

  const handleUncancel = (merchantName: string) => {
    uncancelMutation.mutate(merchantName)
  }

  // Filter active subscriptions (not cancelled)
  const activeSubscriptions = (subscriptionsData?.subscriptions || []).filter(
    (sub: Subscription) => !cancelledMerchantNames.has(sub.merchant_name)
  )

  // Calculate savings from cancelled subscriptions
  const cancelledSubsList = (subscriptionsData?.subscriptions || []).filter(
    (sub: Subscription) => cancelledMerchantNames.has(sub.merchant_name)
  )
  
  const totalMonthlySavings = cancelledSubsList.reduce(
    (sum: number, sub: Subscription) => {
      const monthlyAmount = sub.cadence === 'monthly' ? sub.average_amount : sub.average_amount / 4.33
      return sum + monthlyAmount
    },
    0
  )
  
  const totalYearlySavings = totalMonthlySavings * 12

  return (
    <div className="bg-white border border-[#D4C4B0] rounded-lg p-6 shadow-sm">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-[#5D4037] mb-2">{recommendation.title}</h3>
          <p className="text-sm text-[#556B2F] mb-4">{recommendation.recommendation_text}</p>
        </div>
        {recommendation.priority && (
          <span
            className={`px-2 py-1 text-xs rounded-full ${
              recommendation.priority === 'high'
                ? 'bg-red-100 text-red-800'
                : recommendation.priority === 'medium'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-[#F5E6D3] text-[#5D4037]'
            }`}
          >
            {recommendation.priority}
          </span>
        )}
      </div>

      {/* Savings Banner */}
      {cancelledMerchantNames.size > 0 ? (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm font-semibold text-green-900">
            💰 You will save ${totalYearlySavings.toFixed(2)}/year by canceling {cancelledMerchantNames.size} subscription{cancelledMerchantNames.size !== 1 ? 's' : ''}
          </p>
          <p className="text-xs text-green-700 mt-1">
            Monthly savings: ${totalMonthlySavings.toFixed(2)}
          </p>
        </div>
      ) : savings.yearly ? (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm font-semibold text-green-900">
            💰 You can save ${savings.yearly.toLocaleString()}/year by canceling unused subscriptions
          </p>
        </div>
      ) : null}

      {/* Subscription List with Cancel Buttons */}
      {isSubscriptionRecommendation && (
        <div className="mt-4">
          {isLoadingSubs ? (
            <div className="text-sm text-[#8B6F47]">Loading your subscriptions...</div>
          ) : activeSubscriptions.length > 0 ? (
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-[#5D4037] mb-2">Your Subscriptions</h4>
              {activeSubscriptions.map((subscription: Subscription, idx: number) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-[#E8F5E9] border border-[#D4C4B0] rounded-lg"
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium text-[#5D4037]">{subscription.merchant_name}</p>
                    <p className="text-xs text-[#556B2F] mt-1">
                      ${subscription.average_amount.toFixed(2)}/{subscription.cadence}
                      {subscription.cadence === 'monthly' && (
                        <span className="ml-2">
                          (${(subscription.average_amount * 12).toFixed(2)}/year)
                        </span>
                      )}
                    </p>
                  </div>
                  <button
                    onClick={() => handleCancel(subscription.merchant_name)}
                    className="ml-4 px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              ))}
            </div>
          ) : subscriptionsData?.subscriptions?.length === 0 ? (
            <div className="text-sm text-[#8B6F47] p-3 bg-[#E8F5E9] rounded">
              No active subscriptions found.
            </div>
          ) : null}

          {/* Cancelled Subscriptions */}
          {cancelledMerchantNames.size > 0 && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle2 className="w-4 h-4 text-green-600" />
                <p className="text-sm font-semibold text-green-900">
                  Cancelled Subscriptions ({cancelledMerchantNames.size})
                </p>
              </div>
              <ul className="space-y-2">
                {cancelledSubsList.map((sub: Subscription) => (
                  <li key={sub.merchant_name} className="text-sm text-green-800 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <X className="w-3 h-3" />
                      <span>{sub.merchant_name}</span>
                    </div>
                    <button
                      onClick={() => handleUncancel(sub.merchant_name)}
                      disabled={uncancelMutation.isPending}
                      className="ml-2 px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                    >
                      Restore
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Action Plan Approval Section */}
      {recommendation.action_items && recommendation.action_items.length > 0 && 
       (recommendation.content_id === 'reduce_utilization_specific_card' || 
        recommendation.content_id === 'stop_minimum_payments' ||
        recommendation.content_id === 'build_emergency_fund' ||
        recommendation.content_id?.startsWith('reduce_frequent_merchant_spending') ||
        recommendation.content_id?.startsWith('reduce_category_spending') ||
        recommendation.title.toLowerCase().includes('payment plan') ||
        recommendation.title.toLowerCase().includes('savings plan') ||
        recommendation.title.toLowerCase().includes('reduce spending')) && (
        <ActionPlanApproval 
          recommendationId={recommendation.id}
          userId={userId}
          actionItems={recommendation.action_items}
        />
      )}

      {/* Expected Impact */}
      {recommendation.expected_impact && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-xs font-semibold text-blue-900 mb-1">Expected Impact:</p>
          <p className="text-sm text-[#5D4037]">{recommendation.expected_impact}</p>
        </div>
      )}

      {/* Disclaimer */}
      <div className="mt-4 pt-3 border-t border-[#D4C4B0]">
        <p className="text-xs text-[#8B6F47] italic">
          This is educational content, not financial advice. Consult a licensed advisor for personalized guidance.
        </p>
      </div>
    </div>
  )
}

// Action Plan Approval Component
interface ActionPlanApprovalProps {
  recommendationId: string
  userId: string
  actionItems: string[]
}

function ActionPlanApproval({ recommendationId, userId, actionItems }: ActionPlanApprovalProps) {
  const queryClient = useQueryClient()
  
  // Check if plan is already approved
  const { data: approvedPlan, isLoading: isLoadingPlan } = useQuery({
    queryKey: ['approved-action-plan', userId, recommendationId],
    queryFn: async () => {
      const response = await fetch(`/api/user/${userId}/action-plans/${recommendationId}`)
      if (!response.ok) {
        if (response.status === 404) {
          return null
        }
        throw new Error('Failed to fetch approved plan')
      }
      return response.json()
    },
    enabled: !!userId && !!recommendationId,
    retry: false,
  })

  // Approve plan mutation
  const approveMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/user/${userId}/action-plans/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ recommendation_id: recommendationId }),
      })
      if (!response.ok) {
        throw new Error('Failed to approve action plan')
      }
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approved-action-plan', userId, recommendationId] })
    },
  })

  // Cancel plan mutation
  const cancelMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/user/${userId}/action-plans/${recommendationId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (!response.ok) {
        throw new Error('Failed to cancel action plan')
      }
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approved-action-plan', userId, recommendationId] })
    },
  })

  if (isLoadingPlan) {
    return (
      <div className="mt-4 p-3 bg-[#E8F5E9] rounded-lg">
        <p className="text-sm text-[#8B6F47]">Loading plan status...</p>
      </div>
    )
  }

  if (approvedPlan) {
    return (
      <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-green-900 mb-2">Action Plan Approved ✓</h4>
            <p className="text-xs text-green-700 mb-3">
              You've committed to this plan. Track your progress and stay on target!
            </p>
            <div className="space-y-2 mb-3">
              <p className="text-xs font-semibold text-green-900">Your Plan:</p>
              <ul className="space-y-1">
                {actionItems.map((item, idx) => (
                  <li key={idx} className="text-xs text-green-800 flex items-start">
                    <span className="text-green-600 mr-2 mt-0.5">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <button
              onClick={() => cancelMutation.mutate()}
              disabled={cancelMutation.isPending}
              className="text-xs text-red-600 hover:text-red-800 font-medium disabled:opacity-50"
            >
              Cancel Plan
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Check if this is a spending pattern recommendation with multiple options
  const isSpendingPattern = actionItems.some(item => item.toLowerCase().startsWith('option 1'))
  
  return (
    <div className="mt-4 p-4 bg-[#E8F5E9] border border-[#D4C4B0] rounded-lg">
      <div className="flex items-start gap-3 mb-3">
        <Calendar className="w-5 h-5 text-[#556B2F] mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h4 className="text-sm font-semibold text-[#5D4037] mb-2">
            {isSpendingPattern ? 'Choose Your Savings Plan' : 'Action Plan'}
          </h4>
          <p className="text-xs text-[#556B2F] mb-3">
            {isSpendingPattern 
              ? 'Review the options below and choose the one that best fits your lifestyle:'
              : 'Review the plan below and approve it to start tracking your progress:'}
          </p>
          <div className="space-y-2 mb-4">
            {isSpendingPattern ? (
              // Display options as selectable cards
              <div className="space-y-3">
                {actionItems
                  .filter(item => item.toLowerCase().startsWith('option'))
                  .map((item, idx) => {
                    // Extract option number and savings info
                    const optionMatch = item.match(/Option (\d+):\s*(.+?)(?:\s*-\s*Save\s+\$([\d,]+)\/(year|month))?/i)
                    const optionNum = optionMatch ? optionMatch[1] : (idx + 1).toString()
                    const optionText = optionMatch ? optionMatch[2] : item.replace(/^Option \d+:\s*/i, '')
                    const savingsAmount = optionMatch ? optionMatch[3] : null
                    const savingsPeriod = optionMatch ? optionMatch[4] : null
                    
                    return (
                      <div
                        key={idx}
                        className="p-3 bg-white border-2 border-[#D4C4B0] rounded-lg hover:border-blue-400 transition-colors cursor-pointer"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs font-bold text-[#556B2F]">Option {optionNum}</span>
                              {savingsAmount && (
                                <span className="text-xs font-semibold text-green-600">
                                  Save ${parseFloat(savingsAmount.replace(/,/g, '')).toLocaleString()}/{savingsPeriod}
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-[#556B2F]">{optionText}</p>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                {actionItems.find(item => item.toLowerCase().includes('choose the option')) && (
                  <p className="text-xs text-[#8B6F47] italic mt-2">
                    {actionItems.find(item => item.toLowerCase().includes('choose the option'))}
                  </p>
                )}
              </div>
            ) : (
              // Display regular action items as list
              <ul className="space-y-2">
                {actionItems.map((item, idx) => (
                  <li key={idx} className="text-xs text-[#556B2F] flex items-start">
                    <span className="text-[#556B2F] mr-2 mt-0.5 font-bold">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <button
            onClick={() => approveMutation.mutate()}
            disabled={approveMutation.isPending}
            className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {approveMutation.isPending 
              ? 'Approving...' 
              : isSpendingPattern 
                ? '✓ Approve & Start This Savings Plan' 
                : '✓ Approve & Start This Plan'}
          </button>
        </div>
      </div>
    </div>
  )
}


import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getConsentStatus, grantConsent, revokeConsent } from '../services/api'
import { ConsentWebSocket } from '../services/websocket'
import { AlertCircle, CheckCircle, X } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'

interface ConsentBannerProps {
  userId: string
  onConsentChange?: (consented: boolean) => void
  readOnly?: boolean  // If true, only show status without grant/revoke buttons (for admin views)
}

export default function ConsentBanner({ userId, onConsentChange, readOnly = false }: ConsentBannerProps) {
  const queryClient = useQueryClient()
  const [dismissed, setDismissed] = useState(false)
  const wsRef = useRef<ConsentWebSocket | null>(null)

  const { data: consent, isLoading } = useQuery({
    queryKey: ['consent', userId],
    queryFn: () => getConsentStatus(userId),
    enabled: !!userId,
  })

  // Set up WebSocket for real-time updates (only if not read-only)
  useEffect(() => {
    if (!userId || readOnly) return

    const handleConsentUpdate = (consented: boolean, data: any) => {
      // Update the cache immediately
      queryClient.setQueryData(['consent', userId], data)
      // Invalidate recommendations to refetch
      queryClient.invalidateQueries({ queryKey: ['recommendations', userId] })
      onConsentChange?.(consented)
    }

    wsRef.current = new ConsentWebSocket(userId, handleConsentUpdate)
    wsRef.current.connect()

    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect()
      }
    }
  }, [userId, queryClient, onConsentChange, readOnly])

  const grantMutation = useMutation({
    mutationFn: async () => {
      const result = await grantConsent(userId)
      return result
    },
    onSuccess: (data) => {
      // Optimistically update the cache immediately
      queryClient.setQueryData(['consent', userId], data)
      // Invalidate and refetch recommendations immediately
      queryClient.invalidateQueries({ queryKey: ['recommendations', userId] })
      onConsentChange?.(true)
      // Force immediate refetch to ensure UI updates
      setTimeout(() => {
        queryClient.refetchQueries({ queryKey: ['consent', userId] })
      }, 100)
    },
    onError: (error) => {
      alert(`Failed to grant consent: ${error instanceof Error ? error.message : 'Unknown error'}`)
    },
  })

  const revokeMutation = useMutation({
    mutationFn: () => revokeConsent(userId),
    onSuccess: (data) => {
      // Optimistically update the cache
      queryClient.setQueryData(['consent', userId], data)
      // Invalidate and refetch recommendations immediately
      queryClient.invalidateQueries({ queryKey: ['recommendations', userId] })
      onConsentChange?.(false)
      // Refetch consent status to ensure consistency
      queryClient.refetchQueries({ queryKey: ['consent', userId] })
    },
  })

  const hasConsented = consent?.consented === true

  if (isLoading) {
    return (
      <div className="bg-[#E8F5E9] border-l-4 border-gray-400 p-4 mb-4">
        <div className="flex items-center">
          <div className="text-sm text-[#556B2F]">Loading consent status...</div>
        </div>
      </div>
    )
  }

  if (!consent) {
    return null
  }

  // If user has consented, show a small banner with option to revoke (if not read-only)
  if (hasConsented && !dismissed) {
    return (
      <div className="bg-green-50 border-l-4 border-green-400 p-4 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <CheckCircle className="h-5 w-5 text-green-400 mr-2" />
            <div>
              <p className="text-sm font-medium text-green-800">
                {readOnly ? 'User has consented to personalized recommendations' : 'You have consented to personalized recommendations'}
              </p>
              {!readOnly && (
                <p className="text-xs text-green-600 mt-1">
                  You can revoke consent at any time
                </p>
              )}
              {readOnly && consent.consented_at && (
                <p className="text-xs text-green-600 mt-1">
                  Consent granted on {new Date(consent.consented_at).toLocaleDateString()}
                </p>
              )}
            </div>
          </div>
          {!readOnly && (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  revokeMutation.mutate()
                }}
                className="text-xs text-green-700 hover:text-green-900 underline disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={revokeMutation.isPending}
              >
                {revokeMutation.isPending ? 'Revoking...' : 'Revoke'}
              </button>
              <button
                onClick={() => setDismissed(true)}
                className="text-green-600 hover:text-green-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  // If user hasn't consented, show prominent banner
  if (!hasConsented && !dismissed) {
    return (
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
        <div className="flex items-start">
          <AlertCircle className="h-5 w-5 text-yellow-400 mr-3 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-yellow-800">
              {readOnly ? 'User Has Not Consented' : 'Consent Required for Personalized Recommendations'}
            </h3>
            {readOnly ? (
              <p className="text-sm text-yellow-700 mt-2">
                This user has not consented to data processing. They must grant consent from their own account to receive personalized recommendations.
              </p>
            ) : (
              <>
                <p className="text-sm text-yellow-700 mt-2">
                  To receive personalized financial education and recommendations, we need your consent
                  to process your transaction data. You can revoke this consent at any time.
                </p>
                <div className="mt-4 flex items-center space-x-3">
                  <button
                    onClick={async (e) => {
                      e.preventDefault()
                      try {
                        await grantMutation.mutateAsync()
                      } catch (error) {
                        // Error is handled by mutation's onError
                      }
                    }}
                    disabled={grantMutation.isPending || hasConsented}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-yellow-600 hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {grantMutation.isPending ? 'Processing...' : hasConsented ? 'Consent Granted' : 'Grant Consent'}
                  </button>
                  <button
                    onClick={() => setDismissed(true)}
                    className="text-sm text-yellow-700 hover:text-yellow-900"
                  >
                    Dismiss
                  </button>
                </div>
                <p className="text-xs text-yellow-600 mt-3">
                  <strong>Note:</strong> Without consent, you will not receive personalized recommendations.
                  This is educational content, not financial advice.
                </p>
              </>
            )}
            {readOnly && consent.revoked_at && (
              <p className="text-xs text-yellow-600 mt-2">
                Consent was revoked on {new Date(consent.revoked_at).toLocaleDateString()}
              </p>
            )}
          </div>
        </div>
      </div>
    )
  }

  return null
}


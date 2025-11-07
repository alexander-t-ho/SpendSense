import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getConsentStatus, grantConsent, revokeConsent } from '../services/api'
import { X, CheckCircle, AlertCircle } from 'lucide-react'
import { useState } from 'react'

interface ConsentModalProps {
  userId: string
  isOpen: boolean
  onClose: () => void
  onConsentChange?: (consented: boolean) => void
}

export default function ConsentModal({ userId, isOpen, onClose, onConsentChange }: ConsentModalProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'agreement'>('overview')
  const queryClient = useQueryClient()

  const { data: consent } = useQuery({
    queryKey: ['consent', userId],
    queryFn: () => getConsentStatus(userId),
    enabled: !!userId && isOpen,
  })

  const grantMutation = useMutation({
    mutationFn: async () => {
      const result = await grantConsent(userId)
      return result
    },
    onSuccess: (data) => {
      queryClient.setQueryData(['consent', userId], data)
      queryClient.invalidateQueries({ queryKey: ['recommendations', userId] })
      onConsentChange?.(true)
      onClose()
    },
    onError: (error) => {
      alert(`Failed to grant consent: ${error instanceof Error ? error.message : 'Unknown error'}`)
    },
  })

  const revokeMutation = useMutation({
    mutationFn: () => revokeConsent(userId),
    onSuccess: (data) => {
      queryClient.setQueryData(['consent', userId], data)
      queryClient.invalidateQueries({ queryKey: ['recommendations', userId] })
      onConsentChange?.(false)
    },
  })

  const hasConsented = consent?.consented === true

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={(e) => {
      // Close modal when clicking outside
      if (e.target === e.currentTarget) {
        onClose()
      }
    }}>
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col relative" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#D4C4B0] relative">
          <h2 className="text-2xl font-bold text-[#5D4037]">Data Consent & Privacy</h2>
          <button
            onClick={onClose}
            className="p-2 text-[#5D4037] hover:bg-[#F5E6D3] rounded-md transition-colors relative z-10 cursor-pointer"
            aria-label="Close"
            type="button"
          >
            <X size={24} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[#D4C4B0]">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'overview'
                ? 'text-[#556B2F] border-b-2 border-[#556B2F] bg-[#E8F5E9]'
                : 'text-[#556B2F] hover:bg-[#F5E6D3]'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('agreement')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === 'agreement'
                ? 'text-[#556B2F] border-b-2 border-[#556B2F] bg-[#E8F5E9]'
                : 'text-[#556B2F] hover:bg-[#F5E6D3]'
            }`}
          >
            Full Agreement
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'overview' ? (
            <div className="space-y-4">
              <div className={`p-4 rounded-lg border-2 ${
                hasConsented 
                  ? 'border-green-300 bg-green-50' 
                  : 'border-yellow-300 bg-yellow-50'
              }`}>
                <div className="flex items-center gap-3 mb-2">
                  {hasConsented ? (
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  ) : (
                    <AlertCircle className="h-6 w-6 text-yellow-600" />
                  )}
                  <h3 className="text-lg font-semibold text-[#5D4037]">
                    {hasConsented ? 'Consent Granted' : 'Consent Required'}
                  </h3>
                </div>
                <p className="text-sm text-[#556B2F]">
                  {hasConsented
                    ? 'You have granted consent for personalized financial recommendations. You can revoke this at any time.'
                    : 'To receive personalized financial recommendations, please review and grant consent below.'}
                </p>
              </div>

              <div className="space-y-3">
                <h4 className="font-semibold text-[#5D4037]">What consent allows:</h4>
                <ul className="list-disc list-inside space-y-2 text-sm text-[#556B2F] ml-4">
                  <li>Analysis of your financial transactions to provide personalized recommendations</li>
                  <li>Generation of actionable financial advice based on your spending patterns</li>
                  <li>Category-based budget suggestions tailored to your income and expenses</li>
                  <li>Real-time updates on your financial health and opportunities</li>
                </ul>

                <h4 className="font-semibold text-[#5D4037] mt-4">Your rights:</h4>
                <ul className="list-disc list-inside space-y-2 text-sm text-[#556B2F] ml-4">
                  <li>You can revoke consent at any time</li>
                  <li>Your data is encrypted and securely stored</li>
                  <li>We never share your financial data with third parties</li>
                  <li>You can request data deletion at any time</li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="space-y-4 text-sm text-[#556B2F]">
              <h3 className="text-lg font-semibold text-[#5D4037] mb-4">Data Consent Agreement</h3>
              
              <section className="space-y-3">
                <h4 className="font-semibold text-[#5D4037]">1. Purpose</h4>
                <p>
                  By granting consent, you authorize SpendSense to analyze your financial transaction data 
                  to provide personalized financial recommendations and insights. This includes analysis of 
                  spending patterns, income, and account balances.
                </p>
              </section>

              <section className="space-y-3">
                <h4 className="font-semibold text-[#5D4037]">2. Data Usage</h4>
                <p>
                  Your financial data will be used solely for the purpose of generating personalized 
                  recommendations. We analyze transaction categories, amounts, frequencies, and patterns 
                  to provide actionable financial advice.
                </p>
              </section>

              <section className="space-y-3">
                <h4 className="font-semibold text-[#5D4037]">3. Data Security</h4>
                <p>
                  All data is encrypted in transit and at rest. We follow industry-standard security 
                  practices to protect your financial information. Your data is never shared with 
                  third parties without your explicit consent.
                </p>
              </section>

              <section className="space-y-3">
                <h4 className="font-semibold text-[#5D4037]">4. Your Rights</h4>
                <p>
                  You have the right to revoke consent at any time, request access to your data, 
                  request data deletion, and opt-out of specific features. Revoking consent will 
                  stop the generation of new personalized recommendations.
                </p>
              </section>

              <section className="space-y-3">
                <h4 className="font-semibold text-[#5D4037]">5. Data Retention</h4>
                <p>
                  We retain your financial data only as long as necessary to provide our services. 
                  You can request data deletion at any time, which will be processed within 30 days.
                </p>
              </section>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-[#D4C4B0] bg-[#F5E6D3]">
          {hasConsented ? (
            <button
              onClick={() => revokeMutation.mutate()}
              disabled={revokeMutation.isPending}
              className="w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {revokeMutation.isPending ? 'Revoking...' : 'Revoke Consent'}
            </button>
          ) : (
            <button
              onClick={() => grantMutation.mutate()}
              disabled={grantMutation.isPending}
              className="w-full px-4 py-2 bg-[#556B2F] text-white rounded-md hover:bg-[#6B7A3C] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {grantMutation.isPending ? 'Granting...' : 'Grant Consent'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}


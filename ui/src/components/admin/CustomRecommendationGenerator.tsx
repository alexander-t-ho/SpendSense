import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, Loader2, X, CheckCircle, AlertCircle, Flag } from 'lucide-react'
import RecommendationsDropdown from './RecommendationsDropdown'
import { approveRecommendation, rejectRecommendation, flagRecommendation } from '../../services/operatorApi'

interface CustomRecommendationGeneratorProps {
  userId: string
  contextData?: string
  onRecommendationGenerated?: (recommendation: any) => void
}

export default function CustomRecommendationGenerator({
  userId,
  contextData,
  onRecommendationGenerated
}: CustomRecommendationGeneratorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [prompt, setPrompt] = useState('')
  const [recommendationType, setRecommendationType] = useState<'actionable_recommendation' | 'readings'>('actionable_recommendation')
  const [generatedRec, setGeneratedRec] = useState<any>(null)

  const generateMutation = useMutation({
    mutationFn: async (data: { prompt: string; type: string }) => {
      const response = await fetch('/api/operator/recommendations/generate-custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          admin_prompt: data.prompt,
          recommendation_type: data.type,
          context_data: contextData ? { note: contextData } : undefined,
          window_days: 180
        }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to generate recommendation')
      }
      return response.json()
    },
    onSuccess: (data) => {
      setGeneratedRec(data.recommendation)
      onRecommendationGenerated?.(data.recommendation)
    },
  })

  const handleGenerate = () => {
    if (!prompt.trim()) {
      alert('Please enter a prompt describing the recommendation you want to create.')
      return
    }
    generateMutation.mutate({ prompt, type: recommendationType })
  }

  const handleReset = () => {
    setPrompt('')
    setGeneratedRec(null)
    generateMutation.reset()
  }

  const handleClose = () => {
    setIsOpen(false)
    handleReset()
  }

  // Pre-fill prompt if context data is provided
  useEffect(() => {
    if (contextData && !prompt && !isOpen) {
      setPrompt(`User has: ${contextData}. Create a recommendation based on this observation.`)
    }
  }, [contextData, prompt, isOpen])

  if (!isOpen) {
    return (
      <div className="space-y-2">
        <button
          onClick={() => setIsOpen(true)}
          className="w-full px-4 py-2 bg-[#556B2F] text-white rounded-md hover:bg-[#6B7A3C] transition-colors text-sm font-medium flex items-center gap-2"
        >
          <Send size={16} />
          Create Custom Recommendation
        </button>
        <RecommendationsDropdown userId={userId} />
      </div>
    )
  }

  return (
    <div className="bg-white border border-[#D4C4B0] rounded-lg p-6 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-[#5D4037]">Create Custom Recommendation</h3>
        <button
          onClick={handleClose}
          className="p-1 text-[#556B2F] hover:text-[#5D4037] hover:bg-[#F5E6D3] rounded-md transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      {contextData && (
        <div className="mb-4 p-3 bg-[#E8F5E9] border border-[#556B2F] rounded-md">
          <p className="text-sm text-[#556B2F]">
            <strong>Context:</strong> {contextData}
          </p>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label htmlFor="recommendation-type" className="block text-sm font-medium text-[#556B2F] mb-2">
            Type:
          </label>
          <select
            id="recommendation-type"
            value={recommendationType}
            onChange={(e) => setRecommendationType(e.target.value as 'actionable_recommendation' | 'readings')}
            className="w-full px-3 py-2 border border-[#D4C4B0] rounded-md focus:ring-[#556B2F] focus:border-[#556B2F] mb-4"
            disabled={generateMutation.isPending}
          >
            <option value="actionable_recommendation">Recommendation (Actionable)</option>
            <option value="readings">Readings (Educational Content)</option>
          </select>
        </div>
        <div>
          <label htmlFor="admin-prompt" className="block text-sm font-medium text-[#556B2F] mb-2">
            Describe the {recommendationType === 'readings' ? 'educational content' : 'recommendation'} you want to create:
          </label>
          <textarea
            id="admin-prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., User has 2+ subscriptions in same category: streaming (YouTube Premium, HBO Max, Spotify). Create a recommendation to help them consolidate."
            className="w-full px-3 py-2 border border-[#D4C4B0] rounded-md focus:ring-[#556B2F] focus:border-[#556B2F] min-h-[100px]"
            disabled={generateMutation.isPending}
          />
          <p className="mt-1 text-xs text-[#8B6F47]">
            Describe the observation or situation you want to create a recommendation for. The RAG pipeline will format it into an actionable recommendation.
          </p>
        </div>

        <button
          onClick={handleGenerate}
          disabled={generateMutation.isPending || !prompt.trim()}
          className="w-full px-4 py-2 bg-[#556B2F] text-white rounded-md hover:bg-[#6B7A3C] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {generateMutation.isPending ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Send size={16} />
              Generate Recommendation
            </>
          )}
        </button>

        {generateMutation.isError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">Error</p>
              <p className="text-sm text-red-600">
                {generateMutation.error instanceof Error
                  ? generateMutation.error.message
                  : 'Failed to generate recommendation'}
              </p>
            </div>
          </div>
        )}

        {generatedRec && (
          <div className="mt-6 p-4 bg-[#E8F5E9] border border-[#556B2F] rounded-md">
            <div className="flex items-start gap-2 mb-3">
              <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-semibold text-[#5D4037] mb-2">Generated Recommendation</h4>
                <div className="space-y-3 text-sm">
                  <div>
                    <p className="font-medium text-[#556B2F] mb-1">Title:</p>
                    <p className="text-[#5D4037]">{generatedRec.title}</p>
                  </div>
                  <div>
                    <p className="font-medium text-[#556B2F] mb-1">Recommendation:</p>
                    <p className="text-[#5D4037]">{generatedRec.recommendation_text || generatedRec.description}</p>
                  </div>
                  {generatedRec.action_items && generatedRec.action_items.length > 0 && (
                    <div>
                      <p className="font-medium text-[#556B2F] mb-1">Action Items:</p>
                      <ul className="list-disc list-inside space-y-1 text-[#5D4037]">
                        {generatedRec.action_items.map((item: string, idx: number) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {generatedRec.expected_impact && (
                    <div>
                      <p className="font-medium text-[#556B2F] mb-1">Expected Impact:</p>
                      <p className="text-[#5D4037]">{generatedRec.expected_impact}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button
                onClick={handleReset}
                className="px-3 py-1.5 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              >
                Generate Another
              </button>
              {generatedRec?.id && (
                <CustomRecommendationActions recommendationId={generatedRec.id} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function CustomRecommendationActions({ recommendationId }: { recommendationId: string }) {
  const queryClient = useQueryClient()

  const approveMutation = useMutation({
    mutationFn: () => approveRecommendation(recommendationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
      queryClient.invalidateQueries({ queryKey: ['all-recommendations'] })
      queryClient.invalidateQueries({ queryKey: ['approved-recommendations'] })
    },
    onError: (error) => {
      alert(`Failed to approve: ${error instanceof Error ? error.message : 'Unknown error'}`)
    },
  })

  const rejectMutation = useMutation({
    mutationFn: () => rejectRecommendation(recommendationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
      queryClient.invalidateQueries({ queryKey: ['all-recommendations'] })
    },
    onError: (error) => {
      alert(`Failed to reject: ${error instanceof Error ? error.message : 'Unknown error'}`)
    },
  })

  const flagMutation = useMutation({
    mutationFn: () => flagRecommendation(recommendationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
      queryClient.invalidateQueries({ queryKey: ['all-recommendations'] })
    },
    onError: (error) => {
      alert(`Failed to flag: ${error instanceof Error ? error.message : 'Unknown error'}`)
    },
  })

  return (
    <div className="flex gap-2">
      <button
        onClick={() => approveMutation.mutate()}
        disabled={approveMutation.isPending || rejectMutation.isPending || flagMutation.isPending}
        className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
      >
        <CheckCircle size={14} />
        Approve
      </button>
      <button
        onClick={() => rejectMutation.mutate()}
        disabled={approveMutation.isPending || rejectMutation.isPending || flagMutation.isPending}
        className="px-3 py-1.5 text-sm bg-orange-600 text-white rounded-md hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
      >
        <AlertCircle size={14} />
        Reject
      </button>
      <button
        onClick={() => flagMutation.mutate()}
        disabled={approveMutation.isPending || rejectMutation.isPending || flagMutation.isPending}
        className="px-3 py-1.5 text-sm bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
      >
        <Flag size={14} />
        Flag
      </button>
    </div>
  )
}


// Use environment variable for production, fallback to relative path for local dev (Vite proxy)
export const API_BASE_URL = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL.replace(/\/+$/, '')}/api` : '/api'

// Log API configuration in development or if VITE_API_URL is missing in production
if (import.meta.env.DEV || (import.meta.env.PROD && !import.meta.env.VITE_API_URL)) {
  console.log('🔧 API Configuration:', {
    VITE_API_URL: import.meta.env.VITE_API_URL || '(not set)',
    API_BASE_URL: API_BASE_URL,
    environment: import.meta.env.MODE,
    isProduction: import.meta.env.PROD
  })
  
  if (import.meta.env.PROD && !import.meta.env.VITE_API_URL) {
    console.warn('⚠️  VITE_API_URL is not set in production! API calls will fail.')
    console.warn('   Set VITE_API_URL in Vercel environment variables and redeploy.')
  }
}

// Helper function to get auth headers
function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('auth_token')
  const headers: HeadersInit = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export async function fetchUsers(skip: number = 0, limit: number = 50, includePersona: boolean = false) {
  const params = new URLSearchParams({
    skip: skip.toString(),
    limit: limit.toString(),
    include_persona: includePersona.toString()
  })
  const response = await fetch(`${API_BASE_URL}/users?${params}`)
  if (!response.ok) {
    throw new Error('Failed to fetch users')
  }
  return response.json()
}

export async function fetchUserDetail(userId: string, windowDays: number = 30, includeFeatures: boolean = false) {
  const params = new URLSearchParams({
    transaction_window: windowDays.toString(),
    include_features: includeFeatures.toString()
  })
  const response = await fetch(`${API_BASE_URL}/profile/${userId}?${params}`, {
    headers: getAuthHeaders()
  })
  if (!response.ok) {
    throw new Error('Failed to fetch user details')
  }
  return response.json()
}

export async function fetchStats() {
  const response = await fetch(`${API_BASE_URL}/stats`)
  if (!response.ok) {
    throw new Error('Failed to fetch stats')
  }
  return response.json()
}

// Insights API functions (using Lambda endpoints)
const INSIGHTS_API_BASE = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL.replace(/\/+$/, '')}/api/insights` : '/api/insights'

export async function fetchWeeklyRecap(userId: string, weekStart?: string) {
  const params = weekStart ? `?week_start=${weekStart}` : ''
  const response = await fetch(`${INSIGHTS_API_BASE}/${userId}/weekly-recap${params}`)
  if (!response.ok) {
    throw new Error('Failed to fetch weekly recap')
  }
  return response.json()
}

export async function fetchSpendingAnalysis(userId: string, months: number = 6) {
  const response = await fetch(`${INSIGHTS_API_BASE}/${userId}/spending-analysis?months=${months}`)
  if (!response.ok) {
    throw new Error('Failed to fetch spending analysis')
  }
  return response.json()
}

export async function fetchNetWorth(userId: string, period: string = 'month') {
  const response = await fetch(`${INSIGHTS_API_BASE}/${userId}/net-worth?period=${period}`)
  if (!response.ok) {
    throw new Error('Failed to fetch net worth')
  }
  return response.json()
}

// Evaluation metrics API
export async function fetchEvaluationMetrics(latencySampleSize?: number) {
  const params = latencySampleSize ? `?latency_sample_size=${latencySampleSize}` : ''
  const response = await fetch(`${API_BASE_URL}/evaluation/metrics${params}`)
  if (!response.ok) {
    throw new Error('Failed to fetch evaluation metrics')
  }
  return response.json()
}

export async function fetchSuggestedBudget(userId: string, month?: string, lookbackMonths: number = 6) {
  const params = new URLSearchParams({ lookback_months: lookbackMonths.toString() })
  if (month) params.append('month', month)
  const response = await fetch(`${INSIGHTS_API_BASE}/${userId}/suggested-budget?${params}`, {
    headers: getAuthHeaders()
  })
  if (!response.ok) {
    // Create error with status code for better handling
    const error: any = new Error('Failed to fetch suggested budget')
    error.status = response.status
    error.isConsentError = response.status === 403
    throw error
  }
  return response.json()
}

export async function fetchBudgetTracking(userId: string, month?: string) {
  const params = month ? `?month=${month}` : ''
  const response = await fetch(`${INSIGHTS_API_BASE}/${userId}/budget-tracking${params}`, {
    headers: getAuthHeaders()
  })
  if (!response.ok) {
    // Create error with status code for better handling
    const error: any = new Error('Failed to fetch budget tracking')
    error.status = response.status
    error.isConsentError = response.status === 403
    throw error
  }
  return response.json()
}

export async function generateRAGBudget(userId: string, month?: string) {
  const params = month ? `?month=${month}` : ''
  const response = await fetch(`${INSIGHTS_API_BASE}/${userId}/generate-budget${params}`, {
    method: 'POST',
  })
  if (!response.ok) {
    throw new Error('Failed to generate budget')
  }
  return response.json()
}

export async function fetchApprovedRecommendations(userId: string) {
  const response = await fetch(`${API_BASE_URL}/recommendations/${userId}/approved`)
  if (!response.ok) {
    throw new Error('Failed to fetch approved recommendations')
  }
  return response.json()
}

// Recommendations API
export async function fetchRecommendations(
  userId: string,
  windowDays: number = 180,
  numEducation: number = 5,
  numOffers: number = 3
) {
  const params = new URLSearchParams({
    window_days: windowDays.toString(),
    num_education: numEducation.toString(),
    num_offers: numOffers.toString(),
  })
  const response = await fetch(`${API_BASE_URL}/recommendations/${userId}?${params}`)
  if (!response.ok) {
    const errorText = await response.text()
    const error = new Error(`Failed to fetch recommendations: ${errorText}`)
    ;(error as any).response = { status: response.status }
    throw error
  }
  return response.json()
}

// Budget API
export async function fetchBudgetHistory(userId: string, months: number = 6) {
  const params = new URLSearchParams({ months: months.toString() })
  const response = await fetch(`${API_BASE_URL}/insights/${userId}/budget-history?${params}`)
  if (!response.ok) {
    throw new Error('Failed to fetch budget history')
  }
  return response.json()
}

// Net Worth API
export async function fetchNetWorthHistory(userId: string, period: string = 'month') {
  const params = new URLSearchParams({ period })
  const response = await fetch(`${INSIGHTS_API_BASE}/${userId}/net-worth-history?${params}`)
  if (!response.ok) {
    throw new Error('Failed to fetch net worth history')
  }
  return response.json()
}

// User Feedback API
export async function submitFeedback(
  userId: string,
  insightId: string,
  insightType: string,
  feedbackType: 'like' | 'dislike',
  metadata?: Record<string, any>
) {
  const response = await fetch(`${API_BASE_URL}/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      insight_id: insightId,
      insight_type: insightType,
      feedback_type: feedbackType,
      metadata: metadata || {},
    }),
  })
  if (!response.ok) {
    throw new Error('Failed to submit feedback')
  }
  return response.json()
}

// Consent API
export async function grantConsent(userId: string) {
  const response = await fetch(`${API_BASE_URL}/consent`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId }),
  })
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Failed to grant consent: ${errorText}`)
  }
  const data = await response.json()
  return data
}

export async function revokeConsent(userId: string) {
  const response = await fetch(`${API_BASE_URL}/consent/${userId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Failed to revoke consent: ${errorText}`)
  }
  const data = await response.json()
  return data
}

export async function getConsentStatus(userId: string) {
  const response = await fetch(`${API_BASE_URL}/consent/${userId}`)
  if (!response.ok) {
    throw new Error('Failed to get consent status')
  }
  return response.json()
}


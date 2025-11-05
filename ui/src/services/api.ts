const API_BASE_URL = '/api'

export async function fetchUsers() {
  const response = await fetch(`${API_BASE_URL}/users`)
  if (!response.ok) {
    throw new Error('Failed to fetch users')
  }
  return response.json()
}

export async function fetchUserDetail(userId: string, windowDays: number = 30) {
  const response = await fetch(`${API_BASE_URL}/profile/${userId}?transaction_window=${windowDays}`)
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
const INSIGHTS_API_BASE = '/api/insights'

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
  const response = await fetch(`${INSIGHTS_API_BASE}/${userId}/suggested-budget?${params}`)
  if (!response.ok) {
    throw new Error('Failed to fetch suggested budget')
  }
  return response.json()
}

export async function fetchBudgetTracking(userId: string, month?: string) {
  const params = month ? `?month=${month}` : ''
  const response = await fetch(`${INSIGHTS_API_BASE}/${userId}/budget-tracking${params}`)
  if (!response.ok) {
    throw new Error('Failed to fetch budget tracking')
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
  const response = await fetch(`${API_BASE_URL}/insights/${userId}/net-worth-history?${params}`)
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


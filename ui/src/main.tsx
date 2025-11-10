import React from 'react'
import * as ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Handle unhandled promise rejections to prevent console errors
window.addEventListener('unhandledrejection', (event) => {
  // Suppress browser extension errors
  const reason = event.reason?.message || event.reason?.toString() || ''
  
  // Suppress common browser extension errors
  if (
    reason.includes('message channel closed') ||
    reason.includes('listener indicated an asynchronous response') ||
    reason.includes('message channel closed before a response was received') ||
    reason.includes('No tab with id') ||
    reason.includes('Extension context invalidated') ||
    event.reason?.stack?.includes('background-redux') ||
    event.reason?.stack?.includes('chrome-extension://') ||
    event.reason?.stack?.includes('moz-extension://')
  ) {
    event.preventDefault()
    return
  }
  
  // Suppress 403 errors related to budget/consent (expected when users haven't consented)
  if (
    event.reason?.isConsentError === true ||
    event.reason?.status === 403 ||
    (reason.includes('Failed to fetch') && (reason.includes('budget') || reason.includes('suggested budget') || reason.includes('budget tracking')))
  ) {
    event.preventDefault()
    return
  }
  
  // Log other unhandled rejections for debugging
  console.error('Unhandled promise rejection:', event.reason)
})

// Suppress LastPass and other extension context menu errors
const originalError = console.error
console.error = (...args: any[]) => {
  const message = args.join(' ')
  // Filter out LastPass and extension-related errors
  if (
    message.includes('runtime.lastError') ||
    message.includes('Cannot create item with duplicate id') ||
    message.includes('LastPass') ||
    message.includes('chrome-extension://') ||
    message.includes('moz-extension://')
  ) {
    return // Suppress these errors
  }
  
  // Suppress 403 errors related to budget/consent (expected when users haven't consented)
  if (
    message.includes('Failed to load budget') ||
    message.includes('Failed to fetch suggested budget') ||
    message.includes('Failed to fetch budget tracking')
  ) {
    // Check if it's a 403 error by looking at the error object
    const errorArg = args.find(arg => arg && typeof arg === 'object' && (arg.status === 403 || arg.isConsentError === true))
    if (errorArg) {
      return // Suppress 403 consent errors
    }
  }
  
  originalError.apply(console, args)
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)


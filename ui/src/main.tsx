import React from 'react'
import * as ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Handle unhandled promise rejections to prevent console errors
window.addEventListener('unhandledrejection', (event) => {
  // Suppress browser extension errors
  const reason = event.reason?.message || event.reason?.toString() || ''
  const reasonLower = reason.toLowerCase()
  const stack = event.reason?.stack || ''
  const stackLower = stack.toLowerCase()
  
  // Suppress common browser extension errors
  if (
    reasonLower.includes('message channel closed') ||
    reasonLower.includes('listener indicated an asynchronous response') ||
    reasonLower.includes('message channel closed before a response was received') ||
    reasonLower.includes('no tab with id') ||
    reasonLower.includes('extension context invalidated') ||
    reasonLower.includes('runtime.lasterror') ||
    reasonLower.includes('cannot create item with duplicate id') ||
    reasonLower.includes('duplicate id') ||
    reasonLower.includes('lastpass') ||
    reasonLower.includes('lp-push-server') ||
    stackLower.includes('background-redux') ||
    stackLower.includes('chrome-extension://') ||
    stackLower.includes('moz-extension://') ||
    stackLower.includes('safari-extension://') ||
    stackLower.includes('extension://') ||
    (reasonLower.includes('websocket') && (reasonLower.includes('lastpass') || reasonLower.includes('lp-push-server')))
  ) {
    event.preventDefault()
    return
  }
  
  // Suppress 403 errors related to budget/consent (expected when users haven't consented)
  if (
    event.reason?.isConsentError === true ||
    event.reason?.status === 403 ||
    (reasonLower.includes('failed to fetch') && (reasonLower.includes('budget') || reasonLower.includes('suggested budget') || reasonLower.includes('budget tracking')))
  ) {
    event.preventDefault()
    return
  }
  
  // Log other unhandled rejections for debugging
  console.error('Unhandled promise rejection:', event.reason)
})

// Suppress LastPass and other extension context menu errors
const originalError = console.error
const originalWarn = console.warn

// Helper function to check if message should be suppressed
const shouldSuppressExtensionError = (message: string, args: any[]): boolean => {
  const lowerMessage = message.toLowerCase()
  
  // Check for runtime.lastError variations
  if (
    lowerMessage.includes('runtime.lasterror') ||
    lowerMessage.includes('unchecked runtime.lasterror') ||
    lowerMessage.includes('cannot create item with duplicate id') ||
    lowerMessage.includes('duplicate id')
  ) {
    return true
  }
  
  // Check for LastPass and password manager errors
  if (
    lowerMessage.includes('lastpass') ||
    lowerMessage.includes('lp-push-server') ||
    lowerMessage.includes('background-redux')
  ) {
    return true
  }
  
  // Check for context menu items (LastPass, password managers, form fillers)
  const contextMenuItems = [
    'add item', 'add password', 'add address', 'add payment card',
    'add other item', 'save all entered data', 'generate secure password',
    'separator', 'fill -', 'edit -', 'copy first name', 'copy last name',
    'copy address line', 'copy city', 'copy zip', 'copy postal code',
    'copy email address', 'copy phone number'
  ]
  if (contextMenuItems.some(item => lowerMessage.includes(item))) {
    return true
  }
  
  // Check for extension URLs
  if (
    lowerMessage.includes('chrome-extension://') ||
    lowerMessage.includes('moz-extension://') ||
    lowerMessage.includes('safari-extension://') ||
    lowerMessage.includes('extension://')
  ) {
    return true
  }
  
  // Check for WebSocket errors from extensions
  if (
    lowerMessage.includes('websocket') &&
    (lowerMessage.includes('lastpass') || lowerMessage.includes('lp-push-server'))
  ) {
    return true
  }
  
  // Check error objects for extension-related content
  const hasExtensionError = args.some(arg => {
    if (arg && typeof arg === 'object') {
      const argStr = JSON.stringify(arg).toLowerCase()
      return argStr.includes('runtime.lasterror') || 
             argStr.includes('duplicate id') ||
             argStr.includes('lastpass') ||
             argStr.includes('chrome-extension') ||
             (arg.message && (
               arg.message.toLowerCase().includes('runtime.lasterror') || 
               arg.message.toLowerCase().includes('duplicate id') ||
               arg.message.toLowerCase().includes('lastpass')
             ))
    }
    return false
  })
  if (hasExtensionError) {
    return true
  }
  
  return false
}

console.error = (...args: any[]) => {
  const message = args.join(' ')
  
  // Suppress browser extension errors
  if (shouldSuppressExtensionError(message, args)) {
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

// Also suppress warnings from browser extensions
console.warn = (...args: any[]) => {
  const message = args.join(' ')
  
  // Suppress browser extension warnings
  if (shouldSuppressExtensionError(message, args)) {
    return // Suppress these warnings
  }
  
  originalWarn.apply(console, args)
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)


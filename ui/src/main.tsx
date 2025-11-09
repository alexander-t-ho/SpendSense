import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

<<<<<<< HEAD
// Handle unhandled promise rejections to prevent console errors
window.addEventListener('unhandledrejection', (event) => {
  // Suppress browser extension errors
  if (event.reason?.message?.includes('message channel closed')) {
    event.preventDefault()
    return
  }
  // Log other unhandled rejections for debugging
  console.error('Unhandled promise rejection:', event.reason)
})

=======
>>>>>>> 8fa267a461e5ea19895459dde8fa79dd393d6af3
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)


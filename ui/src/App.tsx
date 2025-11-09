import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from './components/AuthContext'
import UserDetail from './pages/UserDetail'
import UserDashboard from './pages/user/UserDashboard'
import OperatorDashboard from './pages/operator/OperatorDashboard'
import PreviewPage from './pages/PreviewPage'
import LandingPage from './pages/LandingPage'
import Login from './pages/Login'
import AccountTransactions from './pages/AccountTransactions'
import Layout from './components/Layout'

const queryClient = new QueryClient()

// Protected Route component
function ProtectedRoute({ children, requireAdmin = false }: { children: React.ReactNode, requireAdmin?: boolean }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (requireAdmin && !user.is_admin) {
    return <Navigate to="/my-dashboard" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  const { user } = useAuth()

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={
        user ? (
          user.is_admin ? (
            <Navigate to="/operator" replace />
          ) : (
            <Navigate to="/my-dashboard" replace />
          )
        ) : (
          <Login />
        )
      } />
      <Route path="/landing" element={<LandingPage />} />
      
      {/* Preview/Home page with account banners - no Layout wrapper */}
      <Route path="/preview" element={<PreviewPage />} />
      <Route path="/home" element={<PreviewPage />} />
      
      {/* Protected user routes */}
      <Route 
        path="/my-dashboard/:userId" 
        element={
          <ProtectedRoute>
            <UserDashboard />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/my-dashboard" 
        element={
          <ProtectedRoute>
            {user ? <Navigate to={`/my-dashboard/${user.id}`} replace /> : <Navigate to="/login" replace />}
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/account/:userId/:accountId/transactions" 
        element={
          <ProtectedRoute>
            <AccountTransactions />
          </ProtectedRoute>
        } 
      />
      
      {/* Protected admin routes */}
      <Route 
        path="/operator" 
        element={
          <ProtectedRoute requireAdmin>
            <Layout><OperatorDashboard /></Layout>
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/user/:userId" 
        element={
          <ProtectedRoute requireAdmin>
            <UserDetail />
          </ProtectedRoute>
        } 
      />
      
      {/* Root route - redirect based on auth */}
      <Route 
        path="/" 
        element={
          user ? (
            user.is_admin ? (
              <Navigate to="/operator" replace />
            ) : (
              <Navigate to="/my-dashboard" replace />
            )
          ) : (
            <LandingPage />
          )
        } 
      />
    </Routes>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <AppRoutes />
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App


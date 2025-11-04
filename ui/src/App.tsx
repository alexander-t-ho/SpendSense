import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from './pages/Dashboard'
import UserDetail from './pages/UserDetail'
import UserDashboard from './pages/user/UserDashboard'
import OperatorDashboard from './pages/operator/OperatorDashboard'
import Layout from './components/Layout'

const queryClient = new QueryClient()

function App() {
  // TODO: Add authentication/role-based routing
  // For now, we'll use route-based access
  // In production, this would check user role from auth context
  
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Layout>
          <Routes>
            {/* Admin/Operator routes - can see all users */}
            <Route path="/" element={<Dashboard />} />
            <Route path="/operator" element={<OperatorDashboard />} />
            <Route path="/user/:userId" element={<UserDetail />} />
            
            {/* End-user routes - restricted to own account */}
            <Route path="/my-dashboard/:userId" element={<UserDashboard />} />
            {/* TODO: Add route for user's own dashboard without userId param after auth is implemented */}
            {/* <Route path="/my-dashboard" element={<UserDashboard />} /> */}
          </Routes>
        </Layout>
      </Router>
    </QueryClientProvider>
  )
}

export default App


import { useParams } from 'react-router-dom'
import LeaflyLandingPage from '../../components/ui/fin-tech-landing-page'

/**
 * User Dashboard - End-user view
 * Uses the preview format (LeaflyLandingPage) with account banners and monthly spending
 * User can only see their own account data
 */
export default function UserDashboard() {
  const { userId } = useParams<{ userId: string }>()

  return <LeaflyLandingPage userId={userId} />
}

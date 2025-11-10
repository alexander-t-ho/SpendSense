import LeaflyLandingPage from "../../components/ui/fin-tech-landing-page";
import { useAuth } from "../../components/AuthContext";
import { useParams } from "react-router-dom";

/**
 * User Dashboard - Preview-style dashboard for authenticated users
 * This is the new default dashboard (without monthly spending card)
 */
export default function UserDashboardPage() {
  const { user } = useAuth();
  const { userId } = useParams<{ userId?: string }>();
  
  // Use userId from route params if available, otherwise use authenticated user's ID
  const targetUserId = userId || user?.id;
  
  // Hide monthly spending card for the user dashboard
  return <LeaflyLandingPage userId={targetUserId} hideMonthlySpending={true} />;
}


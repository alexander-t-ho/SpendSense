import { useParams } from 'react-router-dom'
import AdminLandingPage from '../components/ui/admin-landing-page'

export default function UserDetail() {
  const { userId } = useParams<{ userId: string }>()

  if (!userId) {
    return (
      <div className="text-center py-12">
        <p className="text-[#8B6F47]">User ID is required</p>
      </div>
    )
  }

  return <AdminLandingPage userId={userId} />
}

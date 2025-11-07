import { useState, useMemo } from 'react'
import { Search, X } from 'lucide-react'

interface User {
  id: string
  name: string
  email: string
}

interface UserSearchProps {
  users: User[]
  selectedUserId: string
  onSelectUser: (userId: string) => void
  placeholder?: string
  className?: string
}

/**
 * Reusable user search component with searchable dropdown
 * Supports filtering users by name or email
 */
export default function UserSearch({
  users,
  selectedUserId,
  onSelectUser,
  placeholder = 'Search for a user...',
  className = '',
}: UserSearchProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [isOpen, setIsOpen] = useState(false)

  const filteredUsers = useMemo(() => {
    if (!searchQuery.trim()) {
      return users
    }
    const query = searchQuery.toLowerCase()
    return users.filter(
      (user) =>
        user.name.toLowerCase().includes(query) ||
        user.email.toLowerCase().includes(query)
    )
  }, [users, searchQuery])

  const selectedUser = users.find((u) => u.id === selectedUserId)

  const handleSelectUser = (userId: string) => {
    onSelectUser(userId)
    setIsOpen(false)
    setSearchQuery('')
  }

  const handleClear = () => {
    onSelectUser('')
    setSearchQuery('')
    setIsOpen(false)
  }

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery || selectedUser?.name || ''}
            onChange={(e) => {
              setSearchQuery(e.target.value)
              setIsOpen(true)
            }}
            onFocus={() => setIsOpen(true)}
            placeholder={selectedUser ? selectedUser.name : placeholder}
            className="w-full pl-10 pr-10 py-2 border border-[#D4C4B0] rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-[#556B2F]"
          />
          {selectedUserId && (
            <button
              onClick={handleClear}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-[#556B2F]"
              type="button"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {isOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />
            <div className="absolute z-20 mt-1 w-full bg-white border border-[#D4C4B0] rounded-md shadow-lg max-h-60 overflow-auto">
              {filteredUsers.length === 0 ? (
                <div className="px-4 py-3 text-sm text-[#8B6F47] text-center">
                  No users found
                </div>
              ) : (
                <ul className="py-1">
                  {filteredUsers.map((user) => (
                    <li
                      key={user.id}
                      onClick={() => handleSelectUser(user.id)}
                      className={`px-4 py-2 cursor-pointer hover:bg-blue-50 ${
                        selectedUserId === user.id ? 'bg-[#E8F5E9]' : ''
                      }`}
                    >
                      <div className="text-sm font-medium text-[#5D4037]">
                        {user.name}
                      </div>
                      <div className="text-xs text-[#8B6F47]">{user.email}</div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        )}
      </div>
      {selectedUser && (
        <div className="mt-1 text-xs text-[#8B6F47]">
          Selected: {selectedUser.name} ({selectedUser.email})
        </div>
      )}
    </div>
  )
}


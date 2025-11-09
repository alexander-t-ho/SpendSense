import { X, CheckCircle, XCircle, Eye, EyeOff, Info } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface ConsentInfoModalProps {
  isOpen: boolean
  onClose: () => void
  userName?: string
}

export default function ConsentInfoModal({ isOpen, onClose, userName }: ConsentInfoModalProps) {
  if (!isOpen) return null

  const visibleItems = [
    { icon: <CheckCircle className="h-5 w-5 text-green-600" />, text: "Basic account information (name, email)" },
    { icon: <CheckCircle className="h-5 w-5 text-green-600" />, text: "Account balances and account types" },
    { icon: <CheckCircle className="h-5 w-5 text-green-600" />, text: "Account metadata (account names, IDs)" },
    { icon: <CheckCircle className="h-5 w-5 text-green-600" />, text: "Liabilities (loans, credit cards) - basic info" },
  ]

  const hiddenItems = [
    { icon: <XCircle className="h-5 w-5 text-red-600" />, text: "Transaction history and details" },
    { icon: <XCircle className="h-5 w-5 text-red-600" />, text: "Personalized financial recommendations" },
    { icon: <XCircle className="h-5 w-5 text-red-600" />, text: "Spending patterns and analysis" },
    { icon: <XCircle className="h-5 w-5 text-red-600" />, text: "Income analysis and payroll detection" },
    { icon: <XCircle className="h-5 w-5 text-red-600" />, text: "Budget calculations and tracking" },
    { icon: <XCircle className="h-5 w-5 text-red-600" />, text: "Subscription detection and recurring payments" },
    { icon: <XCircle className="h-5 w-5 text-red-600" />, text: "Persona analysis and risk assessment" },
    { icon: <XCircle className="h-5 w-5 text-red-600" />, text: "Financial insights and trends" },
  ]

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
          >
            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="bg-gradient-to-r from-[#5D4037] to-[#8B6F47] px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/20 rounded-lg">
                    <Info className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-white">
                      Data Visibility Information
                    </h2>
                    {userName && (
                      <p className="text-sm text-white/80 mt-0.5">
                        {userName} has not granted consent
                      </p>
                    )}
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <X className="h-5 w-5 text-white" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Info Box */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-900">
                    <strong>Note:</strong> When a user has not consented to data processing, 
                    only basic account information is visible. Transaction-level data and 
                    personalized insights require explicit user consent.
                  </p>
                </div>

                {/* Visible Data Section */}
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <Eye className="h-5 w-5 text-green-600" />
                    <h3 className="text-lg font-semibold text-[#5D4037]">
                      What You Can See
                    </h3>
                  </div>
                  <div className="space-y-3">
                    {visibleItems.map((item, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="flex items-start gap-3 p-3 bg-green-50 rounded-lg border border-green-200"
                      >
                        {item.icon}
                        <span className="text-sm text-gray-700 flex-1">{item.text}</span>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* Hidden Data Section */}
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <EyeOff className="h-5 w-5 text-red-600" />
                    <h3 className="text-lg font-semibold text-[#5D4037]">
                      What You Cannot See
                    </h3>
                  </div>
                  <div className="space-y-3">
                    {hiddenItems.map((item, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: (visibleItems.length + index) * 0.05 }}
                        className="flex items-start gap-3 p-3 bg-red-50 rounded-lg border border-red-200"
                      >
                        {item.icon}
                        <span className="text-sm text-gray-700 flex-1">{item.text}</span>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* Footer Note */}
                <div className="bg-[#F5E6D3] border border-[#D4C4B0] rounded-lg p-4">
                  <p className="text-sm text-[#5D4037]">
                    <strong>Privacy Protection:</strong> This user must grant consent from their 
                    own account dashboard to enable full data access and personalized recommendations. 
                    Admins cannot grant consent on behalf of users.
                  </p>
                </div>
              </div>

              {/* Footer */}
              <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
                <button
                  onClick={onClose}
                  className="w-full px-4 py-2 bg-[#5D4037] text-white rounded-lg hover:bg-[#8B6F47] transition-colors font-medium"
                >
                  Understood
                </button>
              </div>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}


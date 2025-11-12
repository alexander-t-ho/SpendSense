import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Leaf, CreditCard, Wallet, Building2, Settings, CheckCircle, XCircle, Info } from "lucide-react";
import { fetchUserDetail, getConsentStatus, API_BASE_URL } from "../../services/api";
import FinancialInsightsCarousel from "../FinancialInsightsCarousel";
import RecommendationsSection from "../RecommendationsSection";
import CreditCardBrandLogo, { detectCreditCardBrand } from "../CreditCardBrandLogo";
import PersonaPieChart from "../PersonaPieChart";
import CustomRecommendationGenerator from "../admin/CustomRecommendationGenerator";
import ConsentInfoModal from "../admin/ConsentInfoModal";

// Planet component for green account cards
function Planet() {
  return (
    <motion.svg
      initial={{ rotate: -8 }}
      animate={{ rotate: 0 }}
      transition={{ duration: 2, type: "spring" }}
      width="220"
      height="220"
      viewBox="0 0 220 220"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#556B2F" />
          <stop offset="100%" stopColor="#F5E6D3" />
        </linearGradient>
      </defs>
      <circle cx="110" cy="110" r="56" fill="url(#grad)" opacity="0.95" />
      <circle cx="94" cy="98" r="10" fill="white" opacity="0.45" />
      <circle cx="132" cy="126" r="8" fill="white" opacity="0.35" />
      <motion.ellipse
        cx="110" cy="110" rx="100" ry="34" stroke="white" strokeOpacity="0.6" fill="none"
        animate={{ strokeDashoffset: [200, 0] }} transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }} strokeDasharray="200 200"
      />
      <motion.circle cx="210" cy="110" r="4" fill="white" animate={{ opacity: [0.2, 1, 0.2] }} transition={{ duration: 2.2, repeat: Infinity }} />
    </motion.svg>
  );
}

// Reuse AccountCard component from fin-tech-landing-page
function AccountCard({ account, index, userId }: { account: any; index: number; userId: string }) {
  const navigate = useNavigate();

  const getAccountIcon = (type: string, subtype: string) => {
    if (type === "credit") {
      return <CreditCard className="h-4 w-4" />;
    } else if (type === "depository") {
      if (subtype === "checking") {
        return <Wallet className="h-4 w-4" />;
      }
      return <Building2 className="h-4 w-4" />;
    }
    return <Wallet className="h-4 w-4" />;
  };

  const formatBalance = (amount: number | null | undefined) => {
    if (amount === null || amount === undefined) return "$0.00";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const getAccountTypeLabel = (type: string, subtype: string) => {
    if (type === "credit") {
      return "Credit Card";
    } else if (type === "depository") {
      return subtype ? subtype.charAt(0).toUpperCase() + subtype.slice(1) : "Account";
    }
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  const maskAccountId = (accountId: string): string => {
    // Mask all but last 4 digits
    if (!accountId || accountId.length < 4) return accountId;
    const last4 = accountId.slice(-4);
    return `*******${last4}`;
  };

  // Check if account should show masked account number (not mortgages or student loans)
  const shouldShowAccountNumber = !(account.type === 'loan' && (account.subtype === 'mortgage' || account.subtype === 'student' || account.subtype === 'student_loan'));

  // Determine card style based on account type
  // Savings and Checking: green to white
  // Credit cards: brown to beige
  // Student loans and mortgages: dark forest green to grey
  const getCardStyle = () => {
    if (account.type === 'depository' && (account.subtype === 'savings' || account.subtype === 'checking')) {
      return 'green-to-white'
    }
    if (account.type === 'credit') {
      return 'brown-to-beige'
    }
    if (account.type === 'loan' && (account.subtype === 'student' || account.subtype === 'student_loan' || account.subtype === 'mortgage')) {
      return 'forest-green-to-grey'
    }
    // Default for other depository accounts
    if (account.type === 'depository') {
      return 'green-to-white'
    }
    // Default for other loan types
    return 'forest-green-to-grey'
  }
  
  const cardStyle = getCardStyle()
  const isGreenCard = cardStyle === 'green-to-white'

  const handleClick = () => {
    navigate(`/account/${userId}/${account.id}/transactions`);
  };

  // Calculate credit utilization for credit cards
  const creditUtilization = account.type === "credit" && account.limit && account.current
    ? ((Math.abs(account.current) / account.limit) * 100).toFixed(1)
    : null;

  // Detect credit card brand for credit cards
  const cardBrand = account.type === "credit" ? detectCreditCardBrand(account.name, account.account_id) : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 + index * 0.1 }}
      onClick={handleClick}
      className={`relative col-span-1 overflow-hidden rounded-3xl p-3 text-white shadow-lg cursor-pointer hover:scale-[1.02] transition-transform w-[300px] h-[200px] flex flex-col ${
        cardStyle === 'green-to-white'
          ? "bg-gradient-to-b from-[#556B2F] to-white" 
          : cardStyle === 'brown-to-beige'
          ? "bg-gradient-to-b from-[#5D4037] to-[#D4C4B0]"
          : "bg-gradient-to-b from-[#2D5016] to-[#808080]"
      }`}
    >
      {cardStyle !== 'green-to-white' && (
        <div className="absolute inset-0">
          <svg className="absolute inset-0 h-full w-full opacity-30" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <radialGradient id={`rg-account-${account.id}`} cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor={cardStyle === 'brown-to-beige' ? "#5D4037" : "#2D5016"} stopOpacity="0.35" />
                <stop offset="100%" stopColor="transparent" />
              </radialGradient>
            </defs>
            <rect width="400" height="400" fill={`url(#rg-account-${account.id})`} />
            {[...Array(12)].map((_, i) => (
              <circle key={i} cx="200" cy="200" r={20 + i * 14} fill="none" stroke="currentColor" strokeOpacity="0.12" />
            ))}
          </svg>
        </div>
      )}
      {isGreenCard && (
        <div className="pointer-events-none absolute -right-8 -top-10 opacity-70">
          <Planet />
        </div>
      )}
      <div className="relative flex h-full flex-col justify-between">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {account.type !== "credit" && (
            <div className={`rounded-full p-1 ring-1 ring-white/10 ${
              isGreenCard ? "bg-white/20" : "bg-[#556B2F]/60"
            }`}>
              {getAccountIcon(account.type, account.subtype)}
            </div>
            )}
            <div className="flex flex-col">
            <span className={`text-xs uppercase tracking-wider ${
              isGreenCard ? "text-white/90" : "text-[#F5E6D3]"
            }`}>
              {getAccountTypeLabel(account.type, account.subtype).toUpperCase()}
            </span>
              {shouldShowAccountNumber && account.account_id && (
                <span className={`text-xs font-mono tracking-wider mt-0.5 ${
                  isGreenCard ? "text-white/70" : "text-white/70"
                }`}>
                  {maskAccountId(account.account_id)}
                </span>
              )}
            </div>
          </div>
        </div>
        <div className={`mt-auto mb-2 ${
          isGreenCard ? "text-white/90" : "text-white/95"
        }`}>
          <h3 className={`text-sm font-semibold mb-1 ${
            isGreenCard ? "text-white" : "text-white"
        }`}>
          {account.name || "Unnamed Account"}
          </h3>
          <div className={`text-base font-bold ${
            isGreenCard ? "text-white" : "text-white"
          }`}>
          {account.type === "credit" 
            ? formatBalance(account.current ? Math.abs(account.current) : 0)
            : formatBalance(account.available ?? account.current ?? 0)
          }
        </div>
        </div>
        <div className="flex flex-col items-start mt-auto space-y-1 relative">
          {account.type === "credit" && creditUtilization && (
            <div className={`text-xs ${
              isGreenCard ? "text-white/80" : "text-white/80"
            }`}>
              {creditUtilization}% utilized
            </div>
          )}
          {account.type === "credit" && (account.liability?.next_payment_due_date || account.next_payment_due_date) && (
            <div className={`text-xs ${
              isGreenCard ? "text-white/80" : "text-white/80"
            }`}>
              Next Payment: {new Date(account.liability?.next_payment_due_date || account.next_payment_due_date!).toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric',
                year: 'numeric'
              })}
            </div>
          )}
          <div className="flex items-center justify-between w-full">
            {account.type === "credit" && account.limit && (
              <div className={`text-xs ${
                isGreenCard ? "text-white/80" : "text-white/80"
              }`}>
                Limit: {formatBalance(account.limit)}
              </div>
            )}
          </div>
          {account.type === "credit" && cardBrand && (
            <div className="absolute bottom-0 right-0">
              <CreditCardBrandLogo brand={cardBrand} />
            </div>
          )}
        </div>
        {cardStyle !== 'green-to-white' && (
          <motion.div
            className={`absolute right-3 top-3 h-8 w-8 rounded-full ${
              cardStyle === 'brown-to-beige' ? 'bg-[#5D4037]/40' : 'bg-[#2D5016]/40'
            }`}
            animate={{ boxShadow: [
              `0 0 0 0 ${cardStyle === 'brown-to-beige' ? 'rgba(93,64,55,0.35)' : 'rgba(45,80,22,0.35)'}`, 
              `0 0 0 12px ${cardStyle === 'brown-to-beige' ? 'rgba(93,64,55,0)' : 'rgba(45,80,22,0)'}`
            ] }}
            transition={{ duration: 2.5, repeat: Infinity }}
          />
        )}
      </div>
    </motion.div>
  );
}

interface AdminLandingPageProps {
  userId: string;
}

export default function AdminLandingPage({ userId }: AdminLandingPageProps) {
  const navigate = useNavigate();
  const [user, setUser] = useState<any>(null);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'insights' | 'recommendations'>('overview');
  const [windowDays] = useState<number>(30);
  const [showConsentInfoModal, setShowConsentInfoModal] = useState(false);

  const { data: consent } = useQuery({
    queryKey: ['consent', userId],
    queryFn: () => getConsentStatus(userId),
    enabled: !!userId,
  });

  useEffect(() => {
    const loadUser = async () => {
      try {
        setLoading(true);
        const userDetail = await fetchUserDetail(userId, 30);
        setUser({ id: userId, ...userDetail });
        setAccounts(userDetail.accounts || []);
      } catch (error) {
        console.error("Failed to load user:", error);
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      loadUser();
    }
  }, [userId]);

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'LOW':
        return 'bg-[#E8F5E9] text-[#5D4037] border-blue-300'
      case 'MINIMAL':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'VERY_LOW':
        return 'bg-[#F5E6D3] text-[#5D4037] border-[#D4C4B0]'
      default:
        return 'bg-[#F5E6D3] text-[#5D4037] border-[#D4C4B0]'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-[#F5E6D3] via-[#D4C4B0] to-[#5D4037] flex items-center justify-center">
        <div className="text-[#8B6F47]">Loading user data...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-[#F5E6D3] via-[#D4C4B0] to-[#5D4037] flex items-center justify-center">
        <div className="text-[#8B6F47]">User not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-[#F5E6D3] via-[#D4C4B0] to-[#5D4037]">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        :root { --font-sans: 'Plus Jakarta Sans', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif; }
        .font-jakarta { font-family: var(--font-sans); }
      `}</style>

      {/* Top nav */}
      <nav className="mx-auto flex w-full max-w-[1180px] items-center justify-between px-4 py-6 md:px-0">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#556B2F] text-white shadow">
            <Leaf className="h-5 w-5" />
          </div>
          <span className="font-jakarta text-xl font-semibold tracking-tight text-[#5D4037]">Leafly</span>
        </div>
        <div className="hidden items-center gap-8 md:flex">
          <button
            onClick={() => setActiveTab('overview')}
            className={`text-sm transition-colors ${
              activeTab === 'overview' 
                ? 'text-[#5D4037] font-semibold border-b-2 border-[#556B2F] pb-1' 
                : 'text-[#8B6F47] hover:text-[#5D4037]'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('insights')}
            className={`text-sm transition-colors ${
              activeTab === 'insights' 
                ? 'text-[#5D4037] font-semibold border-b-2 border-[#556B2F] pb-1' 
                : 'text-[#8B6F47] hover:text-[#5D4037]'
            }`}
          >
            Financial Insights
          </button>
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`text-sm transition-colors ${
              activeTab === 'recommendations' 
                ? 'text-[#5D4037] font-semibold border-b-2 border-[#556B2F] pb-1' 
                : 'text-[#8B6F47] hover:text-[#5D4037]'
            }`}
          >
            Recommendations
          </button>
        </div>
        <div className="hidden gap-2 md:flex">
          <button 
            onClick={() => navigate('/operator')}
            className="flex items-center gap-2 rounded-full px-4 py-2 text-sm text-[#5D4037] hover:bg-white/50"
          >
            <Settings className="h-4 w-4" />
            Back to Dashboard
          </button>
        </div>
      </nav>

      {/* Main Content Area */}
      {activeTab === 'overview' ? (
        <div className="mx-auto w-full max-w-[1180px] px-4 pb-14 md:px-0">
          {/* Single column layout */}
          <div className="flex flex-col justify-start space-y-6">
            <div>
              <h1 className="text-5xl md:text-6xl font-semibold leading-[1.05] tracking-tight text-[#5D4037] mb-2">
                {user.name}
              </h1>
              <p className="text-lg text-[#8B6F47] mb-4">{user.email}</p>
              
              {/* Consent Status Badge */}
              <div className="flex items-center gap-2 mb-6">
                {consent?.consented ? (
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-green-100 text-green-800 rounded-full border border-green-300">
                    <CheckCircle size={16} />
                    <span className="text-sm font-medium">Consented</span>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowConsentInfoModal(true)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-red-100 text-red-800 rounded-full border border-red-300 hover:bg-red-200 transition-colors cursor-pointer group"
                    title="Click to see what data is visible"
                  >
                    <XCircle size={16} />
                    <span className="text-sm font-medium">Not Consented</span>
                    <Info size={14} className="opacity-60 group-hover:opacity-100 transition-opacity" />
                  </button>
                )}
              </div>
            </div>

            {/* Persona & Risk Analysis */}
            {user.persona && (
              <div className="bg-white shadow-lg rounded-3xl p-6 ring-1 ring-[#D4C4B0]">
                <h2 className="text-xl font-semibold text-[#5D4037] mb-4">Persona & Risk Analysis</h2>
                
                {/* Risk Summary */}
                <div className="mb-6 p-5 bg-gradient-to-r from-[#F5E6D3] to-white rounded-xl border border-[#D4C4B0]/50">
                  <div className="flex items-center justify-between flex-wrap gap-4">
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-[#5D4037] mb-2">Risk Assessment</h3>
                      <div className="space-y-2">
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-medium text-[#556B2F]">Total Risk Points:</span>
                          <span className="text-2xl font-bold text-[#5D4037]">{user.persona.total_risk_points?.toFixed(2) || '0.00'}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-medium text-[#556B2F]">Risk Level:</span>
                          <span className={`inline-flex items-center px-4 py-2 rounded-full text-base font-bold border-2 ${getRiskColor(user.persona.risk_level || 'VERY_LOW')}`}>
                            {user.persona.risk_level || 'VERY_LOW'} RISK
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Pie Chart */}
                {user.persona.all_matching_personas && user.persona.all_matching_personas.length > 0 ? (
                  <div className="mb-6 p-4 bg-gradient-to-r from-[#F5E6D3] to-white border border-[#D4C4B0]/50 rounded-xl">
                    <h3 className="text-lg font-semibold text-[#5D4037] mb-4">Persona Distribution</h3>
                    <PersonaPieChart 
                      personas={user.persona.all_matching_personas}
                    />
                  </div>
                ) : null}

                {/* Detailed Breakdown Table */}
                {user.persona.all_matching_personas && user.persona.all_matching_personas.length > 0 ? (
                  <div>
                    <h3 className="text-lg font-semibold text-[#5D4037] mb-4">Persona Breakdown & Criteria</h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 border border-[#D4C4B0] rounded-lg">
                        <thead className="bg-[#F5E6D3]">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-[#556B2F] uppercase tracking-wider">
                              Persona
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-[#556B2F] uppercase tracking-wider">
                              Matched Criteria
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-[#556B2F] uppercase tracking-wider">
                              Points/Criterion
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-[#556B2F] uppercase tracking-wider">
                              Total Points
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-[#556B2F] uppercase tracking-wider">
                              Contribution %
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {user.persona.all_matching_personas.map((persona: any, idx: number) => (
                            <tr key={idx} className="hover:bg-[#F5E6D3]/30">
                              <td className="px-4 py-4 whitespace-nowrap">
                                <div className="text-sm font-semibold text-[#5D4037]">{persona.persona_name}</div>
                              </td>
                              <td className="px-4 py-4">
                                <div className="text-sm text-[#5D4037] mb-2">
                                  <span className="font-semibold text-base">{persona.matched_criteria}/{persona.total_criteria}</span> criteria matched
                                </div>
                                {persona.matched_reasons && persona.matched_reasons.length > 0 && (
                                  <div className="mt-3 p-3 bg-gradient-to-r from-[#F5E6D3] to-white rounded-md border border-[#D4C4B0]/50">
                                    <p className="text-xs font-semibold text-[#5D4037] mb-2 uppercase tracking-wide">Criteria Details:</p>
                                    <ul className="space-y-2 text-xs text-[#8B6F47]">
                                      {persona.matched_reasons.map((reason: string, reasonIdx: number) => (
                                        <li key={reasonIdx} className="flex items-start">
                                          <span className="text-green-600 mr-2 mt-0.5 flex-shrink-0 font-bold">✓</span>
                                          <span className="flex-1">{reason}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </td>
                              <td className="px-4 py-4 whitespace-nowrap">
                                <div className="text-sm font-semibold text-[#5D4037]">{persona.points_per_criterion}</div>
                                <div className="text-xs text-[#8B6F47]">per criterion</div>
                              </td>
                              <td className="px-4 py-4 whitespace-nowrap">
                                <div className="text-sm font-bold text-[#5D4037]">{persona.total_points?.toFixed(2) || '0.00'}</div>
                                <div className="text-xs text-[#8B6F47]">total points</div>
                              </td>
                              <td className="px-4 py-4 whitespace-nowrap">
                                <div className="text-sm font-semibold text-[#5D4037]">{persona.percentage}%</div>
                                <div className="text-xs text-[#8B6F47]">of total risk</div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="text-[#8B6F47] text-center py-8">
                    No matching personas found
                  </div>
                )}
                
                {/* Rationale */}
                {user.persona.rationale && (
                  <div className="mt-6 p-3 bg-gradient-to-r from-[#F5E6D3] to-white border border-[#D4C4B0]/50 rounded-lg">
                    <label className="text-sm font-medium text-[#5D4037]">Analysis Rationale</label>
                    <p className="mt-1 text-sm text-[#8B6F47]">{user.persona.rationale}</p>
                  </div>
                )}
                
                {/* Generate Recommendations Button - Only show if consented */}
                {consent?.consented && (
                  <div className="mt-6 space-y-4">
                    <GenerateRecommendationsButton userId={userId} />
                  </div>
                )}
                
                {/* Custom Recommendation Generator */}
                <div className="mt-6 space-y-4">
                  <CustomRecommendationGenerator 
                    userId={userId}
                    contextData={user.persona?.all_matching_personas?.[0]?.matched_reasons?.[0] || undefined}
                    onRecommendationGenerated={() => {
                      // Recommendation generated successfully
                    }}
                  />
                </div>
              </div>
            )}

            {/* Income Analysis */}
            {user.income && (
              <div className="bg-white shadow-lg rounded-3xl p-6 ring-1 ring-[#D4C4B0]">
                <h2 className="text-xl font-semibold text-[#5D4037] mb-4">Income Analysis</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-gradient-to-r from-[#F5E6D3] to-white border border-[#D4C4B0]/50 rounded-lg">
                    <label className="text-sm font-medium text-[#8B6F47]">180-Day Income</label>
                    <p className="mt-1 text-2xl font-bold text-[#5D4037]">
                      ${user.income['180_day_total']?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                    </p>
                    <p className="text-xs text-[#8B6F47] mt-1">
                      {user.income.payroll_count_180d || 0} payroll transaction{user.income.payroll_count_180d !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <div className="p-4 bg-gradient-to-r from-[#F5E6D3] to-white border border-[#D4C4B0]/50 rounded-lg">
                    <label className="text-sm font-medium text-[#8B6F47]">Estimated Yearly Income</label>
                    <p className="mt-1 text-2xl font-bold text-green-600">
                      ${user.income.yearly_estimated?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                    </p>
                    <p className="text-xs text-[#8B6F47] mt-1">Based on 180-day average</p>
                  </div>
                  <div className="p-4 bg-gradient-to-r from-[#F5E6D3] to-white border border-[#D4C4B0]/50 rounded-lg">
                    <label className="text-sm font-medium text-[#8B6F47]">Monthly Average</label>
                    <p className="mt-1 text-2xl font-bold text-[#5D4037]">
                      ${((user.income.yearly_estimated || 0) / 12).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                    <p className="text-xs text-[#8B6F47] mt-1">Yearly income ÷ 12</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Account cards grid */}
            <div className="grid grid-cols-1 gap-y-[30px] gap-x-[30px] md:grid-cols-2 items-start mt-0">
              {loading ? (
                <>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="col-span-1 rounded-xl bg-white p-6 text-[#5D4037] shadow-lg ring-1 ring-[#D4C4B0]"
                  >
                    <div className="flex items-center justify-center h-48">
                      <div className="text-sm text-[#8B6F47]">Loading accounts...</div>
                    </div>
                  </motion.div>
                  <div className="hidden md:block" />
                </>
              ) : accounts.length === 0 ? (
                <>
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="col-span-1 rounded-xl bg-white p-6 text-[#5D4037] shadow-lg ring-1 ring-[#D4C4B0]"
                  >
                    <div className="flex items-center justify-center h-48">
                      <div className="text-sm text-[#8B6F47]">No accounts found</div>
                    </div>
                  </motion.div>
                  <div className="hidden md:block" />
                </>
              ) : (
                accounts.map((account: any, index: number) => (
                  <AccountCard key={account.id} account={account} index={index} userId={userId} />
                ))
              )}
            </div>
          </div>
        </div>
      ) : activeTab === 'insights' ? (
        <div className="mx-auto w-full max-w-[1180px] px-4 pb-14 md:px-0">
          {user && user.id ? (
            <div className="mt-8">
              <h2 className="text-3xl font-bold text-[#5D4037] mb-6">Financial Insights</h2>
              <FinancialInsightsCarousel userId={user.id} isAdmin={true} />
            </div>
          ) : (
            <div className="mt-8 text-center py-12">
              <div className="text-[#8B6F47]">Loading financial insights...</div>
            </div>
          )}
        </div>
      ) : activeTab === 'recommendations' ? (
        <div className="mx-auto w-full max-w-[1180px] px-4 pb-14 md:px-0">
          {user && user.id ? (
            <div className="mt-8">
              <h2 className="text-3xl font-bold text-[#5D4037] mb-6">Recommendations</h2>
              <RecommendationsSection userId={user.id} windowDays={windowDays} readOnly={true} />
            </div>
          ) : (
            <div className="mt-8 text-center py-12">
              <div className="text-[#8B6F47]">Loading recommendations...</div>
            </div>
          )}
        </div>
      ) : null}

      <footer className="mx-auto w-full max-w-[1180px] px-4 pb-10 text-center text-xs text-[#8B6F47]/70 md:px-0">
        © {new Date().getFullYear()} Leafly, Inc. All rights reserved.
      </footer>

      {/* Consent Info Modal */}
      <ConsentInfoModal
        isOpen={showConsentInfoModal}
        onClose={() => setShowConsentInfoModal(false)}
        userName={user?.name}
      />
    </div>
  );
}

function GenerateRecommendationsButton({ userId }: { userId: string }) {
  const queryClient = useQueryClient()
  const [generatedRecommendations, setGeneratedRecommendations] = useState<any[] | null>(null)

  // API_BASE_URL is imported from services/api

  const generateMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${API_BASE_URL}/recommendations/generate/${userId}?num_recommendations=8`, {
        method: 'POST',
      })
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to generate recommendations' }))
        const error = new Error(errorData.detail || 'Failed to generate recommendations')
        ;(error as any).response = response
        throw error
      }
      return response.json()
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
      // Store generated recommendations to display below
      setGeneratedRecommendations(data.recommendations || [])
    },
    onError: async (error) => {
      let errorMessage = 'Failed to generate recommendations'
      try {
        const errorData = await (error as any).response?.json()
        errorMessage = errorData?.detail || errorMessage
      } catch {
        errorMessage = (error as Error).message || errorMessage
      }
      alert(`Error generating recommendations: ${errorMessage}`)
      setGeneratedRecommendations(null)
    },
  })

  const approveMutation = useMutation({
    mutationFn: async (recommendationId: string) => {
      const response = await fetch(`${API_BASE_URL}/operator/recommendations/${recommendationId}/approve`, {
        method: 'PUT',
      })
      if (!response.ok) {
        throw new Error('Failed to approve recommendation')
      }
      return response.json()
    },
    onSuccess: (_, recommendationId) => {
      // Update the recommendation status in local state
      setGeneratedRecommendations((prev) =>
        prev?.map((rec) =>
          rec.id === recommendationId
            ? { ...rec, approved: true, rejected: false, flagged: false, status: 'approved' }
            : rec
        ) || null
      )
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
      queryClient.invalidateQueries({ queryKey: ['approved-recommendations'] })
      queryClient.invalidateQueries({ queryKey: ['all-recommendations'] })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: async (recommendationId: string) => {
      const response = await fetch(`${API_BASE_URL}/operator/recommendations/${recommendationId}/reject`, {
        method: 'PUT',
      })
      if (!response.ok) {
        throw new Error('Failed to reject recommendation')
      }
      return response.json()
    },
    onSuccess: (_, recommendationId) => {
      // Update the recommendation status in local state
      setGeneratedRecommendations((prev) =>
        prev?.map((rec) =>
          rec.id === recommendationId
            ? { ...rec, approved: false, rejected: true, flagged: false, status: 'rejected' }
            : rec
        ) || null
      )
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  const flagMutation = useMutation({
    mutationFn: async (recommendationId: string) => {
      const response = await fetch(`${API_BASE_URL}/operator/recommendations/${recommendationId}/flag`, {
        method: 'PUT',
      })
      if (!response.ok) {
        throw new Error('Failed to flag recommendation')
      }
      return response.json()
    },
    onSuccess: (_, recommendationId) => {
      // Update the recommendation status in local state
      setGeneratedRecommendations((prev) =>
        prev?.map((rec) =>
          rec.id === recommendationId
            ? { ...rec, approved: false, rejected: false, flagged: true, status: 'flagged' }
            : rec
        ) || null
      )
      queryClient.invalidateQueries({ queryKey: ['operator-recommendations'] })
    },
  })

  return (
    <div>
      <button
        onClick={() => generateMutation.mutate()}
        disabled={generateMutation.isPending}
        className="w-full px-4 py-2 bg-[#556B2F] text-white rounded-md hover:bg-[#5D4037] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {generateMutation.isPending ? 'Generating...' : 'Generate Recommendations'}
      </button>

      {/* Display generated recommendations below - Collapsible */}
      {generatedRecommendations && generatedRecommendations.length > 0 && (
        <CollapsibleRecommendations 
          recommendations={generatedRecommendations}
          approveMutation={approveMutation}
          rejectMutation={rejectMutation}
          flagMutation={flagMutation}
        />
      )}
    </div>
  )
}

function CollapsibleRecommendations({ 
  recommendations, 
  approveMutation, 
  rejectMutation, 
  flagMutation 
}: { 
  recommendations: any[]
  approveMutation: any
  rejectMutation: any
  flagMutation: any
}) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="mt-6 space-y-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full p-4 bg-gradient-to-r from-[#F5E6D3] to-white border border-[#D4C4B0]/50 rounded-lg hover:bg-[#F5E6D3]/80 transition-colors"
      >
        <h3 className="text-lg font-semibold text-[#5D4037]">
          Generated Recommendations ({recommendations.length})
        </h3>
        <svg
          className={`w-5 h-5 text-[#556B2F] transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isExpanded && (
        <div className="space-y-3">
            {recommendations.map((rec: any, idx: number) => {
              const isApproved = rec.approved || rec.status === 'approved'
              const isRejected = rec.rejected || rec.status === 'rejected'
              const isFlagged = rec.flagged || rec.status === 'flagged'
              const isPending = !isApproved && !isRejected && !isFlagged

              return (
                <div
                  key={rec.id || idx}
                  className={`border rounded-lg p-4 ${
                    isApproved
                      ? 'bg-green-50 border-green-200'
                      : isRejected
                      ? 'bg-red-50 border-red-200'
                      : isFlagged
                      ? 'bg-yellow-50 border-yellow-200'
                      : 'bg-gradient-to-r from-[#F5E6D3] to-white border-[#D4C4B0]/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="text-md font-semibold text-[#5D4037]">{rec.title}</h4>
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            rec.priority === 'high'
                              ? 'bg-red-100 text-red-800'
                              : rec.priority === 'medium'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-[#F5E6D3] text-[#5D4037]'
                          }`}
                        >
                          {rec.priority || 'medium'}
                        </span>
                        {isApproved && (
                          <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                            ✓ Approved
                          </span>
                        )}
                        {isRejected && (
                          <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                            ✗ Rejected
                          </span>
                        )}
                        {isFlagged && (
                          <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">
                            ⚠ Flagged
                          </span>
                        )}
                        {isPending && (
                          <span className="px-2 py-1 text-xs bg-gradient-to-r from-[#F5E6D3] to-white text-[#5D4037] border border-[#D4C4B0]/50 rounded">
                            Pending
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-[#556B2F] mb-2">
                        {rec.recommendation_text || rec.description}
                      </p>
                      {rec.action_items && rec.action_items.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs font-medium text-[#556B2F] mb-1">Action Items:</p>
                          <ul className="list-disc list-inside space-y-1">
                            {rec.action_items.slice(0, 3).map((item: string, itemIdx: number) => (
                              <li key={itemIdx} className="text-xs text-[#556B2F]">
                                {item}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {rec.expected_impact && (
                        <p className="text-xs text-[#8B6F47] mt-2">
                          <span className="font-medium">Expected Impact:</span> {rec.expected_impact}
                        </p>
                      )}
                    </div>
                  </div>
                  {isPending && (
                    <div className="mt-4 flex gap-2 pt-3 border-t border-[#D4C4B0]">
                      <button
                        onClick={() => approveMutation.mutate(rec.id)}
                        disabled={approveMutation.isPending}
                        className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {approveMutation.isPending ? 'Approving...' : '✓ Approve'}
                      </button>
                      <button
                        onClick={() => rejectMutation.mutate(rec.id)}
                        disabled={rejectMutation.isPending}
                        className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {rejectMutation.isPending ? 'Rejecting...' : '✗ Reject'}
                      </button>
                      <button
                        onClick={() => flagMutation.mutate(rec.id)}
                        disabled={flagMutation.isPending}
                        className="px-3 py-1.5 text-sm bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {flagMutation.isPending ? 'Flagging...' : '⚠ Flag'}
                      </button>
                    </div>
                  )}
                </div>
              )
            })}
        </div>
      )}
    </div>
  )
}


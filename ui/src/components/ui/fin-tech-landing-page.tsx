import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Leaf, CreditCard, Wallet, Building2, DollarSign, Store, Settings } from "lucide-react";
import { fetchUsers, fetchUserDetail, fetchSuggestedBudget, fetchBudgetTracking, getConsentStatus } from "../../services/api";
import FinancialInsightsCarousel from "../FinancialInsightsCarousel";
import RecommendationsSection from "../RecommendationsSection";
import { WeeklyExpenseCard, ExpenseItem } from "./weekly-expense-card";
import CreditCardBrandLogo, { detectCreditCardBrand } from "../CreditCardBrandLogo";
import CircularBudgetDial from "../CircularBudgetDial";
import ConsentModal from "../ConsentModal";
import { useAuth } from "../AuthContext";

/** Leafly Fintech Landing Page (no browser chrome) */

const SoftButton = ({ children, className = "", ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { children: React.ReactNode; className?: string }) => (
  <button
    className={
      "rounded-full px-5 py-2.5 text-sm font-medium shadow-sm transition focus:outline-none focus:ring-2 focus:ring-offset-2 " +
      "bg-[#556B2F] text-white hover:bg-[#5D4037] focus:ring-[#556B2F] " +
      className
    }
    {...props}
  >
    {children}
  </button>
);

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

interface LeaflyLandingPageProps {
  userId?: string;
  hideMonthlySpending?: boolean; // Option to hide the monthly spending card
}

export default function LeaflyLandingPage({ userId, hideMonthlySpending = false }: LeaflyLandingPageProps = {}) {
  const navigate = useNavigate();
  const { user: currentUser, logout } = useAuth();
  const [user, setUser] = useState<any>(null);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [budget, setBudget] = useState<any>(null);
  const [budgetTracking, setBudgetTracking] = useState<any>(null);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'home' | 'insights' | 'recommendations'>('home');
  const [showConsentModal, setShowConsentModal] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  useEffect(() => {
    const loadUser = async () => {
      try {
        setLoading(true);
        let targetUserId: string | undefined = userId;
        
        // If no userId provided, load a random user (for preview)
        if (!targetUserId) {
          const users = await fetchUsers();
          if (users && users.length > 0) {
            const randomUser = users[Math.floor(Math.random() * users.length)];
            targetUserId = randomUser.id;
          } else {
            setLoading(false);
            return;
          }
        }
        
        // Ensure we have a valid userId before proceeding
        if (!targetUserId) {
          setLoading(false);
          return;
        }
        
        // Fetch user detail
        const userDetail = await fetchUserDetail(targetUserId, 30);
        setUser({ id: targetUserId, ...userDetail });
        setAccounts(userDetail.accounts || []);
        setTransactions(userDetail.transactions || []);
        
        // Check if user is viewing their own data
        const isViewingOwnData = currentUser && currentUser.id === targetUserId;
        
        // Check consent status if viewing own data
        if (isViewingOwnData) {
          try {
            const consent = await getConsentStatus(targetUserId);
            // Show consent modal if user hasn't consented
            if (!consent?.consented) {
              setShowConsentModal(true);
            }
          } catch (error) {
            console.error("Failed to check consent status:", error);
          }
        }
        
        // Fetch user's budget (users can see their own data regardless of consent)
        try {
          const budgetData = await fetchSuggestedBudget(targetUserId);
          setBudget(budgetData);
        } catch (budgetError: any) {
          // Log errors, but don't block UI - users should see their own data
          if (budgetError.status !== 403 || !isViewingOwnData) {
          console.error("Failed to load budget:", budgetError);
          }
        }
        
        // Fetch budget tracking to get spending data (users can see their own data regardless of consent)
        try {
          const trackingData = await fetchBudgetTracking(targetUserId);
          setBudgetTracking(trackingData);
        } catch (trackingError: any) {
          // Log errors, but don't block UI - users should see their own data
          if (trackingError.status !== 403 || !isViewingOwnData) {
          console.error("Failed to load budget tracking:", trackingError);
          }
        }
      } catch (error) {
        console.error("Failed to load user:", error);
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, [userId, currentUser]);

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-[#F5E6D3] via-[#D4C4B0] to-[#5D4037]">
      {/* Fonts */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        :root { --font-sans: 'Plus Jakarta Sans', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif; }
        .font-jakarta { font-family: var(--font-sans); }
      `}</style>

      {/* Top nav (no fake browser bar) */}
      <nav className="mx-auto flex w-full max-w-[1180px] items-center justify-between px-4 py-6 md:px-0">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#556B2F] text-white shadow">
            <Leaf className="h-5 w-5" />
          </div>
          <span className="font-jakarta text-xl font-semibold tracking-tight text-[#5D4037]">Leafly</span>
        </div>
        <div className="hidden items-center gap-8 md:flex">
          <button
            onClick={() => setActiveTab('home')}
            className={`text-sm transition-colors ${
              activeTab === 'home' 
                ? 'text-[#5D4037] font-semibold border-b-2 border-[#556B2F] pb-1' 
                : 'text-[#8B6F47] hover:text-[#5D4037]'
            }`}
          >
            Home
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
            onClick={() => setShowConsentModal(true)}
            className="flex items-center gap-2 rounded-full px-4 py-2 text-sm text-[#5D4037] hover:bg-white/50"
          >
            <Settings className="h-4 w-4" />
            Settings
          </button>
          <SoftButton onClick={handleLogout}>Log Out</SoftButton>
        </div>
      </nav>

      {/* Main Content Area */}
      {activeTab === 'home' ? (
        <div className="mx-auto grid w-full max-w-[1180px] grid-cols-1 gap-6 px-4 pb-14 md:grid-cols-2 md:px-0">
        {/* Left: headline */}
        <div className="flex flex-col justify-start space-y-8 pr-2">
          <div>
            <h1 className="text-5xl md:text-6xl font-semibold leading-[1.05] tracking-tight text-[#5D4037]">
              Welcome back,
              <br />
              {loading ? "..." : user ? user.name : "User"}.
            </h1>
            
            {/* Budget Expense Card - Hidden if hideMonthlySpending is true */}
            {!hideMonthlySpending && budget && budget.total_budget && budgetTracking && (() => {
              // Transform category breakdown into expense items for the chart
              // Colors adapted to match current color scheme: #556B2F (green), #8B6F47 (tan), #5D4037 (brown)
              const categoryColors: { [key: string]: string } = {
                'Food and Drink': '85 50% 40%', // #556B2F green variant
                'Grocery': '85 45% 45%', // Lighter green
                'Shopping': '30 50% 50%', // Orange-brown
                'Transportation': '25 60% 45%', // Brown-orange
                'Entertainment': '200 50% 50%', // Blue
                'Travel': '180 50% 45%', // Teal
                'Bills': '280 40% 50%', // Purple
                'Healthcare': '0 60% 50%', // Red
                'Education': '240 50% 50%', // Indigo
                'Other': '30 20% 50%', // Muted brown-gray
              };

              // Get category breakdown and convert to expense items
              const categoryBreakdown = budgetTracking.category_breakdown || {};
              const expenseItems: ExpenseItem[] = Object.entries(categoryBreakdown)
                .filter(([_, data]: [string, any]) => (data.spent || 0) > 0)
                .map(([category, data]: [string, any]) => {
                  const spent = Math.abs(data.spent || 0);
                  const totalSpent = Math.abs(budgetTracking.total_spent || 0);
                  const percentage = totalSpent > 0 ? (spent / totalSpent) * 100 : 0;
                  
                  // Get color for category or use a default based on category name
                  let color = categoryColors[category] || categoryColors['Other'];
                  if (!categoryColors[category]) {
                    // Generate a color based on category name hash
                    const hash = category.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
                    const hue = hash % 360;
                    color = `${hue} 70% 50%`;
                  }
                  
                  return {
                    category,
                    percentage: Math.round(percentage * 10) / 10,
                    amount: spent,
                    color,
                  };
                })
                .sort((a, b) => b.amount - a.amount); // Show all categories

              // Get current month date range
              const now = new Date();
              const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
              const monthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0);
              const dateRange = `${monthStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${monthEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;

              return (
              <div className="mt-6">
                  <WeeklyExpenseCard
                    title="Monthly Spending"
                    dateRange={dateRange}
                    data={expenseItems}
                    currency="$"
                    buttonText="View Details"
                    onButtonClick={() => setActiveTab('insights')}
                    className="bg-gradient-to-br from-[#5D4037] to-[#3E2723] border-[#5D4037]"
                  />
                </div>
              );
            })()}
            
            {/* Budget Dial - Monthly Spending Breakdown - Above Projected Monthly Income */}
            {budget && budget.total_budget && budgetTracking && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2, duration: 0.5 }}
                className="mt-6 p-6 rounded-xl bg-gradient-to-br from-[#556B2F] to-[#3E4A2F] shadow-lg"
              >
                <div className="text-center mb-4">
                  <h3 className="text-lg font-semibold text-white/90 mb-1">Monthly Budget</h3>
                  <p className="text-xs text-white/70">Spending Overview</p>
                </div>
                <div className="flex justify-center">
                  <CircularBudgetDial
                    spent={Math.abs(budgetTracking.total_spent || 0)}
                    total={budgetTracking.total_budget || budget.total_budget || 0}
                    size={240}
                    strokeWidth={24}
                  />
                </div>
                {/* Budget Summary Stats */}
                <div className="grid grid-cols-3 gap-3 mt-6 pt-6 border-t border-white/20">
                  <div className="text-center">
                    <p className="text-xs text-white/70 mb-1">Budget</p>
                    <p className="text-sm font-semibold text-white">
                      ${((budgetTracking.total_budget || budget.total_budget || 0) / 1000).toFixed(1)}k
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-white/70 mb-1">Spent</p>
                    <p className="text-sm font-semibold text-white">
                      ${(Math.abs(budgetTracking.total_spent || 0) / 1000).toFixed(1)}k
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-white/70 mb-1">Remaining</p>
                    <p className={`text-sm font-semibold ${
                      (budgetTracking.remaining || 0) >= 0 ? 'text-white' : 'text-red-300'
                    }`}>
                      ${(Math.abs(budgetTracking.remaining || 0) / 1000).toFixed(1)}k
                    </p>
                  </div>
                </div>
              </motion.div>
            )}
            
            {/* Projected Monthly Income Banner */}
            {(() => {
              // Calculate projected monthly income from payroll in past 30 days
              const now = new Date();
              const thirtyDaysAgo = new Date(now);
              thirtyDaysAgo.setDate(now.getDate() - 30);
              
              const payrollTransactions = (transactions || []).filter((tx: any) => {
                if (!tx.date || tx.amount <= 0) return false;
                const txDate = new Date(tx.date);
                const isWithin30Days = txDate >= thirtyDaysAgo && txDate <= now;
                const merchantName = (tx.merchant_name || '').toLowerCase();
                const isPayroll = merchantName.includes('payroll') || 
                                 merchantName.includes('deposit') ||
                                 tx.primary_category === 'Transfer In' ||
                                 (tx.amount >= 1000 && tx.amount > 0); // Reasonable payroll amount
                
                return isWithin30Days && isPayroll;
              });
              
              const projectedMonthlyIncome = payrollTransactions.reduce((sum: number, tx: any) => sum + tx.amount, 0);
              
              if (projectedMonthlyIncome > 0) {
                return (
                  <div className="mt-6 p-4 rounded-lg bg-gradient-to-r from-[#F5E6D3] to-white border border-[#D4C4B0]/50">
                    <div className="flex items-center gap-3">
                      <div className="rounded-full bg-[#556B2F]/20 p-2">
                        <DollarSign className="h-5 w-5 text-[#556B2F]" />
                      </div>
                      <div>
                        <div className="text-xs text-[#8B6F47] uppercase tracking-wider">Projected Monthly Income</div>
                        <div className="text-2xl font-semibold text-[#5D4037]">
                          {new Intl.NumberFormat("en-US", {
                            style: "currency",
                            currency: "USD",
                            minimumFractionDigits: 2,
                          }).format(projectedMonthlyIncome)}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              }
              return null;
            })()}
            {/* Monthly Budget Card */}
            {budget && budget.total_budget && (
              <div className="mt-6 p-4 rounded-lg bg-gradient-to-r from-[#F5E6D3] to-white border border-[#D4C4B0]/50">
                <div className="flex items-center gap-3">
                  <div className="rounded-full bg-[#556B2F]/20 p-2">
                    <DollarSign className="h-5 w-5 text-[#556B2F]" />
                  </div>
                  <div>
                    <div className="text-xs text-[#8B6F47] uppercase tracking-wider">Suggested Monthly Budget</div>
                    <div className="text-2xl font-semibold text-[#5D4037]">
                      {new Intl.NumberFormat("en-US", {
                        style: "currency",
                        currency: "USD",
                        minimumFractionDigits: 2,
                      }).format(budget.total_budget)}
                    </div>
                  </div>
                </div>
                <p className="text-[#5D4037]/90 text-sm leading-relaxed mt-4 pt-4 border-t border-[#D4C4B0]">
                  This budget was based on 80% of your predicted monthly income. We recommend you set 20% of all paychecks towards savings, emergency funds, or paying off debts.
                </p>
              </div>
            )}
            {/* Most Frequent Merchant - Last 30 Days */}
            {(() => {
              // Get past 30 days transactions
              const now = new Date();
              const thirtyDaysAgo = new Date(now);
              thirtyDaysAgo.setDate(now.getDate() - 30);
              
              const past30DaysTransactions = (transactions || []).filter((tx: any) => {
                if (!tx.date) return false;
                const txDate = new Date(tx.date);
                const isWithin30Days = txDate >= thirtyDaysAgo && txDate <= now;
                const isSpending = tx.amount < 0; // Only spending transactions (negative amounts)
                const merchantName = (tx.merchant_name || '').toLowerCase();
                const isInterestCharge = merchantName.includes('interest charge') || 
                                        merchantName === 'interest charge';
                const isSubscription = tx.is_subscription === true || 
                                      tx.primary_category === 'Subscription' ||
                                      tx.detailed_category === 'Subscription';
                
                return isWithin30Days && 
                       isSpending && 
                       !isInterestCharge && 
                       !isSubscription &&
                       merchantName.trim() !== '';
              });

              // Count merchant frequency
              const merchantCounts: { [key: string]: number } = {};
              past30DaysTransactions.forEach((tx: any) => {
                const merchant = tx.merchant_name || '';
                if (merchant && merchant.trim() !== '') {
                  merchantCounts[merchant] = (merchantCounts[merchant] || 0) + 1;
                }
              });

              // Find most frequent merchant (only if count > 1)
              const mostFrequentMerchant = Object.entries(merchantCounts)
                .filter(([, count]) => count > 1) // Only merchants visited more than once
                .sort(([, a], [, b]) => b - a)[0];

              if (mostFrequentMerchant && mostFrequentMerchant[1] > 1) {
                const [merchantName, count] = mostFrequentMerchant;
                return (
                  <div className="mt-4 p-4 rounded-lg bg-gradient-to-r from-[#F5E6D3] to-white border border-[#D4C4B0]/50">
                    <div className="flex items-center gap-3">
                      <div className="rounded-full bg-[#8B6F47]/20 p-2">
                        <Store className="h-5 w-5 text-[#8B6F47]" />
                      </div>
                      <div className="flex-1">
                        <div className="text-xs text-[#8B6F47] uppercase tracking-wider">Most Visited (Last 30 Days)</div>
                        <div className="text-lg font-semibold text-[#5D4037]">
                          {merchantName}
                        </div>
                        <div className="text-sm text-[#8B6F47] mt-1">
                          {count} {count === 1 ? 'visit' : 'visits'}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              }
              return null;
            })()}
            
            {/* Notes Section */}
            <div className="mt-6 pt-4 border-t border-[#D4C4B0]/50">
              <p className="text-xs text-[#8B6F47]/70 italic">
                This is from the last 30 days of purchases
              </p>
            </div>
          </div>
        </div>

        {/* Right: animated card grid */}
        <div className="flex flex-col mt-[144px]">
          <div className="grid grid-cols-1 gap-y-[30px] gap-x-[30px] md:grid-cols-2 items-start">
          {/* Display all user accounts in the same card style */}
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
              <AccountCard key={account.id} account={account} index={index} userId={user?.id || ""} />
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
              <FinancialInsightsCarousel userId={user.id} />
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
              <RecommendationsSection userId={user.id} windowDays={30} readOnly={false} />
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

      {/* Consent Modal - Show when Settings button is clicked or when user hasn't consented and is viewing their own data */}
      {user && currentUser && currentUser.id === user.id && (
        <ConsentModal
          userId={user.id}
          isOpen={showConsentModal}
          keepOpenOnGrant={true} // Keep modal open when granting from Settings so user can see confirmation
          onClose={() => setShowConsentModal(false)}
          onConsentChange={(consented) => {
            if (consented) {
              // Refetch budget data after consent is granted
              const loadBudgetData = async () => {
                try {
                  const budgetData = await fetchSuggestedBudget(user.id);
                  setBudget(budgetData);
                } catch (error) {
                  console.error("Failed to load budget:", error);
                }
                try {
                  const trackingData = await fetchBudgetTracking(user.id);
                  setBudgetTracking(trackingData);
                } catch (error) {
                  console.error("Failed to load budget tracking:", error);
                }
              };
              loadBudgetData();
              // Don't auto-close modal - let user close it manually after seeing confirmation
            }
          }}
        />
      )}
    </div>
  );
}


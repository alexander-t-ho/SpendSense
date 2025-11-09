import React from "react"
import { Link, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { useAuth } from '../components/AuthContext'
import { useEffect } from 'react'
import { ShieldCheck, ArrowUpRight, LogIn, UserPlus, Leaf } from "lucide-react"

/** Leafly Fintech Landing Page */

const Stat = ({ label, value }: { label: string; value: string }) => (
  <div className="space-y-1">
    <div className="text-3xl font-semibold tracking-tight text-[#5D4037]">{value}</div>
    <div className="text-sm text-[#8B6F47]">{label}</div>
  </div>
)

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
)

function MiniBars() {
  return (
    <div className="mt-6 flex h-36 items-end gap-4 rounded-xl bg-gradient-to-b from-[#F5E6D3] to-white p-4">
      {[18, 48, 72, 96].map((h, i) => (
        <motion.div
          key={i}
          initial={{ height: 0, opacity: 0.6 }}
          animate={{ height: h }}
          transition={{ delay: 0.5 + i * 0.15, type: "spring" }}
          className="w-10 rounded-xl bg-gradient-to-t from-[#8B6F47]/60 to-[#5D4037]/80 shadow-inner"
        />
      ))}
    </div>
  )
}

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
          <stop offset="100%" stopColor="#8B6F47" />
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
  )
}

export default function LandingPage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    // Redirect authenticated users to dashboard
    if (user) {
      navigate('/my-dashboard')
    }
  }, [user, navigate])

  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-[#F5E6D3] to-[#D4C4B0]">
      {/* Fonts */}
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
          {['Solutions', 'Product', 'Company', 'Insight'].map((item) => (
            <a key={item} href="#" className="text-sm text-[#8B6F47] hover:text-[#5D4037]">{item}</a>
          ))}
        </div>
        <div className="hidden gap-2 md:flex">
          <Link to="/login" className="rounded-full px-4 py-2 text-sm text-[#5D4037] hover:bg-white/50">Login</Link>
          <Link to="/login">
            <SoftButton>Sign Up</SoftButton>
          </Link>
        </div>
      </nav>

      {/* Hero area */}
      <div className="mx-auto grid w-full max-w-[1180px] grid-cols-1 gap-6 px-4 pb-14 md:grid-cols-2 md:px-0">
        {/* Left: headline */}
        <div className="flex flex-col justify-center space-y-8 pr-2">
          <div>
            <h1 className="text-5xl md:text-6xl font-semibold leading-[1.05] tracking-tight text-[#5D4037]">
              Money Doesn't Grow on Trees
            </h1>
            <p className="mt-4 max-w-md text-[#8B6F47]">
              Helping you optimize your spending to continue living your best life
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login">
              <SoftButton>
                Open Account <ArrowUpRight className="ml-1 inline h-4 w-4" />
              </SoftButton>
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-8 pt-2 md:max-w-sm">
            <Stat label="Active Users" value="100+" />
            <Stat label="Savings Generated" value="10s of Dollars Saved!" />
          </div>
          <div className="mt-6 flex items-center gap-8 opacity-70">
            <span className="text-xs text-[#8B6F47]">TRUSTED BY THE BEST</span>
            <div className="flex items-center gap-6 text-[#8B6F47]">
              <span className="font-semibold">TechCorp</span>
              <span className="font-semibold">FinanceHub</span>
              <span className="font-semibold">MoneyWise</span>
            </div>
          </div>
        </div>

        {/* Right: animated card grid */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* Secure card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="relative col-span-1 overflow-hidden rounded-xl bg-gradient-to-b from-[#556B2F] to-[#5D4037] p-6 text-white shadow-lg"
          >
            <div className="absolute inset-0">
              <svg className="absolute inset-0 h-full w-full opacity-30" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <radialGradient id="rg" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#8B6F47" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="transparent" />
                  </radialGradient>
                </defs>
                <rect width="400" height="400" fill="url(#rg)" />
                {[...Array(12)].map((_, i) => (
                  <circle key={i} cx="200" cy="200" r={20 + i * 14} fill="none" stroke="currentColor" strokeOpacity="0.12" />
                ))}
              </svg>
            </div>
            <div className="relative flex h-full flex-col justify-between">
              <div className="flex items-center gap-3">
                <div className="rounded-full bg-white/20 p-2 ring-1 ring-white/10">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <span className="text-xs uppercase tracking-wider text-white/80">Extra Secure</span>
              </div>
              <div className="mt-6 text-xl leading-snug text-white/95">
                Fraud and security
                <br /> keep your money safe
              </div>
              <motion.div
                className="absolute right-6 top-6 h-12 w-12 rounded-full bg-white/20"
                animate={{ boxShadow: ["0 0 0 0 rgba(255,255,255,0.35)", "0 0 0 16px rgba(255,255,255,0)"] }}
                transition={{ duration: 2.5, repeat: Infinity }}
              />
            </div>
          </motion.div>

          {/* Currencies card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="relative col-span-1 overflow-hidden rounded-xl bg-gradient-to-b from-[#8B6F47] to-[#5D4037] p-6 text-white shadow-lg"
          >
            <div className="pointer-events-none absolute -right-8 -top-10 opacity-70">
              <Planet />
            </div>
            <div className="relative mt-24 text-sm text-white/90">Insights</div>
            <div className="text-xl font-medium leading-snug">
              Personalized
              <br /> financial insights
            </div>
          </motion.div>

          {/* Growth card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="col-span-1 rounded-xl bg-white p-6 text-[#5D4037] shadow-lg ring-1 ring-[#D4C4B0]"
          >
            <div className="text-sm text-[#8B6F47]">Growth Revenue</div>
            <div className="mt-2 text-3xl font-semibold tracking-tight">$50,240 <span className="text-sm font-medium text-[#8B6F47] align-middle">USD</span></div>
            <div className="mt-1 text-xs text-[#556B2F]">↑ 0.024%</div>
            <MiniBars />
          </motion.div>

          <div className="hidden md:block" />
        </div>
      </div>

      <footer className="mx-auto w-full max-w-[1180px] px-4 pb-10 text-center text-xs text-[#8B6F47] md:px-0">
        © {new Date().getFullYear()} Leafly, Inc. All rights reserved.
      </footer>
    </div>
  )
}

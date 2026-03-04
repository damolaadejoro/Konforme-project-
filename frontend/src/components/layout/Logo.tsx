import React from 'react'

interface LogoProps {
  size?: 'sm' | 'md' | 'lg'
  showText?: boolean
}

export default function Logo({ size = 'md', showText = true }: LogoProps) {
  const dims = { sm: 28, md: 36, lg: 48 }[size]
  const textSize = { sm: 'text-base', md: 'text-lg', lg: 'text-2xl' }[size]

  return (
    <div className="flex items-center gap-2.5">
      <svg
        width={dims}
        height={dims}
        viewBox="0 0 200 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="flex-shrink-0"
      >
        {/* Background circle */}
        <circle cx="100" cy="100" r="100" fill="#0B1F3A" />
        {/* Shield shape */}
        <path
          d="M100 30L40 58V100C40 137 64 170 100 182C136 170 160 137 160 100V58L100 30Z"
          fill="#0B1F3A"
          stroke="#00C2D4"
          strokeWidth="6"
        />
        {/* K lettermark */}
        <path
          d="M72 72V128M72 100L104 72M72 100L108 128"
          stroke="#00C2D4"
          strokeWidth="10"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {showText && (
        <span className={`font-syne font-bold ${textSize} text-white tracking-tight`}>
          Konf<span className="text-cyan-500">orme</span>
        </span>
      )}
    </div>
  )
}

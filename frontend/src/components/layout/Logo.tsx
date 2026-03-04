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
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="flex-shrink-0"
      >
        {/* Shield base */}
        <path
          d="M20 3L5 9.5V20C5 28.284 11.716 35.5 20 37C28.284 35.5 35 28.284 35 20V9.5L20 3Z"
          fill="#0B1F3A"
          stroke="#00C2D4"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        {/* Glow effect */}
        <path
          d="M20 3L5 9.5V20C5 28.284 11.716 35.5 20 37C28.284 35.5 35 28.284 35 20V9.5L20 3Z"
          fill="none"
          stroke="#00C2D4"
          strokeWidth="0.5"
          strokeLinejoin="round"
          opacity="0.4"
        />
        {/* K lettermark */}
        <text
          x="20"
          y="26"
          fontFamily="Syne, sans-serif"
          fontSize="16"
          fontWeight="700"
          fill="#00C2D4"
          textAnchor="middle"
        >
          K
        </text>
      </svg>
      {showText && (
        <span className={`font-syne font-bold ${textSize} text-white tracking-tight`}>
          Konf<span className="text-cyan-500">orme</span>
        </span>
      )}
    </div>
  )
}

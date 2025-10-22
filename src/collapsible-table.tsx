"use client"

import type React from "react"

import { useState } from "react"

interface CollapsibleTableProps {
  title: string
  children: React.ReactNode
  defaultOpen?: boolean
}

export default function CollapsibleTable({ title, children, defaultOpen = false }: CollapsibleTableProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="bg-background border border-border rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-background/50 transition-colors"
      >
        <h4 className="font-semibold text-foreground">{title}</h4>
        <svg
          className={`w-5 h-5 text-muted-foreground transition-transform ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </button>
      {isOpen && <div className="border-t border-border">{children}</div>}
    </div>
  )
}

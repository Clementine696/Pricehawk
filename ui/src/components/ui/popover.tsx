"use client"

import * as React from "react"

interface PopoverProps {
  children: React.ReactNode
}

interface PopoverTriggerProps {
  children: React.ReactNode
  asChild?: boolean
}

interface PopoverContentProps {
  children: React.ReactNode
  align?: "start" | "center" | "end"
  className?: string
}

const PopoverContext = React.createContext<{
  open: boolean
  setOpen: (open: boolean) => void
}>({
  open: false,
  setOpen: () => {},
})

export function Popover({ children }: PopoverProps) {
  const [open, setOpen] = React.useState(false)

  return (
    <PopoverContext.Provider value={{ open, setOpen }}>
      <div className="relative inline-block">{children}</div>
    </PopoverContext.Provider>
  )
}

export function PopoverTrigger({ children, asChild }: PopoverTriggerProps) {
  const { open, setOpen } = React.useContext(PopoverContext)

  const handleClick = () => {
    setOpen(!open)
  }

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as React.ReactElement<any>, {
      onClick: handleClick,
    })
  }

  return <div onClick={handleClick}>{children}</div>
}

export function PopoverContent({ children, align = "start", className = "" }: PopoverContentProps) {
  const { open, setOpen } = React.useContext(PopoverContext)
  const contentRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (contentRef.current && !contentRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    if (open) {
      document.addEventListener("mousedown", handleClickOutside)
      return () => document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [open, setOpen])

  if (!open) return null

  const alignmentClasses = {
    start: "left-0",
    center: "left-1/2 -translate-x-1/2",
    end: "right-0",
  }

  return (
    <div
      ref={contentRef}
      className={`absolute top-full mt-2 z-50 rounded-md border border-gray-200 bg-white shadow-lg ${alignmentClasses[align]} ${className}`}
      style={{ minWidth: '280px' }}
    >
      {children}
    </div>
  )
}

"use client"

import * as React from "react"

interface CalendarProps {
  mode?: "single"
  selected?: Date
  onSelect?: (date: Date | undefined) => void
  disabled?: (date: Date) => boolean
  defaultMonth?: Date
}

export function Calendar({ mode = "single", selected, onSelect, disabled, defaultMonth }: CalendarProps) {
  const [currentMonth, setCurrentMonth] = React.useState(() => {
    return defaultMonth || selected || new Date()
  })

  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
  const dayNames = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startingDayOfWeek = firstDay.getDay()

    return { daysInMonth, startingDayOfWeek, year, month }
  }

  const { daysInMonth, startingDayOfWeek, year, month } = getDaysInMonth(currentMonth)

  const handlePrevMonth = () => {
    setCurrentMonth(new Date(year, month - 1, 1))
  }

  const handleNextMonth = () => {
    setCurrentMonth(new Date(year, month + 1, 1))
  }

  const handleDateClick = (day: number) => {
    const date = new Date(year, month, day)
    if (disabled && disabled(date)) return
    onSelect?.(date)
  }

  const isToday = (day: number) => {
    const today = new Date()
    return today.getDate() === day && today.getMonth() === month && today.getFullYear() === year
  }

  const isSelected = (day: number) => {
    if (!selected) return false
    return selected.getDate() === day && selected.getMonth() === month && selected.getFullYear() === year
  }

  const isDisabled = (day: number) => {
    if (!disabled) return false
    const date = new Date(year, month, day)
    return disabled(date)
  }

  const renderDays = () => {
    const days = []

    // Empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(<div key={`empty-${i}`} className="h-10 w-10"></div>)
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const isSelectedDay = isSelected(day)
      const isTodayDay = isToday(day)
      const isDisabledDay = isDisabled(day)

      days.push(
        <button
          key={day}
          onClick={() => handleDateClick(day)}
          disabled={isDisabledDay}
          className={`h-10 w-10 rounded-md text-sm font-normal flex items-center justify-center transition-colors
            ${isSelectedDay ? 'bg-cyan-500 text-white hover:bg-cyan-600 font-semibold' : ''}
            ${isTodayDay && !isSelectedDay ? 'font-semibold text-cyan-600 underline decoration-cyan-500 decoration-2 underline-offset-2' : ''}
            ${!isSelectedDay && !isTodayDay ? 'text-gray-700 hover:bg-cyan-50 hover:text-cyan-600' : ''}
            ${isDisabledDay ? 'text-gray-300 opacity-50 cursor-not-allowed hover:bg-transparent' : 'cursor-pointer'}
          `}
        >
          {day}
        </button>
      )
    }

    return days
  }

  return (
    <div className="p-3 bg-white">
      {/* Header */}
      <div className="flex justify-center items-center mb-4 relative">
        <button
          onClick={handlePrevMonth}
          className="absolute left-0 h-8 w-8 flex items-center justify-center rounded-md hover:bg-gray-100 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <div className="text-sm font-semibold text-gray-900">
          {monthNames[month]} {year}
        </div>
        <button
          onClick={handleNextMonth}
          className="absolute right-0 h-8 w-8 flex items-center justify-center rounded-md hover:bg-gray-100 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </div>

      {/* Day names */}
      <div className="grid grid-cols-7 gap-0 mb-2">
        {dayNames.map((day) => (
          <div key={day} className="h-10 w-10 flex items-center justify-center text-xs font-medium text-gray-500">
            {day}
          </div>
        ))}
      </div>

      {/* Days */}
      <div className="grid grid-cols-7 gap-0">
        {renderDays()}
      </div>
    </div>
  )
}

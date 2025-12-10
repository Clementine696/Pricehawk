'use client';

import { ReactNode, useState } from 'react';
import { Check, ChevronDown, ChevronUp } from 'lucide-react';

interface StepCardProps {
  title: string;
  stepNumber: number;
  isActive: boolean;
  isCompleted: boolean;
  children: ReactNode;
  allowExpand?: boolean;
}

export function StepCard({
  title,
  stepNumber,
  isActive,
  isCompleted,
  children,
  allowExpand = true,
}: StepCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const shouldShowContent = isActive || isExpanded;

  const handleHeaderClick = () => {
    if (!isActive && allowExpand && isCompleted) {
      setIsExpanded(!isExpanded);
    }
  };

  const borderColorClass = isActive
    ? 'border-cyan-500'
    : isCompleted
    ? 'border-green-500'
    : 'border-gray-300';

  const bgColorClass = isActive
    ? 'bg-cyan-50'
    : isCompleted && isExpanded
    ? 'bg-green-50'
    : 'bg-white';

  return (
    <div
      className={`
        rounded-xl border-2 transition-all duration-300 overflow-hidden
        ${borderColorClass}
        ${bgColorClass}
        ${isActive ? 'shadow-lg' : 'shadow-sm'}
        ${!isActive && isCompleted ? 'opacity-90' : 'opacity-100'}
      `}
    >
      {/* Header */}
      <div
        onClick={handleHeaderClick}
        className={`
          px-6 py-4 flex items-center justify-between
          ${!isActive && allowExpand && isCompleted ? 'cursor-pointer hover:bg-opacity-80' : ''}
          transition-colors duration-200
        `}
        role={!isActive && allowExpand && isCompleted ? 'button' : undefined}
        aria-expanded={shouldShowContent}
      >
        <div className="flex items-center gap-4">
          {/* Step Number/Checkmark */}
          <div
            className={`
              w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm
              transition-all duration-200
              ${
                isActive
                  ? 'bg-cyan-500 text-white shadow-md'
                  : isCompleted
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-200 text-gray-500'
              }
            `}
          >
            {isCompleted ? <Check className="w-5 h-5" /> : <span>{stepNumber}</span>}
          </div>

          {/* Title */}
          <h3
            className={`
              text-lg font-semibold
              ${isActive ? 'text-cyan-700' : isCompleted ? 'text-green-700' : 'text-gray-700'}
            `}
          >
            {title}
          </h3>
        </div>

        {/* Expand/Collapse Icon */}
        {!isActive && allowExpand && isCompleted && (
          <div className="text-gray-400">
            {isExpanded ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </div>
        )}
      </div>

      {/* Content */}
      {shouldShowContent && (
        <div
          className={`
            px-6 pb-6
            animate-in slide-in-from-top-2 fade-in duration-300
          `}
        >
          {children}
        </div>
      )}
    </div>
  );
}

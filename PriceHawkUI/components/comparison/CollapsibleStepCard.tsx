'use client';

import { ReactNode, useState } from 'react';
import { ChevronDown, Edit2 } from 'lucide-react';

interface CollapsibleStepCardProps {
  stepNumber: number;
  stepTitle: string;
  isCompleted: boolean;
  isActive: boolean;
  children: ReactNode;
  summaryContent?: ReactNode;
  onEdit?: () => void;
}

export function CollapsibleStepCard({
  stepNumber,
  stepTitle,
  isCompleted,
  isActive,
  children,
  summaryContent,
  onEdit,
}: CollapsibleStepCardProps) {
  const [isExpanded, setIsExpanded] = useState(isActive || !isCompleted);

  // Auto-expand if active
  if (isActive && !isExpanded) {
    setIsExpanded(true);
  }

  const handleToggle = () => {
    if (isCompleted && !isActive) {
      setIsExpanded(!isExpanded);
    }
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onEdit) {
      onEdit();
    }
  };

  return (
    <div
      className={`
        rounded-xl border-2 overflow-hidden transition-all duration-300
        ${
          isActive
            ? 'border-cyan-500 shadow-lg ring-4 ring-cyan-100'
            : isCompleted
            ? 'border-gray-300 shadow-md hover:shadow-lg'
            : 'border-gray-200 shadow-sm'
        }
      `}
    >
      {/* Card Header */}
      <div
        onClick={handleToggle}
        className={`
          flex items-center justify-between px-6 py-4 cursor-pointer transition-colors
          ${
            isActive
              ? 'bg-gradient-to-r from-cyan-50 to-cyan-100'
              : isCompleted
              ? 'bg-gray-50 hover:bg-gray-100'
              : 'bg-white'
          }
        `}
      >
        <div className="flex items-center gap-3">
          {/* Step Number Badge */}
          <div
            className={`
              w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm
              transition-colors
              ${
                isActive
                  ? 'bg-cyan-500 text-white'
                  : isCompleted
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-300 text-gray-600'
              }
            `}
          >
            {stepNumber}
          </div>

          {/* Step Title */}
          <h3
            className={`
              text-lg font-semibold transition-colors
              ${
                isActive
                  ? 'text-cyan-700'
                  : isCompleted
                  ? 'text-gray-700'
                  : 'text-gray-900'
              }
            `}
          >
            {stepTitle}
          </h3>

          {/* Completed Badge */}
          {isCompleted && !isActive && (
            <span className="px-2 py-1 text-xs font-medium text-green-700 bg-green-100 rounded-full">
              Completed
            </span>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {isCompleted && !isActive && onEdit && (
            <button
              onClick={handleEdit}
              className="p-2 rounded-lg text-gray-500 hover:text-cyan-600 hover:bg-cyan-50 transition-colors"
              aria-label="Edit this step"
            >
              <Edit2 className="w-4 h-4" />
            </button>
          )}

          {isCompleted && !isActive && (
            <button
              onClick={handleToggle}
              className="p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
            >
              <ChevronDown
                className={`w-5 h-5 transition-transform duration-300 ${
                  isExpanded ? 'rotate-180' : ''
                }`}
              />
            </button>
          )}
        </div>
      </div>

      {/* Card Content */}
      <div
        className={`
          transition-all duration-300 ease-in-out overflow-hidden
          ${
            isExpanded
              ? 'max-h-[2000px] opacity-100'
              : 'max-h-0 opacity-0'
          }
        `}
      >
        <div className="p-6 bg-white border-t-2 border-gray-100">
          {isExpanded && (isActive || !summaryContent) ? children : summaryContent}
        </div>
      </div>

      {/* Collapsed Summary */}
      {!isExpanded && isCompleted && summaryContent && (
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
          <div className="text-sm text-gray-600">{summaryContent}</div>
        </div>
      )}
    </div>
  );
}

'use client';

import { ReactNode, useState, useRef, useEffect } from 'react';
import { HelpCircle } from 'lucide-react';

interface TooltipProps {
  content: string;
  children?: ReactNode;
  trigger?: 'hover' | 'click';
  placement?: 'top' | 'bottom' | 'left' | 'right';
  variant?: 'light' | 'dark';
}

export function Tooltip({
  content,
  children,
  trigger = 'hover',
  placement = 'top',
  variant = 'dark',
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  // Close tooltip when clicking outside
  useEffect(() => {
    if (!isVisible || trigger !== 'click') return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        tooltipRef.current &&
        !tooltipRef.current.contains(event.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(event.target as Node)
      ) {
        setIsVisible(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isVisible, trigger]);

  const handleTriggerAction = () => {
    if (trigger === 'click') {
      setIsVisible(!isVisible);
    }
  };

  const handleMouseEnter = () => {
    if (trigger === 'hover') {
      setIsVisible(true);
    }
  };

  const handleMouseLeave = () => {
    if (trigger === 'hover') {
      setIsVisible(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleTriggerAction();
    }
    if (e.key === 'Escape') {
      setIsVisible(false);
    }
  };

  const placementClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent',
  };

  const variantClasses = {
    light: 'bg-white text-gray-900 border border-gray-200 shadow-lg',
    dark: 'bg-gray-900 text-white',
  };

  const arrowBorderColor = {
    light: 'border-gray-200',
    dark: 'border-gray-900',
  };

  return (
    <div className="relative inline-block">
      <div
        ref={triggerRef}
        onClick={handleTriggerAction}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onKeyDown={handleKeyDown}
        tabIndex={0}
        role="button"
        aria-label="Show tooltip"
        className="inline-flex items-center cursor-help focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-1 rounded-full"
      >
        {children || <HelpCircle className="w-4 h-4 text-gray-400 hover:text-gray-600 transition-colors" />}
      </div>

      {isVisible && (
        <div
          ref={tooltipRef}
          className={`
            absolute z-50 px-3 py-2 text-sm rounded-lg whitespace-nowrap
            animate-in fade-in-0 zoom-in-95 duration-200
            ${placementClasses[placement]}
            ${variantClasses[variant]}
          `}
          role="tooltip"
        >
          {content}
          {/* Arrow */}
          <div
            className={`
              absolute w-0 h-0 border-4
              ${arrowClasses[placement]}
              ${arrowBorderColor[variant]}
            `}
            style={{
              borderTopColor: variant === 'dark' ? '#111827' : undefined,
              borderBottomColor: variant === 'dark' ? '#111827' : undefined,
              borderLeftColor: variant === 'dark' ? '#111827' : undefined,
              borderRightColor: variant === 'dark' ? '#111827' : undefined,
            }}
          />
        </div>
      )}
    </div>
  );
}

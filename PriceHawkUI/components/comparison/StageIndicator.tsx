'use client';

import { Check } from 'lucide-react';

interface StageIndicatorProps {
  currentStage: 'input' | 'selecting' | 'competitor_urls' | 'validation' | 'review' | 'results';
}

const STAGES_V3 = [
  {
    id: 'input',
    label: 'Input',
    number: 1,
    description: 'Enter product details'
  },
  {
    id: 'review',
    label: 'Review',
    number: 2,
    description: 'Confirm your inputs'
  },
  {
    id: 'results',
    label: 'Results',
    number: 3,
    description: 'View comparison'
  },
] as const;

const STAGES_V2 = [
  {
    id: 'input',
    label: 'Input',
    number: 1,
    description: 'Enter Thai Watsadu details'
  },
  {
    id: 'selecting',
    label: 'Select',
    number: 2,
    description: 'Choose competitors'
  },
  {
    id: 'competitor_urls',
    label: 'URLs',
    number: 3,
    description: 'Enter product URLs'
  },
  {
    id: 'validation',
    label: 'Validate',
    number: 4,
    description: 'Review results'
  },
] as const;

export function StageIndicator({ currentStage }: StageIndicatorProps) {
  // Determine which stage set to use
  const isV3Flow = ['input', 'review', 'results'].includes(currentStage);
  const STAGES = isV3Flow ? STAGES_V3 : STAGES_V2;

  const currentStageIndex = STAGES.findIndex((s) => s.id === currentStage);

  return (
    <div className="w-full py-6">
      <div className="flex items-center justify-between max-w-4xl mx-auto px-4">
        {STAGES.map((stage, index) => {
          const isActive = stage.id === currentStage;
          const isCompleted = index < currentStageIndex;
          const isLast = index === STAGES.length - 1;

          return (
            <div key={stage.id} className="flex items-center flex-1">
              {/* Stage Circle */}
              <div className="flex flex-col items-center relative">
                <div
                  className={`
                    w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center font-bold text-xs md:text-sm
                    transition-all duration-300 ease-in-out
                    ${
                      isActive
                        ? 'bg-gradient-to-br from-cyan-500 to-cyan-600 text-white shadow-lg scale-110 ring-2 ring-cyan-400 ring-offset-2'
                        : isCompleted
                        ? 'bg-cyan-500 text-white shadow-md'
                        : 'bg-gray-200 text-gray-400 shadow-sm'
                    }
                  `}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5 md:w-6 md:h-6 animate-in zoom-in-50 duration-200" />
                  ) : (
                    <span className={isActive ? 'scale-110' : ''}>{stage.number}</span>
                  )}
                </div>

                {/* Stage Label & Description */}
                <div className="mt-3 flex flex-col items-center">
                  <span
                    className={`
                      text-xs font-bold text-center whitespace-nowrap
                      transition-colors duration-200
                      ${
                        isActive
                          ? 'text-cyan-600'
                          : isCompleted
                          ? 'text-gray-700'
                          : 'text-gray-400'
                      }
                    `}
                  >
                    {stage.label}
                  </span>
                  <span
                    className={`
                      hidden md:block mt-0.5 text-xs text-center whitespace-nowrap
                      transition-colors duration-200
                      ${
                        isActive
                          ? 'text-cyan-500'
                          : isCompleted
                          ? 'text-gray-500'
                          : 'text-gray-400'
                      }
                    `}
                  >
                    {stage.description}
                  </span>
                </div>
              </div>

              {/* Connector Line */}
              {!isLast && (
                <div className="flex-1 mx-3 relative h-1">
                  {/* Background line */}
                  <div className="absolute inset-0 bg-gray-200 rounded-full" />
                  {/* Progress line with animation */}
                  <div
                    className={`
                      absolute inset-0 rounded-full transition-all duration-500 ease-in-out
                      ${
                        index < currentStageIndex
                          ? 'bg-gradient-to-r from-cyan-500 to-cyan-600 scale-x-100'
                          : 'bg-gray-200 scale-x-0'
                      }
                    `}
                    style={{
                      transformOrigin: 'left',
                    }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

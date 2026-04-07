'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, ChevronDown, X, Check } from 'lucide-react';

interface MultiSelectProps {
  options: string[] | { value: string; label: string }[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder: string;
  className?: string;
  /** Enable corner-drag resize handle. Default: true */
  resizable?: boolean;
}

export function MultiSelect({
  options,
  selected,
  onChange,
  placeholder,
  className = '',
  resizable = true,
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [dropdownWidth, setDropdownWidth] = useState<number | null>(null);
  const [dropdownHeight, setDropdownHeight] = useState(192);
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const resizeHandleRef = useRef<HTMLDivElement>(null);

  const normalizedOptions = options
    .filter(opt => opt !== null && opt !== undefined)
    .map(opt =>
      typeof opt === 'string' ? { value: opt, label: opt } : opt
    );

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (isOpen && searchInputRef.current) searchInputRef.current.focus();
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || !resizable) return;

    const handleMouseMove = (e: MouseEvent) => {
      const containerRect = containerRef.current?.getBoundingClientRect();
      if (!containerRect) return;
      if (resizeHandleRef.current?.dataset.dragging === 'true') {
        e.preventDefault();
        setDropdownWidth(Math.max(200, Math.min(800, e.clientX - containerRect.left)));
        setDropdownHeight(Math.max(100, Math.min(600, e.clientY - containerRect.top - 70)));
      }
    };

    const handleMouseUp = () => {
      if (resizeHandleRef.current) resizeHandleRef.current.dataset.dragging = 'false';
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isOpen, resizable]);

  const toggleOption = (value: string) => {
    onChange(selected.includes(value) ? selected.filter(s => s !== value) : [...selected, value]);
  };

  const clearAll = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange([]);
  };

  const selectedLabels = selected.map(val => {
    const opt = normalizedOptions.find(o => o.value === val);
    return opt ? opt.label : val;
  });

  const filteredOptions = normalizedOptions.filter(o =>
    o.label && o.label.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent bg-white text-left flex items-center justify-between gap-2"
      >
        <span className={`truncate ${selected.length === 0 ? 'text-gray-500' : 'text-gray-900'}`}>
          {selected.length === 0
            ? placeholder
            : selected.length === 1
            ? selectedLabels[0]
            : `${selected.length} selected`}
        </span>
        <div className="flex items-center gap-1 flex-shrink-0">
          {selected.length > 0 && (
            <button onClick={clearAll} className="p-0.5 hover:bg-gray-200 rounded">
              <X className="w-3.5 h-3.5 text-gray-500" />
            </button>
          )}
          <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </div>
      </button>

      {isOpen && (
        <div
          className="absolute z-50 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg flex flex-col"
          style={{ width: dropdownWidth ? `${dropdownWidth}px` : '100%', minWidth: '100%' }}
        >
          <div className="p-2 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search..."
                className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-200 rounded focus:outline-none focus:ring-1 focus:ring-cyan-500"
              />
            </div>
          </div>

          <div className="overflow-auto" style={{ height: resizable ? `${dropdownHeight}px` : undefined, maxHeight: resizable ? undefined : '15rem' }}>
            {filteredOptions.length === 0 ? (
              <div className="px-4 py-2 text-gray-500 text-sm">No options found</div>
            ) : (
              filteredOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => toggleOption(option.value)}
                  className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center gap-2"
                >
                  <div className={`w-4 h-4 border rounded flex items-center justify-center flex-shrink-0 ${
                    selected.includes(option.value) ? 'bg-cyan-500 border-cyan-500' : 'border-gray-300'
                  }`}>
                    {selected.includes(option.value) && <Check className="w-3 h-3 text-white" />}
                  </div>
                  <span className="text-sm text-gray-900 break-words">{option.label}</span>
                </button>
              ))
            )}
          </div>

          {resizable && (
            <div
              ref={resizeHandleRef}
              onMouseDown={(e) => {
                e.preventDefault();
                if (resizeHandleRef.current) {
                  resizeHandleRef.current.dataset.dragging = 'true';
                  document.body.style.cursor = 'nwse-resize';
                  document.body.style.userSelect = 'none';
                }
              }}
              className="absolute bottom-0 right-0 w-4 h-4 cursor-nwse-resize hover:bg-cyan-100 rounded-bl-lg flex items-center justify-center group"
              title="Drag to resize"
            >
              <div className="w-3 h-3 border-r-2 border-b-2 border-gray-400 group-hover:border-cyan-500"></div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

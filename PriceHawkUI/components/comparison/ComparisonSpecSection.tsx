'use client';

import React from 'react';
import { ComparisonAttributeRow } from './ComparisonAttributeRow';

interface AttributeConfig {
  key: string;
  label: string;
  type?: 'text' | 'price' | 'status' | 'url';
  showIcons?: boolean;
}

interface ComparisonSpecSectionProps {
  title: string;
  attributes: AttributeConfig[];
  thaiWatsuduData: Record<string, any>;
  competitorData: Record<string, any>[];
}

export function ComparisonSpecSection({
  title,
  attributes,
  thaiWatsuduData,
  competitorData,
}: ComparisonSpecSectionProps) {
  return (
    <tbody>
      {/* Section Header */}
      <tr className="bg-gray-50">
        <td
          colSpan={2 + competitorData.length}
          className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500"
        >
          {title}
        </td>
      </tr>

      {/* Attribute Rows */}
      {attributes.map((attr) => {
        const thaiWatsuduValue = thaiWatsuduData[attr.key];
        const competitorValues = competitorData.map((data) => data[attr.key]);

        return (
          <ComparisonAttributeRow
            key={attr.key}
            label={attr.label}
            thaiWatsuduValue={thaiWatsuduValue}
            competitorValues={competitorValues}
            attributeType={attr.type}
            showIcons={attr.showIcons}
          />
        );
      })}

      {/* Section Divider */}
      <tr>
        <td
          colSpan={2 + competitorData.length}
          className="h-4 bg-white"
        ></td>
      </tr>
    </tbody>
  );
}

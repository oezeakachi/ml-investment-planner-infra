'use client'
import React from 'react'

export const SelectField: React.FC<{
  label: string; id: string; value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string; description?: string }[];
  error?: string; required?: boolean;
}> = ({ label, id, value, onChange, options, error, required }) => (
  <div className="space-y-2">
    <label htmlFor={id} className="block text-sm font-semibold text-gray-700">
      {label}{required && <span className="text-red-500">*</span>}
    </label>
    <select
      id={id} value={value}
      onChange={e => onChange(e.target.value)}
      className={`w-full px-4 py-3 rounded-lg border 
        ${error ? 'border-red-300 bg-red-50' : 'border-gray-200'}
        focus:ring-2 focus:ring-primary-700 focus:outline-none`}
    >
      <option value="">Select risk tolerance</option>
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
    {error && <p className="text-sm text-red-600">⚠ {error}</p>}
    {value && <p className="text-xs text-gray-500">{options.find(o => o.value === value)?.description}</p>}
  </div>
)

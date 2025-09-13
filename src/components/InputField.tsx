'use client'
import React from 'react'

export const InputField: React.FC<{
  label: string; id: string; type: string;
  placeholder: string; value: string;
  onChange: (v: string) => void;
  error?: string; prefix?: string; required?: boolean;
}> = ({ label, id, type, placeholder, value, onChange, error, prefix, required }) => (
  <div className="space-y-2">
    <label htmlFor={id} className="block text-sm font-semibold text-gray-700">
      {label}{required && <span className="text-red-500">*</span>}
    </label>
    <div className="relative">
      {prefix && <span className="absolute left-3 top-3 text-gray-500">{prefix}</span>}
      <input
        id={id} type={type} value={value} placeholder={placeholder}
        onChange={e => onChange(e.target.value)}
        className={`w-full px-4 py-3 rounded-lg border ${prefix ? 'pl-8' : ''} 
          ${error ? 'border-red-300 bg-red-50' : 'border-gray-200'} 
          focus:ring-2 focus:ring-primary-700 focus:outline-none`}
      />
    </div>
    {error && <p className="text-sm text-red-600">⚠ {error}</p>}
  </div>
)

'use client'
import React from 'react'

export const ResultCard: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
    <h3 className="text-lg font-semibold mb-4">{title}</h3>
    {children}
  </div>
)

export const StatItem: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="text-center p-4 bg-gray-50 rounded-lg">
    <div className="text-2xl font-bold">{value}</div>
    <div className="text-sm text-gray-600">{label}</div>
  </div>
)

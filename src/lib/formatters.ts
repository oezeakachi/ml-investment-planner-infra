export const formatCurrency = (v: number) =>
  new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', maximumFractionDigits: 0 }).format(v);

export const formatPercentage = (v: number) =>
  `${(v * 100).toFixed(1)}%`;

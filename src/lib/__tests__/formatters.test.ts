import { formatCurrency } from '../formatters'

test('formatCurrency formats numbers correctly', () => {
  expect(formatCurrency(1000)).toBe('£1,000')
})
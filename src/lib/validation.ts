import { FormData, FormErrors } from '@/types';

export function validateForm(f: FormData): FormErrors {
  const e: FormErrors = {};
  const num = (x: string) => parseFloat(x.replace(/[£,]/g, ''));

  if (!f.targetGoal || num(f.targetGoal) <= 0) e.targetGoal = 'Enter a valid target goal';
  if (!f.yearsToInvest || +f.yearsToInvest <= 0) e.yearsToInvest = 'Enter valid years';
  if (!f.monthlyContribution || num(f.monthlyContribution) < 0) e.monthlyContribution = 'Enter valid monthly contribution';
  if (!f.startingCapital || num(f.startingCapital) < 0) e.startingCapital = 'Enter valid starting capital';
  if (!f.riskTolerance) e.riskTolerance = 'Select a risk tolerance';

  return e;
}

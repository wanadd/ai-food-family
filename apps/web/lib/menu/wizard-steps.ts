/** Wizard screen index → content step (personal mode skips "persons"). */
const PERSONAL_LOGICAL_STEPS = [0, 2, 3, 4] as const;

export function wizardLogicalStep(screenIndex: number, isFamily: boolean): number {
  if (isFamily) return screenIndex;
  return PERSONAL_LOGICAL_STEPS[screenIndex] ?? 4;
}

export function maxWizardScreenIndex(isFamily: boolean): number {
  return isFamily ? 4 : 3;
}

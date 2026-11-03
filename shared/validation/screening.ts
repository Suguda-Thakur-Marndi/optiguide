/**
 * Screening input validation helpers
 */

export function validateScreeningDistance(distanceCm: number): { isValid: boolean; message?: string } {
  if (distanceCm < 20 || distanceCm > 400) {
    return {
      isValid: false,
      message: `Calibration distance ${distanceCm}cm is outside the valid range (20cm - 400cm).`,
    };
  }
  return { isValid: true };
}

export function validateConsentVersion(version: string): { isValid: boolean; message?: string } {
  if (!version || version.trim().length === 0) {
    return { isValid: false, message: 'Consent version cannot be empty.' };
  }
  return { isValid: true };
}

export function validateSessionCancellationReason(reason?: string): { isValid: boolean; message?: string } {
  if (reason && reason.length > 255) {
    return { isValid: false, message: 'Cancellation reason must not exceed 255 characters.' };
  }
  return { isValid: true };
}

// Layer: L1 — Product Experience
// Product: ai-console
// Temporal:
//   Trigger: user
//   Execution: sync
// Role: Debounce hook for input handling
// Callers: UI components
// Allowed Imports: L2
// Forbidden Imports: L3, L4, L5, L6
// Reference: Frontend Utilities

/**
 * useDebounce Hook
 *
 * Debounces a value by a specified delay.
 * Useful for search inputs to avoid excessive API calls.
 */

import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default useDebounce;

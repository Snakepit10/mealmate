import { useWS } from './useWS'

export function useCalendarWS(familyId, { onUpdate } = {}) {
  useWS(familyId ? `/ws/families/${familyId}/calendars/` : null, {
    'calendar.entry_added': onUpdate,
    'calendar.entry_updated': onUpdate,
    'calendar.entry_removed': onUpdate,
  })
}

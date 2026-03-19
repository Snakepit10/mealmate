import { useWS } from './useWS'

export function usePantryWS(familyId, { onUpdate } = {}) {
  useWS(familyId ? `/ws/families/${familyId}/pantry/` : null, {
    'pantry.item_added': onUpdate,
    'pantry.item_updated': onUpdate,
    'pantry.item_finished': onUpdate,
    'pantry.item_removed': onUpdate,
  })
}

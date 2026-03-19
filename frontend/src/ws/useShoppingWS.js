import { useWS } from './useWS'

export function useShoppingWS(familyId, { onUpdate } = {}) {
  useWS(familyId ? `/ws/families/${familyId}/shopping/` : null, {
    'shopping.item_added': onUpdate,
    'shopping.item_checked': onUpdate,
    'shopping.item_unchecked': onUpdate,
    'shopping.item_removed': onUpdate,
    'shopping.list_completed': onUpdate,
  })
}

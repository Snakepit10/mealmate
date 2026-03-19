import { startOfWeek, endOfWeek, eachDayOfInterval, addWeeks, subWeeks, format, isToday } from 'date-fns'
import { it } from 'date-fns/locale'

export function getWeekDays(referenceDate) {
  const start = startOfWeek(referenceDate, { weekStartsOn: 1 }) // Monday
  const end = endOfWeek(referenceDate, { weekStartsOn: 1 })
  return eachDayOfInterval({ start, end })
}

export function nextWeek(date) {
  return addWeeks(date, 1)
}

export function prevWeek(date) {
  return subWeeks(date, 1)
}

export function formatDay(date) {
  return format(date, 'EEE d', { locale: it })
}

export function formatDate(date) {
  return format(date, 'yyyy-MM-dd')
}

export function formatDisplayDate(dateStr) {
  const date = new Date(dateStr)
  return format(date, 'd MMMM yyyy', { locale: it })
}

export { isToday }

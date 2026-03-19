import client from './client'

export const calendarApi = {
  listCalendars: (familyId) =>
    client.get(`/families/${familyId}/calendars/`),

  createCalendar: (familyId, data) =>
    client.post(`/families/${familyId}/calendars/`, data),

  updateCalendar: (familyId, cid, data) =>
    client.patch(`/families/${familyId}/calendars/${cid}/`, data),

  deleteCalendar: (familyId, cid) =>
    client.delete(`/families/${familyId}/calendars/${cid}/`),

  // Slots
  listSlots: (familyId, cid, params) =>
    client.get(`/families/${familyId}/calendars/${cid}/slots/`, { params }),

  createSlot: (familyId, cid, data) =>
    client.post(`/families/${familyId}/calendars/${cid}/slots/`, data),

  deleteSlot: (familyId, cid, sid) =>
    client.delete(`/families/${familyId}/calendars/${cid}/slots/${sid}/`),

  // Entries
  listEntries: (familyId, cid, sid) =>
    client.get(`/families/${familyId}/calendars/${cid}/slots/${sid}/entries/`),

  createEntry: (familyId, cid, sid, data) =>
    client.post(`/families/${familyId}/calendars/${cid}/slots/${sid}/entries/`, data),

  updateEntry: (familyId, cid, sid, eid, data) =>
    client.patch(`/families/${familyId}/calendars/${cid}/slots/${sid}/entries/${eid}/`, data),

  deleteEntry: (familyId, cid, sid, eid) =>
    client.delete(`/families/${familyId}/calendars/${cid}/slots/${sid}/entries/${eid}/`),

  planWeek: (familyId, cid, data) =>
    client.post(`/families/${familyId}/calendars/${cid}/plan-week/`, data),

  checkPantry: (familyId, cid, params) =>
    client.get(`/families/${familyId}/calendars/${cid}/check-pantry/`, { params }),
}

const initData = () => window.Telegram?.WebApp?.initData || ''

const headers = () => ({
  'Content-Type': 'application/json',
  'X-Telegram-Init-Data': initData(),
})

async function request(method, path, body) {
  const res = await fetch(`/api${path}`, {
    method,
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.text().catch(() => res.status)
    throw new Error(`${method} /api${path} → ${res.status}: ${err}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  getReminders: (filter = 'all', tag = null) => {
    const params = new URLSearchParams({ filter })
    if (tag) params.append('tag', tag)
    return request('GET', `/reminders?${params}`)
  },
  createReminder: (body) => request('POST', '/reminders', body),
  markDone: (id) => request('PATCH', `/reminders/${id}/done`),
  deleteReminder: (id) => request('DELETE', `/reminders/${id}`),
  getTags: () => request('GET', '/tags'),
}

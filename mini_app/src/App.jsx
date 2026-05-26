import { useState, useEffect, useCallback } from 'react'
import { api } from './api.js'
import TodoList from './components/TodoList.jsx'
import AddTask from './components/AddTask.jsx'
import TagFilter from './components/TagFilter.jsx'

const tg = window.Telegram?.WebApp

export default function App() {
  const [data, setData] = useState({ reminders: [], timezone: 'Europe/Moscow' })
  const [tags, setTags] = useState([])
  const [filter, setFilter] = useState('all')
  const [activeTag, setActiveTag] = useState(null)
  const [showAdd, setShowAdd] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadReminders = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.getReminders(filter, activeTag)
      setData(result)
    } catch (e) {
      setError('Не удалось загрузить напоминания')
    } finally {
      setLoading(false)
    }
  }, [filter, activeTag])

  const loadTags = useCallback(async () => {
    try {
      setTags(await api.getTags())
    } catch { /* non-critical */ }
  }, [])

  useEffect(() => {
    tg?.ready()
    tg?.expand()
    loadReminders()
    loadTags()
  }, [])

  useEffect(() => { loadReminders() }, [filter, activeTag])

  const handleDone = async (id) => {
    await api.markDone(id)
    setData(prev => ({ ...prev, reminders: prev.reminders.filter(r => r.id !== id) }))
  }

  const handleDelete = async (id) => {
    await api.deleteReminder(id)
    setData(prev => ({ ...prev, reminders: prev.reminders.filter(r => r.id !== id) }))
    loadTags()
  }

  const handleCreate = async (body) => {
    await api.createReminder(body)
    setShowAdd(false)
    loadReminders()
    loadTags()
  }

  return (
    <div className="app">
      <header className="header">
        <div className="filter-tabs">
          {[['all', 'Все'], ['today', 'Сегодня'], ['week', 'Неделя']].map(([val, label]) => (
            <button
              key={val}
              className={`tab ${filter === val ? 'active' : ''}`}
              onClick={() => setFilter(val)}
            >
              {label}
            </button>
          ))}
        </div>
        {tags.length > 0 && (
          <TagFilter tags={tags} activeTag={activeTag} onSelect={setActiveTag} />
        )}
      </header>

      <main className="main">
        {loading ? (
          <div className="empty">Загрузка…</div>
        ) : error ? (
          <div className="empty">{error}</div>
        ) : (
          <TodoList
            reminders={data.reminders}
            timezone={data.timezone}
            onDone={handleDone}
            onDelete={handleDelete}
          />
        )}
      </main>

      <button className="fab" onClick={() => setShowAdd(true)}>＋</button>

      {showAdd && (
        <AddTask onSubmit={handleCreate} onClose={() => setShowAdd(false)} />
      )}
    </div>
  )
}

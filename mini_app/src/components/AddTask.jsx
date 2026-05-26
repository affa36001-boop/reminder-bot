import { useState, useEffect, useCallback, useRef } from 'react'

const tg = window.Telegram?.WebApp

function nowPlusHour() {
  const d = new Date()
  d.setHours(d.getHours() + 1, 0, 0, 0)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:00`
}

export default function AddTask({ onSubmit, onClose }) {
  const [text, setText] = useState('')
  const [remindAt, setRemindAt] = useState(nowPlusHour)
  const [recurrence, setRecurrence] = useState('none')
  const [tag, setTag] = useState('')
  const [loading, setLoading] = useState(false)

  const stateRef = useRef()
  stateRef.current = { text, remindAt, recurrence, tag }

  const handleSubmit = useCallback(async () => {
    const { text, remindAt, recurrence, tag } = stateRef.current
    if (!text.trim() || !remindAt) return
    setLoading(true)
    try {
      await onSubmit({
        text: text.trim(),
        remind_at: remindAt,
        recurrence,
        tag: tag.trim() || null,
        pre_notify_minutes: 0,
      })
    } finally {
      setLoading(false)
    }
  }, [onSubmit])

  useEffect(() => {
    if (!tg) return
    const onMain = () => stateRef.current && handleSubmit()
    const onBack = () => onClose()

    tg.BackButton.show()
    tg.BackButton.onClick(onBack)
    tg.MainButton.setText('Сохранить')
    tg.MainButton.show()
    tg.MainButton.onClick(onMain)

    return () => {
      tg.BackButton.hide()
      tg.BackButton.offClick(onBack)
      tg.MainButton.hide()
      tg.MainButton.offClick(onMain)
    }
  }, [handleSubmit, onClose])

  return (
    <div className="overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="sheet">
        <div className="sheet-header">
          <h2>Новое напоминание</h2>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        <div className="form">
          <div className="form-field">
            <label>Текст</label>
            <textarea
              rows={3}
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="О чём напомнить?"
              autoFocus
            />
          </div>

          <div className="form-field">
            <label>Дата и время</label>
            <input
              type="datetime-local"
              value={remindAt}
              onChange={e => setRemindAt(e.target.value)}
            />
          </div>

          <div className="form-field">
            <label>Повтор</label>
            <select value={recurrence} onChange={e => setRecurrence(e.target.value)}>
              <option value="none">Без повтора</option>
              <option value="daily">Ежедневно</option>
              <option value="weekly">Еженедельно</option>
              <option value="monthly">Ежемесячно</option>
              <option value="yearly">Ежегодно</option>
            </select>
          </div>

          <div className="form-field">
            <label>Тег (необязательно)</label>
            <input
              type="text"
              value={tag}
              onChange={e => setTag(e.target.value.replace(/\s/g, '').replace(/^#/, ''))}
              placeholder="работа, здоровье, личное…"
            />
          </div>

          {!tg && (
            <button className="btn-submit" onClick={handleSubmit} disabled={loading || !text.trim()}>
              {loading ? 'Сохранение…' : 'Сохранить'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

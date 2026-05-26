import { useState } from 'react'

const REC_LABELS = {
  daily: '🔁 ежедневно',
  weekly: '🔁 еженедельно',
  monthly: '🔁 ежемесячно',
  yearly: '🔁 ежегодно',
}

export default function TodoItem({ reminder, timezone, onDone, onDelete }) {
  const [confirming, setConfirming] = useState(false)

  const fmt = new Intl.DateTimeFormat('ru-RU', {
    timeZone: timezone,
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(reminder.remind_at + 'Z'))

  return (
    <li className="todo-item">
      <div className="todo-body">
        <div className="todo-time">{fmt}</div>
        <div className="todo-text">{reminder.text}</div>
        <div className="todo-meta">
          {reminder.tag && <span className="todo-tag">#{reminder.tag}</span>}
          {reminder.recurrence !== 'none' && (
            <span className="todo-rec">
              {REC_LABELS[reminder.recurrence] ?? `🔁 ${reminder.recurrence}`}
            </span>
          )}
        </div>
      </div>

      <div className="todo-actions">
        <button className="btn-icon" onClick={() => onDone(reminder.id)} title="Выполнено">✅</button>
        {!confirming ? (
          <button className="btn-icon" onClick={() => setConfirming(true)} title="Удалить">🗑</button>
        ) : (
          <div className="confirm-row">
            <button className="btn-yes" onClick={() => onDelete(reminder.id)}>Да</button>
            <button className="btn-no" onClick={() => setConfirming(false)}>Нет</button>
          </div>
        )}
      </div>
    </li>
  )
}

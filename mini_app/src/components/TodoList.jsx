import TodoItem from './TodoItem.jsx'

function EmptyState({ filter, onAdd }) {
  const isToday = filter === 'today'

  return (
    <div className="empty-state">
      <div className="empty-icon" aria-hidden="true">
        {isToday ? (
          <svg width="72" height="72" viewBox="0 0 72 72" fill="none">
            <circle cx="36" cy="36" r="32" fill="currentColor" opacity="0.1"/>
            <path d="M22 36 L32 46 L50 28" stroke="currentColor" strokeWidth="3.5"
              strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        ) : (
          <svg width="72" height="72" viewBox="0 0 72 72" fill="none">
            <rect x="12" y="20" width="48" height="42" rx="8" fill="currentColor" opacity="0.08"/>
            <rect x="12" y="20" width="48" height="42" rx="8" stroke="currentColor" strokeWidth="2" opacity="0.35"/>
            <path d="M25 16 L25 26" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
            <path d="M47 16 L47 26" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
            <path d="M12 35 L60 35" stroke="currentColor" strokeWidth="1.5" opacity="0.25"/>
            <path d="M25 46 L47 46" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.4"/>
            <path d="M25 54 L40 54" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.4"/>
          </svg>
        )}
      </div>
      <p className="empty-text">
        {isToday
          ? <>Все дела сделаны!<br />Время отдыхать ✨</>
          : <>Здесь пока пусто.<br />Самое время запланировать<br />что-то важное!</>
        }
      </p>
      <button className="empty-cta" onClick={onAdd}>
        + Создать напоминание
      </button>
    </div>
  )
}

export default function TodoList({ reminders, timezone, onDone, onDelete, filter, onAdd }) {
  if (reminders.length === 0) {
    return <EmptyState filter={filter} onAdd={onAdd} />
  }
  return (
    <ul className="todo-list">
      {reminders.map(r => (
        <TodoItem
          key={r.id}
          reminder={r}
          timezone={timezone}
          onDone={onDone}
          onDelete={onDelete}
        />
      ))}
    </ul>
  )
}

import TodoItem from './TodoItem.jsx'

export default function TodoList({ reminders, timezone, onDone, onDelete }) {
  if (reminders.length === 0) {
    return <div className="empty">📭 Нет напоминаний</div>
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

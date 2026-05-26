export default function TagFilter({ tags, activeTag, onSelect }) {
  return (
    <div className="tag-filter">
      <button
        className={`tag-btn ${activeTag === null ? 'active' : ''}`}
        onClick={() => onSelect(null)}
      >
        Все
      </button>
      {tags.map(t => (
        <button
          key={t}
          className={`tag-btn ${activeTag === t ? 'active' : ''}`}
          onClick={() => onSelect(activeTag === t ? null : t)}
        >
          #{t}
        </button>
      ))}
    </div>
  )
}

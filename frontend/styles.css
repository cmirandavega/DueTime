import { useState } from 'react'

// Zero Data: the log lives in App state only. Closing the tab clears it.
// The user keeps their records by exporting a file to their own device.
export default function ServiceLog({ t, vehicle, items, setItems }) {
  const [draft, setDraft] = useState({ service: '', miles: '', declined: false })

  function add(e) {
    e.preventDefault()
    if (!draft.service.trim()) return
    setItems([...items, { ...draft, service: draft.service.trim(), source: 'manual' }])
    setDraft({ service: '', miles: '', declined: false })
  }

  function exportLog() {
    const services = items.map(({ source, ...x }) => ({ ...x, miles: x.miles ? Number(x.miles) : null }))
    const blob = new Blob([JSON.stringify({ vehicle, services }, null, 2)], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `duetime-${vehicle.year}-${vehicle.make}-${vehicle.model}.json`.toLowerCase().replace(/\s+/g, '-')
    a.click()
    URL.revokeObjectURL(a.href)
  }

  return (
    <section className="card">
      <h2>{t.log}</h2>
      <p className="muted">{t.logLead}</p>
      <form className="row log" onSubmit={add}>
        <input placeholder={t.logService} value={draft.service} onChange={(e) => setDraft({ ...draft, service: e.target.value })} />
        <input placeholder={t.logMiles} inputMode="numeric" value={draft.miles}
          onChange={(e) => setDraft({ ...draft, miles: e.target.value.replace(/[^\d]/g, '') })} />
        <label className="inline"><input type="checkbox" checked={draft.declined} onChange={(e) => setDraft({ ...draft, declined: e.target.checked })} /> {t.logDeclined}</label>
        <button className="btn small">{t.logAdd}</button>
      </form>
      {items.length > 0 && (
        <>
          <ul className="list">
            {items.map((x, i) => (
              <li key={i}>
                {x.service}
                {x.miles ? ` · ~${Number(x.miles).toLocaleString()} mi` : ''}
                {x.declined && <span className="pill overdue"> {t.logDeclined}</span>}
              </li>
            ))}
          </ul>
          <button className="btn ghost" onClick={exportLog}>{t.logExport}</button>
        </>
      )}
    </section>
  )
}

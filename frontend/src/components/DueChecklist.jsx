import { useState } from 'react'

const usd = (n) => (n == null ? '—' : `$${Number(n).toLocaleString()}`)
const range = (r) => (Array.isArray(r) && r.length === 2 ? `${usd(r[0])}–${usd(r[1])}` : '—')

// Zero Data: checked state lives only in this component. Nothing is saved.
export default function DueChecklist({ items, t }) {
  const [done, setDone] = useState({})
  const toggle = (s) => setDone((d) => ({ ...d, [s]: !d[s] }))
  const left = items.filter((d) => !done[d.service]).length
  const allDone = left === 0

  return (
    <section className={`card ${allDone ? 'good' : 'alert'}`}>
      <h2>{t.dueTitle}</h2>
      <p className="muted">{allDone ? t.dueAllDone : t.dueLeft(left, items.length)}</p>
      <ul className="due">
        {items.map((d) => {
          const isDone = !!done[d.service]
          return (
            <li key={d.service} className={isDone ? 'done' : ''}>
              <label>
                <input type="checkbox" checked={isDone} onChange={() => toggle(d.service)} />
                <span>
                  <strong>{d.service}</strong>
                  {isDone ? (
                    <span className="pill">{t.dueDone}</span>
                  ) : (
                    <>
                      <p>{d.risk_if_ignored}</p>
                      <p className="costs">
                        <span>{t.ifIgnored}: {range(d.cost_if_ignored_usd)}</span>
                        <span>{t.doNow}: {range(d.cost_to_do_now_usd)}</span>
                      </p>
                    </>
                  )}
                </span>
              </label>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
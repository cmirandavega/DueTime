const usd = (n) => (n == null ? '—' : `$${Number(n).toLocaleString()}`)
const range = (r) => (Array.isArray(r) && r.length === 2 ? `${usd(r[0])}–${usd(r[1])}` : '—')

// Checked items live in the shared service log (App state). Nothing is saved anywhere.
export default function DueChecklist({ items, t, log = [], setLog = () => {} }) {
  const entry = (service) => log.find((x) => x.source === 'checklist' && x.service === service)

  function toggle(service) {
    if (entry(service)) setLog(log.filter((x) => !(x.source === 'checklist' && x.service === service)))
    else setLog([...log, { service, miles: '', declined: false, source: 'checklist' }])
  }

  const setMiles = (service, miles) =>
    setLog(log.map((x) => (x.source === 'checklist' && x.service === service ? { ...x, miles } : x)))

  const left = items.filter((d) => !entry(d.service)).length
  const allDone = left === 0

  return (
    <section className={`card ${allDone ? 'good' : 'alert'}`}>
      <h2>{t.dueTitle}</h2>
      <p className="muted">{allDone ? t.dueAllDone : t.dueLeft(left, items.length)}</p>
      <ul className="due">
        {items.map((d) => {
          const e = entry(d.service)
          return (
            <li key={d.service} className={e ? 'done' : ''}>
              <label>
                <input type="checkbox" checked={!!e} onChange={() => toggle(d.service)} />
                <span>
                  <strong>{d.service}</strong>
                  {!e && (
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
              {e && (
                <div className="when">
                  <span className="pill">{t.dueDone}</span>
                  <input inputMode="numeric" placeholder={t.dueMilesPlaceholder} aria-label={t.dueMilesLabel}
                    value={e.miles} onChange={(ev) => setMiles(d.service, ev.target.value.replace(/[^\d]/g, ''))} />
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}

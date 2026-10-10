import { useState } from 'react'
import { diagnose } from '../api.js'

export default function SymptomCard({ t, vehicle, lang }) {
  const [symptom, setSymptom] = useState('')
  const [res, setRes] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit(e) {
    e.preventDefault()
    if (symptom.trim().length < 3) return
    setLoading(true); setError('')
    try {
      setRes(await diagnose({ vehicle, symptom: symptom.trim(), lang }))
    } catch (err) {
      setError(err.message || t.error)
    } finally { setLoading(false) }
  }

  return (
    <section className="card">
      <h2>{t.symptomTitle}</h2>
      <form onSubmit={submit}>
        <textarea rows="3" value={symptom} maxLength={500} placeholder={t.symptomPlaceholder}
          onChange={(e) => setSymptom(e.target.value)} />
        <button className="btn" disabled={loading}>{loading ? t.searching : t.symptomGo}</button>
      </form>
      {error && <p className="error">{error}</p>}

      {res && (
        <div className="diagnosis">
          {res.stop_driving && (
            <p className="stop">{t.stopDriving}{res.stop_reason ? ` ${res.stop_reason}` : ''}</p>
          )}
          {res.note && <p className="muted">{res.note}</p>}
          <ol className="list">
            {res.causes?.map((c) => (
              <li key={c.cause}>
                <strong>{c.cause}</strong> <span className="pill">{t.who[c.who] || c.who}</span>
                <p>{c.how_to_confirm}</p>
                {c.nhtsa_complaints ? <p className="flag">{t.reportedByOwners(c.nhtsa_complaints)}</p> : null}
              </li>
            ))}
          </ol>
          {res.sources?.length > 0 && (
            <>
              <h3>{t.sources}</h3>
              <ul className="sources">
                {res.sources.map((s) => (
                  <li key={s.url}><a href={s.url} target="_blank" rel="noopener noreferrer">{s.title}</a></li>
                ))}
              </ul>
            </>
          )}
          {/* Google's terms require showing Search Suggestions with grounded results. */}
          {res.search_suggestions_html && (
            <div className="suggestions" dangerouslySetInnerHTML={{ __html: res.search_suggestions_html }} />
          )}
          <p className="muted small">{t.diagnoseDisclaimer}</p>
        </div>
      )}
    </section>
  )
}

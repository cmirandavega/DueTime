import { useState } from 'react'
import { strings } from './i18n.js'
import { getReport, usingSample } from './api.js'
import CarForm from './components/CarForm.jsx'
import Report from './components/Report.jsx'
import ServiceLog from './components/ServiceLog.jsx'
import SymptomCard from './components/SymptomCard.jsx'

export default function App() {
  const [lang, setLang] = useState('en')
  const [report, setReport] = useState(null)
  const [query, setQuery] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const t = strings[lang]

  async function run(q, language = lang) {
    setQuery(q)
    setLoading(true)
    setError('')
    try {
      setReport(await getReport({ ...q, lang: language }))
    } catch (e) {
      setError(e.message || t.error)
    } finally {
      setLoading(false)
    }
  }

  function switchLang(next) {
    setLang(next)
    if (query) run(query, next) // re-fetch so report text comes back translated
  }

  return (
    <div className="app">
      <header className="top">
        <div className="brand">
          <img src="/icon.svg" alt="" width="32" height="32" />
          <div>
            <h1>DueTime</h1>
            <p className="muted">{t.tagline}</p>
          </div>
        </div>
        <div className="lang" role="group" aria-label="Language">
          <button className={lang === 'en' ? 'on' : ''} onClick={() => switchLang('en')}>EN</button>
          <button className={lang === 'es' ? 'on' : ''} onClick={() => switchLang('es')}>ES</button>
        </div>
      </header>

      {usingSample && <p className="notice">{t.sample}</p>}

      <CarForm t={t} onSubmit={run} loading={loading} />
      {error && <p className="error">{error}</p>}
      {report && <Report report={report} t={t} />}
      {report && <SymptomCard t={t} vehicle={report.vehicle} lang={lang} />}
      {report && <ServiceLog t={t} vehicle={report.vehicle} />}

      <footer className="muted">{t.privacy}</footer>
    </div>
  )
}

import { useState } from 'react'
import { decodeVin, vinFromPhoto, usingSample } from '../api.js'

// One-tap demo cars for the pitch. Match backend/scripts/demo_cars.json.
const DEMO = [
  { label: "'01 Integra", year: 2001, make: 'ACURA', model: 'INTEGRA', mileage: 168000, mode: 'own' },
  { label: "'13 Altima", year: 2013, make: 'NISSAN', model: 'ALTIMA', mileage: 110000, askingPrice: 4500, mode: 'buy' },
  { label: "'04 330Ci", year: 2004, make: 'BMW', model: '3 SERIES', mileage: 150000, mode: 'own' }
]

export default function CarForm({ t, onSubmit, loading }) {
  const [mode, setMode] = useState('own')
  const [f, setF] = useState({ vin: '', year: '', make: '', model: '', mileage: '', askingPrice: '' })
  const [busy, setBusy] = useState('')
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  async function fillFromVin(vin) {
    if (usingSample || vin.length !== 17) return
    setBusy('vin')
    try {
      const v = await decodeVin(vin)
      setF((cur) => ({ ...cur, vin, year: v.year ?? cur.year, make: v.make ?? cur.make, model: v.model ?? cur.model }))
    } finally { setBusy('') }
  }

  async function onPhoto(e) {
    const file = e.target.files?.[0]
    if (!file || usingSample) return
    setBusy('photo')
    try {
      const v = await vinFromPhoto(file)
      setF((cur) => ({ ...cur, vin: v.vin, year: v.year ?? cur.year, make: v.make ?? cur.make, model: v.model ?? cur.model }))
    } catch (err) {
      alert(err.message)
    } finally { setBusy(''); e.target.value = '' }
  }

  function submit(e) {
    e.preventDefault()
    onSubmit({ ...f, mode })
  }

  function demo(d) {
    setMode(d.mode)
    setF({ vin: '', year: d.year, make: d.make, model: d.model, mileage: d.mileage, askingPrice: d.askingPrice ?? '' })
    onSubmit({ ...d, mode: d.mode })
  }

  return (
    <form className="card form" onSubmit={submit}>
      <div className="seg" role="group">
        <button type="button" className={mode === 'own' ? 'on' : ''} onClick={() => setMode('own')}>{t.own}</button>
        <button type="button" className={mode === 'buy' ? 'on' : ''} onClick={() => setMode('buy')}>{t.buy}</button>
      </div>

      <label>{t.vin}
        <input value={f.vin} maxLength={17} autoCapitalize="characters"
          onChange={(e) => { const v = e.target.value.toUpperCase(); setF({ ...f, vin: v }); fillFromVin(v) }} />
      </label>
      <label className="photo">
        <input type="file" accept="image/*" capture="environment" onChange={onPhoto} hidden />
        <span className="btn ghost">{busy === 'photo' ? '…' : t.vinPhoto}</span>
      </label>

      <p className="or muted">{t.or}</p>
      <div className="row">
        <label>{t.year}<input inputMode="numeric" value={f.year} onChange={set('year')} required /></label>
        <label>{t.make}<input value={f.make} onChange={set('make')} required /></label>
      </div>
      <div className="row">
        <label>{t.model}<input value={f.model} onChange={set('model')} required /></label>
        <label>{t.mileage}<input inputMode="numeric" value={f.mileage} onChange={set('mileage')} /></label>
      </div>
      {mode === 'buy' && (
        <label>{t.askingPrice}<input inputMode="numeric" value={f.askingPrice} onChange={set('askingPrice')} /></label>
      )}

      <button className="btn" disabled={loading || busy === 'vin'}>{loading ? t.checking : t.check}</button>

      <div className="demo">
        {DEMO.map((d) => <button type="button" key={d.label} className="chip" onClick={() => demo(d)}>{d.label}</button>)}
      </div>
    </form>
  )
}

import sample from './mock/sample-report.json'
import sampleDiagnosis from './mock/sample-diagnosis.json'

const API = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
export const usingSample = !API || new URLSearchParams(location.search).has('mock')

async function json(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || res.statusText)
  }
  return res.json()
}

export async function getReport({ year, make, model, mileage, askingPrice, mode, lang, vin }) {
  if (usingSample) return { ...sample, mode, language: lang }
  const params = new URLSearchParams({ year, make, model, mode, lang })
  if (mileage) params.set('mileage', mileage)
  if (askingPrice) params.set('asking_price', askingPrice)
  if (vin) params.set('vin', vin)
  return json(await fetch(`${API}/api/report?${params}`))
}

export async function diagnose({ vehicle, symptom, lang }) {
  if (usingSample) return sampleDiagnosis
  return json(await fetch(`${API}/api/diagnose`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ year: vehicle.year, make: vehicle.make, model: vehicle.model, mileage: vehicle.mileage, symptom, lang })
  }))
}

export async function decodeVin(vin) {
  return json(await fetch(`${API}/api/vin/${encodeURIComponent(vin)}`))
}

export async function vinFromPhoto(file) {
  const form = new FormData()
  form.append('photo', file)
  return json(await fetch(`${API}/api/vin-photo`, { method: 'POST', body: form }))
}

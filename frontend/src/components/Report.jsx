import DueChecklist from './DueChecklist.jsx'

const usd = (n) => (n == null ? '—' : `$${Number(n).toLocaleString()}`)
const range = (r) => (Array.isArray(r) && r.length === 2 ? `${usd(r[0])}–${usd(r[1])}` : '—')
const miles = (n) => (n == null ? '—' : `${Number(n).toLocaleString()} mi`)

function Card({ title, lead, tone, children }) {
  return (
    <section className={`card ${tone || ''}`}>
      <h2>{title}</h2>
      {lead && <p className="muted">{lead}</p>}
      {children}
    </section>
  )
}

export default function Report({ report: r, t }) {
  const v = r.vehicle
  const pre = r.pre_purchase || {}
  const p = r.price_check || {}

  return (
    <div className="report">
      <section className="card hero">
        <p className="muted">{v.year} {v.make} {v.model}{v.mileage ? ` · ${miles(v.mileage)}` : ''}</p>
        <p className="summary">{r.summary}</p>
      </section>

        {r.declined_services?.length > 0 && <DueChecklist items={r.declined_services} t={t} />}

      <Card title={t.recalls}>
        {r.recalls?.length ? (
          <ul className="list">
            {r.recalls.map((x) => (
              <li key={x.campaign}>
                <span className={`pill ${x.risk}`}>{x.component}</span>
                <p>{x.summary_plain}</p>
                <p className="muted">{x.remedy_plain}</p>
              </li>
            ))}
          </ul>
        ) : <p className="muted">{t.noRecalls}</p>}
      </Card>

      {r.known_problems?.length > 0 && (
        <Card title={t.knownProblems}>
          <ul className="list">
            {r.known_problems.map((k) => (
              <li key={k.component} className={k.in_range ? 'hot' : ''}>
                <strong>{k.component}</strong>
                <p className="muted">
                  {k.complaint_count != null && `${k.complaint_count} ${t.complaints}`}
                  {k.typical_mileage?.median ? ` · ${t.typically} ${miles(k.typical_mileage.median)}` : ''}
                </p>
                {k.in_range && <p className="flag">{t.inRange}</p>}
                {k.explanation && <p>{k.explanation}</p>}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {r.maintenance_due?.length > 0 && (
        <Card title={t.maintenance}>
          <ul className="list">
            {r.maintenance_due.map((m) => (
              <li key={m.service}>
                <span className={`pill ${m.status}`}>{t.status[m.status] || m.status}</span> <strong>{m.service}</strong>
                <p>{m.why}</p>
                {m.verify && <p className="muted small">{t.verify}</p>}
              </li>
            ))}
          </ul>
        </Card>
      )}

      {r.diy_cards?.length > 0 && (
        <Card title={t.diy}>
          {r.diy_cards.map((d) => (
            <div className="diy" key={d.job}>
              <strong>{d.job}</strong> <span className={`pill ${d.difficulty}`}>{d.difficulty}</span>
              <dl>
                <dt>{t.time}</dt><dd>{d.time_hours?.join('–')} h</dd>
                <dt>{t.parts}</dt><dd>{range(d.parts_cost_usd)}</dd>
                <dt>{t.shop}</dt><dd>{range(d.shop_cost_usd)}</dd>
                <dt>{t.tools}</dt><dd>{d.tools?.join(', ')}</dd>
              </dl>
              {d.safety_note && <p className="flag">{d.safety_note}</p>}
            </div>
          ))}
        </Card>
      )}

      {r.mode === 'buy' && (
        <Card title={t.prePurchase}>
          {[['inspect', t.inspect], ['should_be_done', t.shouldBeDone], ['ask_seller', t.askSeller]].map(([k, label]) =>
            pre[k]?.length ? (
              <div key={k}>
                <h3>{label}</h3>
                <ul className="checks">{pre[k].map((x) => <li key={x}><label><input type="checkbox" /> {x}</label></li>)}</ul>
              </div>
            ) : null
          )}
        </Card>
      )}

      {(r.mode === 'buy' || p.comps > 0) && (
        <Card title={t.price}>
          <p className={`verdict ${p.verdict}`}>{t.verdicts[p.verdict] || p.verdict}</p>
          {p.median != null && (
            <p className="muted">{t.median}: {usd(p.median)} ({usd(p.p25)}–{usd(p.p75)}) · {p.comps} {t.comps}</p>
          )}
        </Card>
      )}

      <ul className="muted small disclaimers">{r.disclaimers?.map((d) => <li key={d}>{d}</li>)}</ul>
    </div>
  )
}

import { useEffect, useMemo, useState } from 'react'

export default function App() {
  const [leads, setLeads] = useState(null)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('all')
  const [expandedId, setExpandedId] = useState(null)

  useEffect(() => {
    fetch('/leads.json')
      .then((res) => {
        if (!res.ok) throw new Error('leads.json not found')
        return res.json()
      })
      .then(setLeads)
      .catch((err) => setError(err.message))
  }, [])

  const filtered = useMemo(() => {
    if (!leads) return []
    return leads.filter((lead) => {
      const matchesFilter = filter === 'all' || lead.category === filter
      const q = query.trim().toLowerCase()
      const matchesQuery =
        q === '' ||
        lead.name.toLowerCase().includes(q) ||
        (lead.focus_area || '').toLowerCase().includes(q) ||
        (lead.subtype || '').toLowerCase().includes(q)
      return matchesFilter && matchesQuery
    })
  }, [leads, query, filter])

  const counts = useMemo(() => {
    if (!leads) return { all: 0, funder: 0, partner: 0 }
    return {
      all: leads.length,
      funder: leads.filter((l) => l.category === 'funder').length,
      partner: leads.filter((l) => l.category === 'partner').length,
    }
  }, [leads])

  if (error) {
    return (
      <div className="state-message">
        <p><strong>Couldn't load leads.json</strong></p>
        <p>
          Run <code>python export_leads.py</code> in your project folder,
          then copy the resulting <code>leads.json</code> into{' '}
          <code>affa-ui/public/leads.json</code> and refresh.
        </p>
      </div>
    )
  }

  if (!leads) {
    return <div className="state-message">Loading leads…</div>
  }

  return (
    <div className="page">
      <header className="hero">
        <div className="eyebrow">A Farm For All &middot; Growth Pipeline</div>
        <h1>Funding &amp; Partnership CRM</h1>
        <p className="subhead">
          {counts.all} leads researched, organized, and ready for outreach —
          built by a coordinated team of AI agents.
        </p>
      </header>

      <div className="toolbar">
        <div className="filters">
          <button
            className={filter === 'all' ? 'chip active' : 'chip'}
            onClick={() => setFilter('all')}
          >
            All <span className="chip-count">{counts.all}</span>
          </button>
          <button
            className={filter === 'funder' ? 'chip active chip-funder' : 'chip'}
            onClick={() => setFilter('funder')}
          >
            Funders <span className="chip-count">{counts.funder}</span>
          </button>
          <button
            className={filter === 'partner' ? 'chip active chip-partner' : 'chip'}
            onClick={() => setFilter('partner')}
          >
            Partners <span className="chip-count">{counts.partner}</span>
          </button>
        </div>
        <input
          className="search"
          type="text"
          placeholder="Search by name or focus area…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Organization</th>
              <th>Category</th>
              <th>Type</th>
              <th>Focus Area</th>
              <th>Outreach</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((lead) => {
              const isOpen = expandedId === lead.id
              const hasMessage = lead.outreach_message && lead.outreach_message.trim() !== ''
              return (
                <>
                  <tr
                    key={lead.id}
                    className={isOpen ? 'row row-open' : 'row'}
                    onClick={() => setExpandedId(isOpen ? null : lead.id)}
                  >
                    <td className="name-cell">
                      {lead.name}
                      {lead.url && (
                        <a
                          href={lead.url}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="link-out"
                        >
                          ↗
                        </a>
                      )}
                    </td>
                    <td>
                      <span className={`tag tag-${lead.category}`}>{lead.category}</span>
                    </td>
                    <td className="muted">{lead.subtype || '—'}</td>
                    <td className="focus-cell">{lead.focus_area}</td>
                    <td>
                      {hasMessage ? (
                        <span className="status-drafted">
                          {isOpen ? 'Hide ▲' : 'View ▾'}
                        </span>
                      ) : (
                        <span className="status-pending">Not drafted</span>
                      )}
                    </td>
                  </tr>
                  {isOpen && hasMessage && (
                    <tr className="detail-row" key={`${lead.id}-detail`}>
                      <td colSpan={5}>
                        <div className="detail-box">
                          <div className="detail-label">Drafted outreach message</div>
                          <p className="detail-message">{lead.outreach_message}</p>
                          {lead.fit_reason && (
                            <>
                              <div className="detail-label">Why this fit was flagged</div>
                              <p className="detail-fit">{lead.fit_reason}</p>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              )
            })}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <div className="empty-state">No leads match your search.</div>
        )}
      </div>
    </div>
  )
}

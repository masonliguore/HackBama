import { useMemo, useState } from 'react'
import Plot from 'react-plotly.js'
import { Activity, ArrowDownRight, ArrowUpRight, Gauge, LayoutDashboard, Settings2, Wind } from 'lucide-react'

type CardProps = { label: string; value: string; unit: string; change: string; positive?: boolean }
function MetricCard({ label, value, unit, change, positive = true }: CardProps) {
  return <article className="metric-card"><div className="metric-top"><span>{label}</span><Activity size={17} /></div><div className="metric-value">{value}<small> {unit}</small></div><div className={positive ? 'trend good' : 'trend warn'}>{positive ? <ArrowUpRight size={15} /> : <ArrowDownRight size={15} />}{change}</div></article>
}

export default function App() {
  const [mass, setMass] = useState(1200)
  const [force, setForce] = useState(2400)
  const [range, setRange] = useState(12)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const acceleration = force / mass
  const times = useMemo(() => Array.from({ length: 25 }, (_, i) => i * range / 24), [range])
  const velocity = times.map(t => acceleration * t)
  const distance = times.map(t => 0.5 * acceleration * t * t)

  function refresh(simulateFailure = false) {
    setLoading(true); setError('')
    window.setTimeout(() => {
      if (simulateFailure) setError('Sample data could not be loaded. Check the source, then retry.')
      else if (mass <= 0 || force < 0 || range <= 0) setError('Use a positive mass and duration, and a non-negative force.')
      setLoading(false)
    }, 350)
  }

  return <div className="shell">
    <aside className="sidebar"><div className="brand"><span className="brand-mark"><Wind size={19} /></span><span>fieldnote<small>ENGINEERING STUDIO</small></span></div><div className="nav-label">WORKSPACE</div><a className="nav-item active" href="#overview"><LayoutDashboard size={17} /> Overview</a><a className="nav-item" href="#simulation"><Gauge size={17} /> Simulations</a><a className="nav-item" href="#parameters"><Settings2 size={17} /> Parameters</a><div className="sidebar-bottom"><span className="status-dot" /> Local simulation <span className="version">v1.0</span></div></aside>
    <main className="main"><header className="topbar"><div><div className="eyebrow">ENGINEERING / MOTION LAB</div><h1>System overview</h1></div><div className="actions"><button className="error-preview" onClick={() => refresh(true)}>Preview error state</button><button className="refresh" onClick={() => refresh()}>{loading ? 'Calculating…' : 'Recalculate'}</button></div></header>
      <div className="sim-banner"><span className="sim-icon">i</span><div><strong>SIMULATED EXAMPLE</strong><span>Deterministic sample data · No live sensors or vehicle data connected</span></div><span className="live-tag"><span className="status-dot" /> LOCAL</span></div>
      <section className="section-head"><div><h2>Performance snapshot</h2><p>Constant-force motion model · Starts from rest, drag excluded</p></div><span className="updated">Updated just now</span></section>
      {error && <div className="error" role="alert">{error} <button onClick={() => refresh()}>Retry</button></div>}
      {loading ? <div className="loading">Updating the simulation…</div> : <>
        <section className="metrics" id="overview"><MetricCard label="Acceleration" value={acceleration.toFixed(2)} unit="m/s²" change="Calculated from inputs" /><MetricCard label="Final velocity" value={(acceleration * range).toFixed(1)} unit="m/s" change={`At ${range}s`} /><MetricCard label="Distance traveled" value={(0.5 * acceleration * range * range).toFixed(1)} unit="m" change="Numerical model" positive={false} /></section>
        <section className="panel" id="simulation"><div className="panel-head"><div><h2>Motion over time</h2><p>Velocity and distance from the selected input values</p></div><span className="chart-legend"><i className="blue-key" /> Velocity <i className="orange-key" /> Distance</span></div><Plot data={[{ x: times, y: velocity, type: 'scatter', mode: 'lines', name: 'Velocity (m/s)', line: { color: '#247ba0', width: 3 }, yaxis: 'y' }, { x: times, y: distance, type: 'scatter', mode: 'lines', name: 'Distance (m)', line: { color: '#e08b55', width: 3 }, yaxis: 'y2' }]} layout={{ autosize: true, height: 290, margin: { l: 48, r: 48, t: 12, b: 42 }, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', font: { family: 'Inter, sans-serif', color: '#687781', size: 11 }, xaxis: { title: { text: 'Time (s)' }, gridcolor: '#edf1f3', zeroline: false }, yaxis: { title: { text: 'Velocity (m/s)' }, gridcolor: '#edf1f3', zeroline: false }, yaxis2: { title: { text: 'Distance (m)' }, overlaying: 'y', side: 'right', showgrid: false, zeroline: false }, showlegend: false }} config={{ displayModeBar: false, responsive: true, showSendToCloud: false }} useResizeHandler style={{ width: '100%' }} />
        </section>
        <section className="panel controls" id="parameters"><div className="panel-head"><div><h2>Model parameters</h2><p>Change an input and recalculate to explore the response</p></div><span className="input-tag">INTERACTIVE INPUTS</span></div><div className="control-grid"><label>Mass <span>{mass} kg</span><input type="range" min="100" max="3000" step="50" value={mass} onChange={e => setMass(Number(e.target.value))} /></label><label>Applied force <span>{force} N</span><input type="range" min="0" max="12000" step="100" value={force} onChange={e => setForce(Number(e.target.value))} /></label><label>Time range <span>{range} s</span><input type="range" min="2" max="30" step="1" value={range} onChange={e => setRange(Number(e.target.value))} /></label></div></section>
      </>}
      <footer>FIELDNOTE ENGINEERING <span>Sample interface · All values are illustrative</span></footer>
    </main>
  </div>
}

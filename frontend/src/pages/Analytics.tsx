import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, ArrowUpRight, ChartNoAxesCombined, CreditCard, DollarSign, RefreshCw, ShieldAlert, Users } from "lucide-react";
import { Area, AreaChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { count, money, percent, useResource } from "../api";
import { Badge, DataTable, Heading, Metric, Panel, Status } from "../components";
import type { CustomerRisk, Overview, TransactionStats, Trend, User } from "../types";

function Trends({ days }: { days: number }) {
  const resource = useResource<Trend[]>(`/api/analytics/trends?days=${days}`);
  return <Panel title="Transaction activity" description={`Daily transaction volume over the last ${days} days`} action={<span className="chart-key"><span className="dot" />Transaction volume</span>}>
    <Status {...resource} retry={resource.refresh} />
    {resource.data && (resource.data.length ? <div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={resource.data} margin={{ top: 15, right: 15, left: 0, bottom: 0 }}><defs><linearGradient id="volumeFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#159b82" stopOpacity={0.2} /><stop offset="100%" stopColor="#159b82" stopOpacity={0} /></linearGradient></defs><CartesianGrid strokeDasharray="4 5" vertical={false} stroke="#e8edf3" /><XAxis dataKey="date" tickFormatter={(date: string) => new Date(`${date}T00:00:00`).toLocaleDateString("en-US", { month: "short", day: "numeric" })} tick={{ fontSize: 11, fill: "#8290a4" }} axisLine={false} tickLine={false} minTickGap={35} /><YAxis tickFormatter={(value: number) => `$${value >= 1000 ? `${(value / 1000).toFixed(0)}k` : value}`} tick={{ fontSize: 11, fill: "#8290a4" }} axisLine={false} tickLine={false} width={65} /><Tooltip formatter={(value) => money(Number(value))} contentStyle={{ borderRadius: 10, borderColor: "#e8edf3" }} /><Area type="monotone" dataKey="total_volume" name="Volume" stroke="#159b82" fill="url(#volumeFill)" strokeWidth={2.5} /></AreaChart></ResponsiveContainer></div> : <div className="state">No transactions in this date range.</div>)}
  </Panel>;
}

function RiskDistribution({ stats }: { stats: TransactionStats }) {
  const distribution = [
    { name: "Low risk", value: stats.low_risk_transactions, color: "#149d85" },
    { name: "Medium risk", value: stats.medium_risk_transactions, color: "#edb04c" },
    { name: "High risk", value: stats.high_risk_transactions, color: "#ec7583" },
    { name: "Unassessed", value: Math.max(0, stats.total_transactions - stats.low_risk_transactions - stats.medium_risk_transactions - stats.high_risk_transactions), color: "#cbd5e1" },
  ];
  return <Panel title="Risk distribution" description="Assessed and unassessed transactions">
    <div className="donut-wrap"><div className="donut-label"><strong>{count(stats.total_transactions)}</strong><span>total transactions</span></div><ResponsiveContainer width="100%" height={225}><PieChart><Pie data={distribution} dataKey="value" innerRadius={77} outerRadius={99} paddingAngle={3} stroke="none">{distribution.map((item) => <Cell key={item.name} fill={item.color} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></div>
    <div className="legend">{distribution.map((item) => <div key={item.name}><span><i style={{ backgroundColor: item.color }} />{item.name}</span><strong>{count(item.value)}</strong><small>{stats.total_transactions ? percent(item.value / stats.total_transactions) : "0.0%"}</small></div>)}</div>
  </Panel>;
}

export function OverviewPage({ user }: { user: User }) {
  const resource = useResource<Overview>("/api/analytics/dashboard");
  const stats = useResource<TransactionStats>("/api/analytics/transactions?days=30");
  const canReview = user.role !== "viewer";
  return <>
    <Heading eyebrow="THE BIG PICTURE" title="Risk operations overview" description={`Welcome back, ${user.full_name.split(" ")[0]}. Here is your financial risk snapshot.`}>
      <span className="date-chip">Last 30 days</span><button className="button secondary" onClick={() => { resource.refresh(); stats.refresh(); }}><RefreshCw size={16} />Refresh metrics</button>
    </Heading>
    <div className="overview-banner"><div className="banner-icon"><ShieldAlert size={24} /></div><div><strong>Clarity across every transaction.</strong><p>Monitor the signals. Investigate what matters. Keep your decisions explainable.</p></div><Link to={canReview ? "/alerts" : "/analytics"}>{canReview ? "Open review queue" : "Explore risk analytics"}<ArrowRight size={17} /></Link></div>
    <Status {...resource} retry={resource.refresh} /><Status {...stats} retry={stats.refresh} />
    {resource.data && stats.data && <>
      <div className="metrics-grid">
        <Metric title="Total transactions" value={count(stats.data.total_transactions)} note="Transactions in the last 30 days" icon={<CreditCard size={18} />} />
        <Metric title="Transaction volume" value={money(stats.data.total_volume)} note={`Average transaction ${money(stats.data.average_amount)}`} icon={<DollarSign size={18} />} />
        <Metric title="High-risk transactions" value={count(stats.data.high_risk_transactions)} note="Flagged by risk assessment" icon={<ShieldAlert size={18} />} />
        <Metric title="Pending alerts" value={count(resource.data.pending_alerts)} note={`${count(resource.data.under_review_alerts)} currently under review`} icon={<ChartNoAxesCombined size={18} />} />
      </div>
      <div className="chart-grid"><Trends days={30} /><RiskDistribution stats={stats.data} /></div>
      <div className="two-columns"><Panel title="Investigation snapshot" description="A focused view of your review workflow"><div className="insight-row"><span className="insight-icon"><ShieldAlert size={20} /></span><div><strong>{count(resource.data.total_alerts)} alerts raised</strong><p>Across the last 30 days</p></div>{canReview && <Link className="text-button" to="/alerts">Review <ArrowUpRight size={16} /></Link>}</div><div className="insight-row"><span className="insight-icon purple"><Users size={20} /></span><div><strong>Prioritize customer risk</strong><p>Review profiles and suspicious patterns</p></div><Link className="text-button" to="/analytics">Explore <ArrowUpRight size={16} /></Link></div></Panel>
        <Panel title="Make your models measurable" description="Build a transparent fraud detection workflow"><div className="studio-promo"><div className="eyebrow">MODEL STUDIO</div><h3>Train. Evaluate. Understand.</h3><p>Compare saved metrics, inspect feature importance, and train evaluation models from labeled data.</p><Link className="button primary" to="/models">Open model studio<ArrowRight size={16} /></Link></div></Panel></div>
    </>}
  </>;
}

export function RiskPage() {
  const [days, setDays] = useState(30);
  const stats = useResource<TransactionStats>(`/api/analytics/transactions?days=${days}`);
  const customers = useResource<{ high_risk_customers: CustomerRisk[] }>("/api/analytics/customers?limit=20");
  const anomalies = useResource<{ type: string; severity: string; description: string }[]>("/api/analytics/anomalies");
  return <>
    <Heading eyebrow="CONNECT THE SIGNALS" title="Risk analytics" description="Understand exposure, customer behavior, and emerging anomalies."><label className="inline-label">Period<select value={days} onChange={(event) => setDays(Number(event.target.value))}><option value={7}>Last 7 days</option><option value={30}>Last 30 days</option><option value={90}>Last 90 days</option></select></label></Heading>
    <Status {...stats} retry={stats.refresh} />
    {stats.data && <><div className="metrics-grid"><Metric title="Total volume" value={money(stats.data.total_volume)} note={`Last ${days} days`} icon={<DollarSign size={18} />} /><Metric title="Average amount" value={money(stats.data.average_amount)} note="Per transaction" icon={<CreditCard size={18} />} /><Metric title="High risk" value={count(stats.data.high_risk_transactions)} note="Assessed high-risk transactions" icon={<ShieldAlert size={18} />} /><Metric title="Low risk" value={count(stats.data.low_risk_transactions)} note="Assessed low-risk transactions" icon={<ChartNoAxesCombined size={18} />} /></div><div className="chart-grid"><Trends days={days} /><RiskDistribution stats={stats.data} /></div></>}
    <Panel title="Customer risk profiles" description="Top profiles returned by the risk service (all-time customer history)">
      <Status {...customers} retry={customers.refresh} />{customers.data && <DataTable rows={customers.data.high_risk_customers} rowKey={(row) => row.customer_id} columns={[
        { title: "Customer", cell: (row) => <strong>Customer #{row.customer_id}</strong> },
        { title: "Transactions", cell: (row) => count(row.total_transactions) },
        { title: "High risk", cell: (row) => count(row.high_risk_count) },
        { title: "Fraud rate", cell: (row) => `${row.fraud_rate.toFixed(1)}%` },
        { title: "Avg. amount", cell: (row) => money(row.average_transaction_amount) },
        { title: "Profile", cell: (row) => <Badge value={row.risk_profile} /> },
        { title: "Patterns", cell: (row) => row.suspicious_patterns.join(", ") || "None detected" },
      ]} />}
    </Panel>
    <Panel title="Recent anomaly signals" description="Activity detected by the analytics service over its recent lookback window"><Status {...anomalies} retry={anomalies.refresh} />{anomalies.data && <DataTable rows={anomalies.data} rowKey={(row) => `${row.type}-${row.description}`} columns={[{ title: "Signal", cell: (row) => row.type.replaceAll("_", " ") }, { title: "Severity", cell: (row) => <Badge value={row.severity} /> }, { title: "Observation", cell: (row) => row.description }]} />}</Panel>
  </>;
}

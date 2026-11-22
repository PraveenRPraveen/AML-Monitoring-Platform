import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Tooltip, Legend } from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Tooltip, Legend);

const API = '/api/v1';
const sections = ['Overview','Transactions','Fraud Alerts','AML Monitoring','Cases','Analytics','Audit'];

function App() {
  const [token, setToken] = useState(localStorage.getItem('aml_token'));
  const [role, setRole] = useState(localStorage.getItem('aml_role') || 'ANALYST');
  const [active, setActive] = useState('Overview');
  const [transactions, setTransactions] = useState([]);
  const [fraud, setFraud] = useState([]);
  const [aml, setAml] = useState([]);
  const [cases, setCases] = useState([]);
  const [stats, setStats] = useState({total_transactions:0,fraud_alerts:0,aml_alerts:0,open_cases:0,critical_alerts:0});
  const [email, setEmail] = useState('analyst@aml.local');
  const [password, setPassword] = useState('Analyst123!');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) return;
    axios.defaults.headers.common.Authorization = `Bearer ${token}`;
    const load = async () => {
      try {
        const [t,f,a,c,s] = await Promise.all([
          axios.get(`${API}/transactions?page_size=30`), axios.get(`${API}/fraud-alerts?page_size=30`),
          axios.get(`${API}/aml-alerts?page_size=30`), axios.get(`${API}/cases`), axios.get(`${API}/dashboard/stats`)
        ]);
        setTransactions(t.data); setFraud(f.data); setAml(a.data); setCases(c.data); setStats(s.data);
      } catch (e) { setError(e.response?.data?.detail || 'Unable to load monitoring data'); }
    };
    load();
    const timer = setInterval(load, 10000);
    return () => clearInterval(timer);
  }, [token]);

  const login = async (event) => {
    event.preventDefault();
    try {
      const response = await axios.post(`${API}/auth/login`, {email,password});
      localStorage.setItem('aml_token', response.data.access_token);
      localStorage.setItem('aml_role', response.data.role);
      setToken(response.data.access_token); setRole(response.data.role); setError('');
    } catch (e) { setError(e.response?.data?.detail || 'Login failed'); }
  };

  if (!token) return <div className="login-wrap"><form className="login-card" onSubmit={login}><div className="brand-mark">AML</div><h1>Financial Crime Operations</h1><p>Secure monitoring console</p>{error && <div className="error">{error}</div>}<label>Email<input value={email} onChange={e=>setEmail(e.target.value)} /></label><label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} /></label><button>Sign in</button><small>Demo: analyst@aml.local / Analyst123!</small></form></div>;

  const logout = () => { localStorage.clear(); setToken(null); };
  return <div className="app-shell"><aside><div className="brand"><span className="brand-mark">AML</span><div><b>Sentinel</b><small>Financial Crime</small></div></div><nav>{sections.map(name=><button key={name} className={active===name?'active':''} onClick={()=>setActive(name)}><span>{icon(name)}</span>{name}</button>)}</nav><div className="operator"><div className="avatar">{role[0]}</div><div><b>{role === 'ADMIN' ? 'System Admin' : 'Fraud Analyst'}</b><small>Online</small></div><button onClick={logout}>×</button></div></aside><main><header><div><p>Operations Console</p><h1>{active}</h1></div><div className="live"><i></i> Live monitoring</div></header>{error&&<div className="error page-error">{error}</div>}<div className="content">{active==='Overview'&&<Overview stats={stats} transactions={transactions}/>} {active==='Transactions'&&<Transactions data={transactions}/>} {active==='Fraud Alerts'&&<FraudAlerts data={fraud}/>} {active==='AML Monitoring'&&<AmlAlerts data={aml}/>} {active==='Cases'&&<Cases data={cases}/>} {active==='Analytics'&&<Analytics fraud={fraud} aml={aml} transactions={transactions}/>} {active==='Audit'&&<Audit role={role}/>}</div></main></div>;
}

function icon(name){ const map={Overview:'▦',Transactions:'⇄','Fraud Alerts':'!', 'AML Monitoring':'◎',Cases:'▤',Analytics:'▥',Audit:'≡'}; return map[name]; }

function Overview({stats,transactions}) { const cards=[['Total Transactions',stats.total_transactions,'#2563eb'],['Fraud Alerts',stats.fraud_alerts,'#d97706'],['AML Alerts',stats.aml_alerts,'#7c3aed'],['Open Cases',stats.open_cases,'#dc2626'],['Critical Alerts',stats.critical_alerts,'#991b1b']]; const chartData={labels:['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],datasets:[{label:'Transactions',data:[180,240,210,320,290,380,350],borderColor:'#2563eb',backgroundColor:'#dbeafe',tension:.35}]}; return <><div className="metric-grid">{cards.map(([title,value,color])=> <div className="metric" key={title}><div className="metric-icon" style={{background:color+'18',color}}>{title[0]}</div><div><small>{title}</small><strong>{value}</strong></div></div>)}</div><div className="grid-2"><Panel title="Transaction activity"><Line data={chartData} options={{responsive:true,plugins:{legend:{display:false}},scales:{x:{grid:{display:false}}}}}/></Panel><Panel title="Risk distribution"><Doughnut data={{labels:['Low','Medium','High','Critical'],datasets:[{data:[62,22,11,5],backgroundColor:['#22c55e','#eab308','#f97316','#dc2626']}]}} options={{cutout:'68%',plugins:{legend:{position:'bottom'}}}}/></Panel></div><Panel title="Recent transactions"><Transactions data={transactions.slice(0,8)} compact/></Panel></>; }

function Panel({title,children,action}) { return <section className="panel"><div className="panel-head"><h2>{title}</h2>{action}</div>{children}</section>; }

function Transactions({data,compact=false}) { return <div className="table-wrap"><table><thead><tr><th>Transaction</th><th>From / To</th><th>Amount</th><th>Channel</th><th>Location</th><th>Status</th><th>Time</th></tr></thead><tbody>{data.length?data.map(t=><tr key={t.transaction_id}><td><b>{String(t.transaction_id).slice(0,8)}</b></td><td>{String(t.sender_account_id).slice(0,8)} → {String(t.receiver_account_id).slice(0,8)}</td><td><b>{t.amount} {t.currency}</b></td><td>{t.channel}</td><td>{t.source_location}</td><td><span className={'badge '+(t.status==='COMPLETED'?'success':'danger')}>{t.status}</span></td><td>{new Date(t.occurred_at).toLocaleString()}</td></tr>):<tr><td colSpan="7" className="empty">No transactions found</td></tr>}</tbody></table></div>; }

function FraudAlerts({data}) { return <Panel title="Fraud alert queue" action={<button className="secondary">Export</button>}><div className="table-wrap"><table><thead><tr><th>Alert</th><th>Transaction</th><th>Risk</th><th>Severity</th><th>Rules</th><th>Status</th></tr></thead><tbody>{data.map(a=><tr key={a.id}><td><b>{String(a.id).slice(0,8)}</b></td><td>{String(a.transaction_id).slice(0,8)}</td><td><div className="risk"><span style={{width:Math.max(8,a.risk_score)+'%'}}></span><b>{a.risk_score}</b></div></td><td><span className={'badge '+a.severity.toLowerCase()}>{a.severity}</span></td><td>{a.triggered_rules.map(r=>r.rule).join(', ')}</td><td><span className="badge neutral">{a.status}</span></td></tr>)}</tbody></table></div></Panel>; }

function AmlAlerts({data}) { return <><div className="grid-2"><Panel title="Suspicious networks"><div className="network"><div className="node n1">A-1001</div><div className="node n2">A-1002</div><div className="node n3">A-1003</div><div className="node n4">A-1004</div><div className="line l1"></div><div className="line l2"></div><div className="line l3"></div></div></Panel><Panel title="Pattern distribution"><Bar data={{labels:['Structuring','Rapid movement','Many-to-one','Circular'],datasets:[{label:'Alerts',data:[5,3,7,2],backgroundColor:'#3b82f6'}]}} options={{plugins:{legend:{display:false}}}}/></Panel></div><Panel title="AML indicators"><div className="table-wrap"><table><thead><tr><th>Alert</th><th>Pattern</th><th>Accounts</th><th>Transactions</th><th>Risk</th><th>Status</th></tr></thead><tbody>{data.map(a=><tr key={a.id}><td>{String(a.id).slice(0,8)}</td><td><b>{a.pattern_type.replaceAll('_',' ')}</b></td><td>{a.involved_accounts.length}</td><td>{a.related_transactions.length}</td><td>{a.risk_score}</td><td><span className="badge neutral">{a.status}</span></td></tr>)}</tbody></table></div></Panel></>; }

function Cases({data}) { return <Panel title="Investigation cases"><div className="case-grid">{data.length?data.map(c=><article className="case-card" key={c.id}><div><span className={'badge '+(c.priority==='HIGH'?'high':'neutral')}>{c.priority}</span><small>{String(c.id).slice(0,8)}</small></div><h3>{c.title}</h3><p>{c.source_type} investigation</p><footer><span>{c.status.replaceAll('_',' ')}</span><button className="secondary">Open</button></footer></article>):<div className="empty">No investigation cases</div>}</div></Panel>; }

function Analytics({fraud,aml,transactions}) { const severity={Low:fraud.filter(a=>a.severity==='LOW').length,Medium:fraud.filter(a=>a.severity==='MEDIUM').length,High:fraud.filter(a=>a.severity==='HIGH').length,Critical:fraud.filter(a=>a.severity==='CRITICAL').length}; return <div className="grid-2"><Panel title="Fraud severity"><Bar data={{labels:Object.keys(severity),datasets:[{data:Object.values(severity),backgroundColor:['#22c55e','#eab308','#f97316','#dc2626']}]}} options={{plugins:{legend:{display:false}}}}/></Panel><Panel title="AML patterns"><Doughnut data={{labels:['Structuring','Rapid movement','Many-to-one','Circular'],datasets:[{data:[aml.filter(a=>a.pattern_type==='STRUCTURING').length,aml.filter(a=>a.pattern_type==='RAPID_FUND_MOVEMENT').length,aml.filter(a=>a.pattern_type==='MANY_TO_ONE').length,aml.filter(a=>a.pattern_type==='CIRCULAR_TRANSACTION').length],backgroundColor:['#2563eb','#7c3aed','#db2777','#0891b2']}]}}/></Panel></div>; }

function Audit({role}) { const [logs,setLogs]=useState([]); useEffect(()=>{if(role==='ADMIN') axios.get(`${API}/audit`).then(r=>setLogs(r.data)).catch(()=>setLogs([]));},[role]); return <Panel title="Audit trail"><div className="table-wrap"><table><thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Entity</th><th>Change</th></tr></thead><tbody>{role==='ADMIN'?logs.map(l=><tr key={l.id}><td>{new Date(l.created_at).toLocaleString()}</td><td>{String(l.actor_id).slice(0,8)}</td><td>{l.action}</td><td>{l.entity_type}</td><td>{l.updated_value||'-'}</td></tr>):<tr><td colSpan="5" className="empty">Administrator access required</td></tr>}</tbody></table></div></Panel>; }

export default App;

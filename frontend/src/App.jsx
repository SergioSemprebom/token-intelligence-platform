import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  Bell,
  Bot,
  Boxes,
  CircleDollarSign,
  Gauge,
  LayoutDashboard,
  RefreshCw,
  Settings,
  Sparkles,
  WalletCards,
  Zap,
} from 'lucide-react'
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

const fallback = {
  periodo: '2026-07',
  moeda: 'USD',
  gasto_mes: 42.7,
  orcamento_mensal: 100,
  projecao_mes: 67.3,
  tokens_total: 8420500,
  requisicoes_total: 12480,
  economia_estimada: 18.4,
  provedores: [
    { nome: 'OpenAI', slug: 'openai', status: 'demonstracao', tokens: 3200000, requisicoes: 4850, custo: 18.6 },
    { nome: 'Gemini', slug: 'gemini', status: 'planejado', tokens: 2900000, requisicoes: 5100, custo: 8.2 },
    { nome: 'Claude', slug: 'anthropic', status: 'planejado', tokens: 1800000, requisicoes: 1930, custo: 14.7 },
    { nome: 'OpenRouter', slug: 'openrouter', status: 'planejado', tokens: 520500, requisicoes: 600, custo: 1.2 },
  ],
  consumo_diario: [
    { dia: '01', custo: 3.2 },
    { dia: '05', custo: 5.1 },
    { dia: '10', custo: 6.8 },
    { dia: '15', custo: 8.4 },
    { dia: '20', custo: 9.7 },
    { dia: '25', custo: 9.5 },
  ],
}

const money = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD' })
const number = new Intl.NumberFormat('pt-BR')

function MetricCard({ icon: Icon, label, value, detail }) {
  return (
    <article className="metric-card">
      <div className="metric-icon"><Icon size={20} /></div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </article>
  )
}

function App() {
  const [data, setData] = useState(fallback)
  const [loading, setLoading] = useState(true)
  const [source, setSource] = useState('Demonstração')

  async function loadDashboard() {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/v1/dashboard/resumo`)
      if (!response.ok) throw new Error('Falha ao consultar a API')
      setData(await response.json())
      setSource('API conectada')
    } catch {
      setData(fallback)
      setSource('Demonstração local')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboard()
  }, [])

  const budgetPercent = useMemo(
    () => Math.min(100, (data.gasto_mes / data.orcamento_mensal) * 100),
    [data],
  )

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Sparkles size={22} /></div>
          <div><strong>Token Intelligence</strong><span>Platform</span></div>
        </div>

        <nav>
          <a className="active" href="#dashboard"><LayoutDashboard size={18} /> Visão geral</a>
          <a href="#providers"><Boxes size={18} /> Provedores</a>
          <a href="#usage"><Activity size={18} /> Consumo</a>
          <a href="#budgets"><WalletCards size={18} /> Orçamentos</a>
          <a href="#alerts"><Bell size={18} /> Alertas</a>
          <a href="#settings"><Settings size={18} /> Configurações</a>
        </nav>

        <div className="sidebar-footer">
          <Bot size={18} />
          <div><strong>Fase 8</strong><span>Dashboard multiprovedor</span></div>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <div>
            <p className="eyebrow">CENTRAL DE GOVERNANÇA DE IA</p>
            <h1>Visão geral do consumo</h1>
            <p>Monitore tokens, custos, requisições e orçamento em um único lugar.</p>
          </div>
          <button onClick={loadDashboard} disabled={loading}>
            <RefreshCw size={17} className={loading ? 'spin' : ''} /> Atualizar
          </button>
        </header>

        <section className="status-row">
          <span className="status-dot" /> {source}
          <span>Período: {data.periodo}</span>
        </section>

        <section className="metrics-grid">
          <MetricCard icon={CircleDollarSign} label="Gasto no mês" value={money.format(data.gasto_mes)} detail={`${budgetPercent.toFixed(1)}% do orçamento`} />
          <MetricCard icon={Gauge} label="Tokens utilizados" value={number.format(data.tokens_total)} detail="Entrada, saída e cache" />
          <MetricCard icon={Zap} label="Requisições" value={number.format(data.requisicoes_total)} detail="Todos os provedores" />
          <MetricCard icon={Sparkles} label="Economia estimada" value={money.format(data.economia_estimada)} detail="Otimizações sugeridas" />
        </section>

        <section className="dashboard-grid">
          <article className="panel chart-panel">
            <div className="panel-header">
              <div><span>EVOLUÇÃO DE CUSTO</span><h2>Consumo diário</h2></div>
              <span className="projection">Projeção: {money.format(data.projecao_mes)}</span>
            </div>
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.consumo_diario}>
                  <defs>
                    <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4fd1c5" stopOpacity={0.45} />
                      <stop offset="95%" stopColor="#4fd1c5" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#26384d" />
                  <XAxis dataKey="dia" stroke="#7890a8" />
                  <YAxis stroke="#7890a8" />
                  <Tooltip contentStyle={{ background: '#0f1d2c', border: '1px solid #294158', borderRadius: 12 }} />
                  <Area type="monotone" dataKey="custo" stroke="#4fd1c5" fill="url(#costGradient)" strokeWidth={3} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </article>

          <article className="panel budget-panel">
            <div className="panel-header"><div><span>CONTROLE FINANCEIRO</span><h2>Orçamento mensal</h2></div></div>
            <div className="budget-circle" style={{ '--progress': `${budgetPercent * 3.6}deg` }}>
              <div><strong>{budgetPercent.toFixed(0)}%</strong><span>utilizado</span></div>
            </div>
            <div className="budget-values">
              <div><span>Consumido</span><strong>{money.format(data.gasto_mes)}</strong></div>
              <div><span>Limite</span><strong>{money.format(data.orcamento_mensal)}</strong></div>
            </div>
          </article>
        </section>

        <section className="panel providers-panel" id="providers">
          <div className="panel-header">
            <div><span>INTEGRAÇÕES</span><h2>Consumo por provedor</h2></div>
            <button className="secondary-button"><Boxes size={16} /> Gerenciar provedores</button>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Provedor</th><th>Status</th><th>Tokens</th><th>Requisições</th><th>Custo mensal</th></tr></thead>
              <tbody>
                {data.provedores.map((provider) => (
                  <tr key={provider.slug}>
                    <td><div className="provider-name"><div className={`provider-logo ${provider.slug}`}>{provider.nome[0]}</div><strong>{provider.nome}</strong></div></td>
                    <td><span className={`badge ${provider.status}`}>{provider.status.replaceAll('_', ' ')}</span></td>
                    <td>{number.format(provider.tokens)}</td>
                    <td>{number.format(provider.requisicoes)}</td>
                    <td><strong>{money.format(provider.custo)}</strong></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App

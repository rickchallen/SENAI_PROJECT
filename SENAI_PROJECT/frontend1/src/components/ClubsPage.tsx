import { useEffect, useMemo, useState, type FormEvent } from 'react'

import { api } from '../api'
import { localDate, money } from '../format'
import type {
  Club,
  Formation,
  Lineup,
  Player,
  Transaction,
  TransactionHistory,
} from '../types'
import type { ActionRunner } from './shared'

const formations: Formation[] = ['3-1', '2-2', '2-1-1', '1-2-1']

export function ClubsPage({
  refreshToken,
  busy,
  run,
}: {
  refreshToken: number
  busy: boolean
  run: ActionRunner
}) {
  const [clubs, setClubs] = useState<Club[]>([])
  const [sort, setSort] = useState('name')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    let active = true
    api.clubs(sort)
      .then((data) => {
        if (!active) return
        setLoadError('')
        setClubs(data)
        setSelectedId((current) =>
          current && !data.some((club) => club.id === current) ? null : current,
        )
      })
      .catch((error: Error) => {
        if (active) setLoadError(error.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [sort, refreshToken])

  const createClub = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const created = await run(
      () =>
        api.createClub({
          name: String(form.get('name')),
          acronym: String(form.get('acronym')).toUpperCase(),
        }),
      'Clube cadastrado com caixa inicial de R$ 300,00.',
    )
    if (created) {
      setSelectedId((created as Club).id)
      setShowCreate(false)
    }
  }

  return (
    <section className="page-stack">
      <header className="page-heading">
        <div>
          <p className="eyebrow">GESTÃO FINANCEIRA</p>
          <h1>Clubes</h1>
          <p>Organize elencos, contratos e histórico de movimentações.</p>
        </div>
        <button className="button button-primary" onClick={() => setShowCreate(true)}>
          + Novo clube
        </button>
      </header>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Clubes da liga</h2>
            <p>{clubs.length} de 20 clubes</p>
          </div>
          <label className="sort-control">
            Ordenar por
            <select value={sort} onChange={(event) => setSort(event.target.value)}>
              <option value="name">Nome</option>
              <option value="net_worth_desc">Maior patrimônio</option>
              <option value="net_worth_asc">Menor patrimônio</option>
            </select>
          </label>
        </div>
        {loading ? (
          <div className="state-message">Carregando clubes…</div>
        ) : loadError ? (
          <div className="state-message state-error">{loadError}</div>
        ) : clubs.length === 0 ? (
          <div className="empty-card">
            <span className="empty-icon">⚽</span>
            <strong>A liga ainda não tem clubes</strong>
            <p>Cadastre o primeiro clube para começar a montar os elencos.</p>
          </div>
        ) : (
          <div className="club-grid">
            {clubs.map((club) => (
              <button
                key={club.id}
                className={`club-card ${selectedId === club.id ? 'club-card-selected' : ''}`}
                onClick={() =>
                  setSelectedId((current) => (current === club.id ? null : club.id))
                }
              >
                <span className="club-mark">{club.acronym}</span>
                <span className="club-card-copy">
                  <strong>{club.name}</strong>
                  <small>Caixa {money(club.cash)}</small>
                </span>
                <span className="club-worth">
                  <small>Patrimônio</small>
                  <strong>{money(club.net_worth)}</strong>
                </span>
              </button>
            ))}
          </div>
        )}
      </section>

      {selectedId && (
        <ClubDetails
          key={selectedId}
          clubId={selectedId}
          refreshToken={refreshToken}
          busy={busy}
          run={run}
        />
      )}

      {showCreate && (
        <div className="modal-backdrop" role="presentation">
          <section className="modal-card" role="dialog" aria-modal="true" aria-label="Cadastrar clube">
            <header className="modal-heading">
              <h2>Novo clube</h2>
              <button className="icon-button" aria-label="Fechar" onClick={() => setShowCreate(false)}>×</button>
            </header>
            <form className="form-grid" onSubmit={createClub}>
              <label className="wide-field">
                Nome do clube
                <input name="name" minLength={3} maxLength={60} required placeholder="Ex.: Águias FC" />
              </label>
              <label>
                Sigla
                <input name="acronym" minLength={3} maxLength={3} pattern="[A-Za-z]{3}" required placeholder="AGU" />
              </label>
              <p className="form-hint wide-field">
                O clube será criado com R$ 300,00 em caixa. A sigla deve acompanhar as letras do nome.
              </p>
              <div className="form-actions wide-field">
                <button className="button" type="button" onClick={() => setShowCreate(false)}>Cancelar</button>
                <button className="button button-primary" disabled={busy}>Criar clube</button>
              </div>
            </form>
          </section>
        </div>
      )}
    </section>
  )
}

function ClubDetails({
  clubId,
  refreshToken,
  busy,
  run,
}: {
  clubId: number
  refreshToken: number
  busy: boolean
  run: ActionRunner
}) {
  const [club, setClub] = useState<Club | null>(null)
  const [lineup, setLineup] = useState<Lineup | null>(null)
  const [transactions, setTransactions] = useState<TransactionHistory | null>(null)
  const [allTransactions, setAllTransactions] = useState<Transaction[]>([])
  const [tab, setTab] = useState<'squad' | 'lineup' | 'history'>('squad')
  const [typeFilters, setTypeFilters] = useState<string[]>([])
  const [playerFilter, setPlayerFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [formation, setFormation] = useState<Formation>('2-1-1')
  const [selectedPlayers, setSelectedPlayers] = useState<number[]>([])
  const [saleReceipt, setSaleReceipt] = useState<Record<string, unknown> | null>(null)

  const transactionParams = useMemo(
    () => ({
      type: typeFilters.length ? typeFilters.join(',') : undefined,
      player_id: playerFilter ? Number(playerFilter) : undefined,
    }),
    [typeFilters, playerFilter],
  )

  useEffect(() => {
    let active = true
    Promise.all([
      api.club(clubId),
      api.lineup(clubId),
      api.transactions(clubId, transactionParams),
      api.transactions(clubId),
    ])
      .then(([clubData, lineupData, history, completeHistory]) => {
        if (!active) return
        setLoadError('')
        setClub(clubData)
        setLineup(lineupData)
        setTransactions(history)
        setAllTransactions(completeHistory.data)
        if (lineupData.formation) setFormation(lineupData.formation)
        setSelectedPlayers(lineupData.players.map((player) => player.id))
      })
      .catch((error: Error) => {
        if (active) setLoadError(error.message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [clubId, refreshToken, transactionParams])

  const toggleType = (value: string) => {
    setTypeFilters((current) =>
      current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value],
    )
  }

  const sellPlayer = async (player: Player) => {
    if (!window.confirm(`Vender ${player.name} por ${money(player.market_value)}?`)) return
    const receipt = await run(
      () => api.sell(player.id),
      'Venda concluída. Os valores foram calculados pela API.',
    )
    if (receipt) setSaleReceipt(receipt as Record<string, unknown>)
  }

  const saveLineup = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (selectedPlayers.length !== 5) return
    const updated = await run(
      () => api.saveLineup(clubId, { formation, player_ids: selectedPlayers }),
      'Escalação salva.',
    )
    if (updated) setLineup(updated as Lineup)
  }

  const exportCsv = async () => {
    const file = await run(
      () => api.exportTransactions(clubId, transactionParams),
      'Exportação CSV pronta.',
    )
    if (!file) return
    const url = URL.createObjectURL(file as Blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `transacoes-${clubId}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  const availablePlayers = (club?.players ?? []).filter(
    (player) => player.condition !== 'DOENTE',
  )
  const selectedRoster = (club?.players ?? []).filter((player) =>
    selectedPlayers.includes(player.id),
  )
  const formationSlots: Record<Formation, [number, number, number]> = {
    '3-1': [3, 0, 1],
    '2-2': [2, 0, 2],
    '2-1-1': [2, 1, 1],
    '1-2-1': [1, 2, 1],
  }
  const selectedDefense = selectedRoster.filter(
    (player) => player.position === 'ZAG' || player.position === 'LAT',
  ).length
  const selectedMidfield = selectedRoster.filter(
    (player) => player.position === 'MEI',
  ).length
  const selectedAttack = selectedRoster.filter(
    (player) => player.position === 'ATA',
  ).length
  const [requiredDefense, requiredMidfield, requiredAttack] =
    formationSlots[formation]
  const lineupIsValid =
    selectedRoster.length === 5 &&
    selectedRoster.filter((player) => player.position === 'GOL').length === 1 &&
    selectedDefense === requiredDefense &&
    selectedMidfield === requiredMidfield &&
    selectedAttack === requiredAttack
  const lineupIssue =
    selectedRoster.length !== 5
      ? 'Selecione exatamente cinco titulares.'
      : !lineupIsValid
        ? 'As posições não correspondem à formação selecionada.'
        : ''

  const togglePlayer = (playerId: number) => {
    setSelectedPlayers((current) =>
      current.includes(playerId)
        ? current.filter((id) => id !== playerId)
        : current.length < 5
          ? [...current, playerId]
          : current,
    )
  }

  return (
    <section className="panel club-details">
      {loading ? (
        <div className="state-message">Carregando dados do clube…</div>
      ) : loadError ? (
        <div className="state-message state-error">{loadError}</div>
      ) : !club ? (
        <div className="state-message">Clube indisponível.</div>
      ) : (
        <>
          {saleReceipt && (
            <aside className="sale-receipt">
              <div className="receipt-heading">
                <strong>Venda de {receiptText(saleReceipt.player_name, 'jogador')} concluída</strong>
                <button className="icon-button" aria-label="Fechar comprovante" onClick={() => setSaleReceipt(null)}>×</button>
              </div>
              <div className="receipt-values">
                <ClubReceiptValue label="Valor de compra" value={saleReceipt.purchase_value} />
                <ClubReceiptValue label="Valor de venda" value={saleReceipt.value} />
                <ClubReceiptValue label="Dias restantes" value={saleReceipt.remaining_days} />
                <ClubReceiptValue label="Multa" value={saleReceipt.penalty} />
                <ClubReceiptValue label="Lucro" value={saleReceipt.profit} />
                <ClubReceiptValue label="Comissão" value={saleReceipt.fee} />
                <ClubReceiptValue label="Crédito" value={saleReceipt.cash_change} />
                <ClubReceiptValue label="Novo caixa" value={saleReceipt.club_cash} />
              </div>
            </aside>
          )}
          <div className="club-profile">
            <span className="club-mark club-mark-large">{club.acronym}</span>
            <div>
              <p className="eyebrow">VISÃO DO CLUBE</p>
              <h2>{club.name}</h2>
            </div>
            <div className="club-metrics">
              <Metric label="Caixa" value={money(club.cash)} />
              <Metric label="Valor do elenco" value={money(club.squad_value)} />
              <Metric label="Patrimônio" value={money(club.net_worth)} />
            </div>
          </div>
          <nav className="tabs" aria-label="Seções do clube">
            <button className={tab === 'squad' ? 'tab-active' : ''} onClick={() => setTab('squad')}>Elenco</button>
            <button className={tab === 'lineup' ? 'tab-active' : ''} onClick={() => setTab('lineup')}>Escalação</button>
            <button className={tab === 'history' ? 'tab-active' : ''} onClick={() => setTab('history')}>Transações</button>
          </nav>

          {tab === 'squad' && (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Jogador</th><th>Posição</th><th>Condição</th><th>Mercado</th>
                    <th>Fidelidade até</th><th>Dias restantes</th><th>Multa</th><th />
                  </tr>
                </thead>
                <tbody>
                  {club.players?.map((player) => (
                    <tr key={player.id}>
                      <td><strong>{player.name}</strong><small>#{player.id}</small></td>
                      <td><span className="position-tag">{player.position}</span></td>
                      <td>{player.condition}</td>
                      <td className="value-cell">{money(player.market_value)}</td>
                      <td>{player.contract ? localDate(player.contract.loyalty_until) : '—'}</td>
                      <td>{player.contract?.remaining_days ?? '—'}</td>
                      <td>{player.contract ? `${player.contract.penalty_rate}%` : '—'}</td>
                      <td>
                        <button className="button button-small button-danger" disabled={busy} onClick={() => void sellPlayer(player)}>
                          Vender
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!club.players?.length && <div className="state-message">Este clube ainda não tem jogadores.</div>}
            </div>
          )}

          {tab === 'lineup' && (
            <form className="lineup-editor" onSubmit={saveLineup}>
              <div className="lineup-summary">
                <div>
                  <h3>Titulares</h3>
                  <p>Escolha um goleiro e quatro jogadores de linha. DOENTE não pode ser escalado.</p>
                </div>
                <label>
                  Formação
                  <select value={formation} onChange={(event) => setFormation(event.target.value as Formation)}>
                    {formations.map((item) => <option key={item}>{item}</option>)}
                  </select>
                </label>
              </div>
              <div className="lineup-status">
                <span className={lineup?.complete ? 'status-dot status-good' : 'status-dot'} />
                {lineup?.complete ? 'Escalação completa' : 'Escalação incompleta — o clube não pode jogar'}
              </div>
              {lineupIssue && <p className="lineup-warning">{lineupIssue}</p>}
              <div className="lineup-list">
                {availablePlayers.map((player) => (
                  <label className="lineup-player" key={player.id}>
                    <input
                      type="checkbox"
                      checked={selectedPlayers.includes(player.id)}
                      disabled={busy || (!selectedPlayers.includes(player.id) && selectedPlayers.length >= 5)}
                      onChange={() => togglePlayer(player.id)}
                    />
                    <span className="position-tag">{player.position}</span>
                    <span className="lineup-player-name">{player.name}</span>
                    <small>{player.condition}</small>
                  </label>
                ))}
                {!availablePlayers.length && <p className="state-message">Compre jogadores para montar uma escalação.</p>}
              </div>
              <div className="form-actions">
                <span className="subtle">{selectedPlayers.length} de 5 titulares</span>
                <button className="button button-primary" disabled={busy || !lineupIsValid}>
                  Salvar escalação
                </button>
              </div>
            </form>
          )}

          {tab === 'history' && (
            <div className="history-content">
              <div className="filter-panel history-filters">
                <fieldset>
                  <legend>Tipo</legend>
                  {(['COMPRA', 'VENDA'] as const).map((type) => (
                    <label className="checkbox-label" key={type}>
                      <input type="checkbox" checked={typeFilters.includes(type)} onChange={() => toggleType(type)} />
                      {type === 'COMPRA' ? 'Compras' : 'Vendas'}
                    </label>
                  ))}
                </fieldset>
                <label>
                  Jogador do histórico
                  <select value={playerFilter} onChange={(event) => setPlayerFilter(event.target.value)}>
                    <option value="">Todos os jogadores</option>
                    {uniquePlayers(allTransactions).map((player) => (
                      <option key={player.id} value={player.id}>{player.name}</option>
                    ))}
                  </select>
                </label>
                <button className="button button-outline" disabled={busy} onClick={() => void exportCsv()}>
                  ↓ Exportar CSV
                </button>
              </div>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr><th>Data e hora</th><th>Tipo</th><th>Jogador</th><th>Valor</th><th>Taxa/comissão</th><th>Multa</th><th>Lucro</th><th>Variação do caixa</th></tr>
                  </thead>
                  <tbody>
                    {transactions?.data.map((transaction) => (
                      <tr key={transaction.id}>
                        <td>{localDate(transaction.created_at)}</td>
                        <td><span className={`transaction-tag ${transaction.type === 'COMPRA' ? 'tag-buy' : 'tag-sell'}`}>{transaction.type}</span></td>
                        <td>{transaction.player_name}</td>
                        <td>{money(transaction.value)}</td>
                        <td>{money(transaction.fee)}</td>
                        <td>{money(transaction.penalty)}</td>
                        <td>{transaction.profit === null ? '—' : money(transaction.profit)}</td>
                        <td className={transaction.cash_change < 0 ? 'negative-value' : 'positive-value'}>
                          {transaction.cash_change < 0 ? '−' : '+'}{money(Math.abs(transaction.cash_change))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!transactions?.data.length && <div className="state-message">Nenhuma transação para esses filtros.</div>}
              </div>
              {transactions && <SummaryCards summary={transactions.summary} />}
            </div>
          )}
        </>
      )}
    </section>
  )
}

function uniquePlayers(transactions: Transaction[]) {
  const players = new Map<number, string>()
  transactions.forEach((transaction) => players.set(transaction.player_id, transaction.player_name))
  return [...players.entries()]
    .map(([id, name]) => ({ id, name }))
    .sort((left, right) => left.name.localeCompare(right.name, 'pt-BR'))
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="metric"><small>{label}</small><strong>{value}</strong></div>
}

function receiptText(value: unknown, fallback: string) {
  return typeof value === 'string' ? value : fallback
}

function ClubReceiptValue({ label, value }: { label: string; value: unknown }) {
  const display =
    typeof value !== 'number'
      ? '—'
      : label === 'Dias restantes'
        ? String(value)
        : money(value)
  return <span><small>{label}</small><b>{display}</b></span>
}

function SummaryCards({ summary }: { summary: TransactionHistory['summary'] }) {
  return (
    <div className="summary-grid">
      <Metric label="Pago em compras" value={money(summary.total_spent)} />
      <Metric label="Recebido em vendas" value={money(summary.total_received)} />
      <Metric label="Taxas e comissões" value={money(summary.total_fees)} />
      <Metric label="Multas" value={money(summary.total_penalties)} />
      <Metric label="Lucro total" value={money(summary.total_profit)} />
    </div>
  )
}

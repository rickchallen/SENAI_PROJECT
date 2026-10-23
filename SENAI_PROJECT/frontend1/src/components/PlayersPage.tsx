import { useEffect, useState, type FormEvent } from 'react'

import { api } from '../api'
import { dateTimeInputDefault, localDate, money } from '../format'
import type { Club, Condition, Player, PlayerList, Position } from '../types'
import type { ActionRunner } from './shared'

const positions: Position[] = ['GOL', 'ZAG', 'LAT', 'MEI', 'ATA']
const conditions: Condition[] = ['APTO', 'MAL_CONDICIONADO', 'DOENTE']
const numericFields = [
  ['pace', 'Velocidade'],
  ['shooting', 'Finalização'],
  ['passing', 'Passe'],
  ['dribbling', 'Drible'],
  ['defending', 'Defesa'],
  ['physical', 'Físico'],
  ['potential', 'Potencial'],
] as const

type Filters = {
  search: string
  position: string
  condition: string
  free: string
  club_id: string
  min_age: string
  max_age: string
  min_value: string
  max_value: string
  sort: string
  page: number
}

const initialFilters: Filters = {
  search: '',
  position: '',
  condition: '',
  free: '',
  club_id: '',
  min_age: '',
  max_age: '',
  min_value: '',
  max_value: '',
  sort: 'name',
  page: 1,
}

function queryParams(filters: Filters) {
  return Object.fromEntries(
    Object.entries(filters).filter(
      ([key, value]) => key !== 'page' && value !== '',
    ),
  )
}

function receiptText(value: unknown, fallback: string) {
  return typeof value === 'string' ? value : fallback
}

function receiptNumber(value: unknown) {
  return typeof value === 'number' ? value : 0
}

function receiptContractDate(value: unknown) {
  if (typeof value !== 'object' || value === null || !('loyalty_until' in value)) {
    return '—'
  }
  const loyaltyUntil = value.loyalty_until
  return typeof loyaltyUntil === 'string' ? localDate(loyaltyUntil) : '—'
}

function ReceiptValue({
  label,
  value,
  formatted = false,
}: {
  label: string
  value: unknown
  formatted?: boolean
}) {
  const display =
    formatted && typeof value === 'string'
      ? value
      : typeof value === 'number'
        ? money(value)
        : '—'
  return <span><small>{label}</small><b>{display}</b></span>
}

function createInitialForm() {
  return {
    name: '',
    position: 'MEI',
    agility: '70',
    age: '25',
    pace: '70',
    shooting: '70',
    passing: '70',
    dribbling: '70',
    defending: '70',
    physical: '70',
    potential: '70',
  }
}

export function PlayersPage({
  refreshToken,
  busy,
  run,
}: {
  refreshToken: number
  busy: boolean
  run: ActionRunner
}) {
  const [filters, setFilters] = useState(initialFilters)
  const [result, setResult] = useState<PlayerList | null>(null)
  const [clubs, setClubs] = useState<Club[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState(createInitialForm)
  const [createdPlayer, setCreatedPlayer] = useState<Player | null>(null)
  const [editing, setEditing] = useState<Player | null>(null)
  const [buying, setBuying] = useState<Player | null>(null)
  const [purchaseReceipt, setPurchaseReceipt] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    let active = true
    Promise.all([api.players({ ...queryParams(filters), page: filters.page }), api.clubs()])
      .then(([players, clubList]) => {
        if (active) {
          setLoadError('')
          setResult(players)
          setClubs(clubList)
        }
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
  }, [filters, refreshToken])

  const changeFilter = (field: keyof Filters, value: string) => {
    setFilters((current) => ({
      ...current,
      [field]: value,
      page: field === 'page' ? Number(value) : 1,
    }))
  }

  const submitCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const payload = {
      name: createForm.name,
      position: createForm.position,
      ...Object.fromEntries(
        [
          'agility',
          'age',
          ...numericFields.map(([field]) => field),
        ].map((field) => [field, Number(createForm[field as keyof typeof createForm])]),
      ),
    } as Record<string, string | number>
    const created = await run(
      () => api.createPlayer(payload),
      'Jogador cadastrado.',
    )
    if (created) {
      setCreatedPlayer(created as Player)
      setCreateForm(createInitialForm())
      setShowCreate(false)
    }
  }

  const submitEdit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!editing) return
    const form = new FormData(event.currentTarget)
    const updated = await run(
      () =>
        api.updatePlayer(editing.id, {
          name: String(form.get('name')),
          position: String(form.get('position')),
          agility: Number(form.get('agility')),
          age: Number(form.get('age')),
        }),
      'Dados do jogador atualizados.',
    )
    if (updated) setEditing(null)
  }

  const submitBuy = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!buying) return
    const form = new FormData(event.currentTarget)
    const clubId = Number(form.get('club_id'))
    const loyaltyUntil = String(form.get('loyalty_until'))
    const purchase = await run(
      () =>
        api.buy(buying.id, {
          club_id: clubId,
          loyalty_until: `${loyaltyUntil}-03:00`,
        }),
      'Compra concluída.',
    )
    if (purchase) {
      setPurchaseReceipt(purchase as Record<string, unknown>)
      setBuying(null)
    }
  }

  return (
    <section className="page-stack">
      <header className="page-heading">
        <div>
          <p className="eyebrow">ELENCO DA LIGA</p>
          <h1>Jogadores</h1>
          <p>Cadastre, acompanhe valores e gerencie transferências.</p>
        </div>
        <button className="button button-primary" onClick={() => setShowCreate(true)}>
          + Novo jogador
        </button>
      </header>

      {purchaseReceipt && (
        <aside className="receipt-card">
          <div className="receipt-heading">
            <strong>Compra de {receiptText(purchaseReceipt.player_name, 'jogador')} concluída</strong>
            <button className="icon-button" aria-label="Fechar comprovante" onClick={() => setPurchaseReceipt(null)}>×</button>
          </div>
          <div className="receipt-values">
            <ReceiptValue label="Valor de mercado" value={purchaseReceipt.value} />
            <ReceiptValue label="Taxa" value={purchaseReceipt.fee} />
            <ReceiptValue
              label="Custo total"
              value={receiptNumber(purchaseReceipt.value) + receiptNumber(purchaseReceipt.fee)}
            />
            <ReceiptValue label="Fidelidade até" value={receiptContractDate(purchaseReceipt.contract)} formatted />
            <ReceiptValue label="Novo caixa" value={purchaseReceipt.club_cash} />
          </div>
        </aside>
      )}

      {createdPlayer && (
        <aside className="calculated-result">
          <strong>{createdPlayer.name} cadastrado</strong>
          <span>Overall {createdPlayer.overall}</span>
          <span>Valor base {money(createdPlayer.base_value)}</span>
          <span>Valor de mercado {money(createdPlayer.market_value)}</span>
          <button
            className="icon-button"
            aria-label="Fechar resumo"
            onClick={() => setCreatedPlayer(null)}
          >
            ×
          </button>
        </aside>
      )}

      <form
        className="filter-panel"
        onSubmit={(event) => event.preventDefault()}
        aria-label="Filtros de jogadores"
      >
        <label className="filter-search">
          Buscar jogador
          <input
            value={filters.search}
            onChange={(event) => changeFilter('search', event.target.value)}
            placeholder="Nome do jogador"
          />
        </label>
        <label>
          Posição
          <select
            value={filters.position}
            onChange={(event) => changeFilter('position', event.target.value)}
          >
            <option value="">Todas</option>
            {positions.map((position) => (
              <option key={position}>{position}</option>
            ))}
          </select>
        </label>
        <label>
          Condição
          <select
            value={filters.condition}
            onChange={(event) => changeFilter('condition', event.target.value)}
          >
            <option value="">Todas</option>
            {conditions.map((condition) => (
              <option key={condition}>{condition}</option>
            ))}
          </select>
        </label>
        <label>
          Situação
          <select
            value={filters.free}
            onChange={(event) => {
              const next = event.target.value
              if (next === 'true' && filters.club_id) {
                changeFilter('club_id', '')
              }
              changeFilter('free', next)
            }}
          >
            <option value="">Todos</option>
            <option value="true">Livres</option>
            <option value="false">Com clube</option>
          </select>
        </label>
        <label>
          Clube
          <select
            value={filters.club_id}
            disabled={filters.free === 'true'}
            onChange={(event) => changeFilter('club_id', event.target.value)}
          >
            <option value="">Todos</option>
            {clubs.map((club) => (
              <option key={club.id} value={club.id}>
                {club.acronym}
              </option>
            ))}
          </select>
        </label>
        <label>
          Idade de
          <input
            type="number"
            min="16"
            max="45"
            value={filters.min_age}
            onChange={(event) => changeFilter('min_age', event.target.value)}
          />
        </label>
        <label>
          até
          <input
            type="number"
            min="16"
            max="45"
            value={filters.max_age}
            onChange={(event) => changeFilter('max_age', event.target.value)}
          />
        </label>
        <label>
          Valor mín.
          <input
            type="number"
            min="0"
            max="550"
            step="0.01"
            value={filters.min_value}
            onChange={(event) => changeFilter('min_value', event.target.value)}
          />
        </label>
        <label>
          Valor máx.
          <input
            type="number"
            min="0"
            max="550"
            step="0.01"
            value={filters.max_value}
            onChange={(event) => changeFilter('max_value', event.target.value)}
          />
        </label>
        <label>
          Ordenar
          <select
            value={filters.sort}
            onChange={(event) => changeFilter('sort', event.target.value)}
          >
            <option value="name">Nome</option>
            <option value="value_desc">Maior valor</option>
            <option value="value_asc">Menor valor</option>
            <option value="age_asc">Menor idade</option>
            <option value="age_desc">Maior idade</option>
            <option value="position">Posição</option>
          </select>
        </label>
      </form>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Todos os jogadores</h2>
            <p>{result?.meta.total_items ?? 0} encontrados</p>
          </div>
          {result && (
            <span className="subtle">
              Página {result.meta.page} de {result.meta.total_pages}
            </span>
          )}
        </div>
        {loading ? (
          <div className="state-message">Carregando jogadores…</div>
        ) : loadError ? (
          <div className="state-message state-error">{loadError}</div>
        ) : !result?.data.length ? (
          <div className="state-message">Nenhum jogador encontrado com esses filtros.</div>
        ) : (
          <>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Jogador</th>
                    <th>Posição</th>
                    <th>Overall</th>
                    <th>Agilidade</th>
                    <th>Idade</th>
                    <th>Condição</th>
                    <th>Valor base</th>
                    <th>Mercado</th>
                    <th>Clube</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {result.data.map((player) => (
                    <tr key={player.id}>
                      <td>
                        <strong>{player.name}</strong>
                        <small>#{player.id}</small>
                      </td>
                      <td><span className="position-tag">{player.position}</span></td>
                      <td>{player.overall}</td>
                      <td>{player.agility}</td>
                      <td>{player.age}</td>
                      <td>
                        <select
                          className="condition-select"
                          aria-label={`Condição de ${player.name}`}
                          value={player.condition}
                          disabled={busy}
                          onChange={(event) =>
                            void run(
                              () =>
                                api.updateCondition(
                                  player.id,
                                  event.target.value,
                                ),
                              'Condição física atualizada.',
                            )
                          }
                        >
                          {conditions.map((condition) => (
                            <option key={condition}>{condition}</option>
                          ))}
                        </select>
                      </td>
                      <td>{money(player.base_value)}</td>
                      <td className="value-cell">{money(player.market_value)}</td>
                      <td>
                        {player.club_id
                          ? clubs.find((club) => club.id === player.club_id)?.acronym ?? '—'
                          : 'Livre'}
                      </td>
                      <td>
                        <div className="row-actions">
                          <button
                            className="button button-small"
                            disabled={busy}
                            onClick={() => setEditing(player)}
                          >
                            Editar
                          </button>
                          {player.club_id ? (
                            <span className="subtle">No elenco</span>
                          ) : (
                            <>
                              <button
                                className="button button-small button-outline"
                                disabled={busy || clubs.length === 0}
                                onClick={() => setBuying(player)}
                              >
                                Comprar
                              </button>
                              <button
                                className="button button-small button-danger"
                                disabled={busy}
                                onClick={() => {
                                  if (window.confirm(`Excluir ${player.name}?`)) {
                                    void run(
                                      () => api.deletePlayer(player.id),
                                      'Jogador excluído.',
                                    )
                                  }
                                }}
                              >
                                Excluir
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="pagination">
              <button
                className="button"
                disabled={filters.page <= 1 || busy}
                onClick={() => changeFilter('page', String(filters.page - 1))}
              >
                Anterior
              </button>
              <span>
                {result.meta.total_items} jogadores · página {filters.page}
              </span>
              <button
                className="button"
                disabled={filters.page >= result.meta.total_pages || busy}
                onClick={() => changeFilter('page', String(filters.page + 1))}
              >
                Próxima
              </button>
            </div>
          </>
        )}
      </section>

      {showCreate && (
        <Modal title="Cadastrar jogador" onClose={() => setShowCreate(false)}>
          <form className="form-grid" onSubmit={submitCreate}>
            <label className="wide-field">
              Nome completo
              <input name="name" minLength={3} maxLength={100} required value={createForm.name} onChange={(event) => setCreateForm({ ...createForm, name: event.target.value })} />
            </label>
            <label>
              Posição
              <select name="position" value={createForm.position} onChange={(event) => setCreateForm({ ...createForm, position: event.target.value })}>
                {positions.map((position) => <option key={position}>{position}</option>)}
              </select>
            </label>
            <NumberField label="Agilidade" name="agility" min={1} max={100} value={createForm.agility} onChange={(value) => setCreateForm({ ...createForm, agility: value })} />
            <NumberField label="Idade" name="age" min={16} max={45} value={createForm.age} onChange={(value) => setCreateForm({ ...createForm, age: value })} />
            {numericFields.map(([field, label]) => (
              <NumberField key={field} label={label} name={field} min={1} max={99} value={createForm[field]} onChange={(value) => setCreateForm({ ...createForm, [field]: value })} />
            ))}
            <div className="form-actions wide-field">
              <button className="button" type="button" onClick={() => setShowCreate(false)}>Cancelar</button>
              <button className="button button-primary" disabled={busy}>Cadastrar jogador</button>
            </div>
          </form>
        </Modal>
      )}

      {editing && (
        <Modal title={`Editar ${editing.name}`} onClose={() => setEditing(null)}>
          <form className="form-grid" onSubmit={submitEdit}>
            <label className="wide-field">
              Nome completo
              <input name="name" defaultValue={editing.name} minLength={3} maxLength={100} required />
            </label>
            <label>
              Posição
              <select name="position" defaultValue={editing.position}>
                {positions.map((position) => <option key={position}>{position}</option>)}
              </select>
            </label>
            <NumberField label="Agilidade" name="agility" min={1} max={100} defaultValue={editing.agility} />
            <NumberField label="Idade" name="age" min={editing.age} max={45} defaultValue={editing.age} />
            <div className="form-actions wide-field">
              <button className="button" type="button" onClick={() => setEditing(null)}>Cancelar</button>
              <button className="button button-primary" disabled={busy}>Salvar alterações</button>
            </div>
          </form>
        </Modal>
      )}

      {buying && (
        <Modal title={`Comprar ${buying.name}`} onClose={() => setBuying(null)}>
          <form className="form-grid" onSubmit={submitBuy}>
            <label className="wide-field">
              Clube comprador
              <select name="club_id" required defaultValue="">
                <option value="" disabled>Selecione um clube</option>
                {clubs.map((club) => (
                  <option key={club.id} value={club.id}>{club.name} · caixa {money(club.cash)}</option>
                ))}
              </select>
            </label>
            <label className="wide-field">
              Fim da fidelidade (horário de Brasília)
              <input name="loyalty_until" type="datetime-local" defaultValue={dateTimeInputDefault()} required />
            </label>
            <p className="form-hint wide-field">
              Valor de mercado atual: <strong>{money(buying.market_value)}</strong>. O caixa e as taxas serão calculados pela API.
            </p>
            <div className="form-actions wide-field">
              <button className="button" type="button" onClick={() => setBuying(null)}>Cancelar</button>
              <button className="button button-primary" disabled={busy}>Confirmar compra</button>
            </div>
          </form>
        </Modal>
      )}
    </section>
  )
}

function NumberField({
  label,
  name,
  min,
  max,
  value,
  defaultValue,
  onChange,
}: {
  label: string
  name: string
  min: number
  max: number
  value?: string
  defaultValue?: number
  onChange?: (value: string) => void
}) {
  return (
    <label>
      {label}
      <input
        name={name}
        type="number"
        min={min}
        max={max}
        required
        value={value}
        defaultValue={defaultValue}
        onChange={onChange ? (event) => onChange(event.target.value) : undefined}
      />
    </label>
  )
}

function Modal({
  title,
  onClose,
  children,
}: {
  title: string
  onClose: () => void
  children: React.ReactNode
}) {
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose()
    }}>
      <section className="modal-card" role="dialog" aria-modal="true" aria-label={title}>
        <header className="modal-heading">
          <h2>{title}</h2>
          <button className="icon-button" aria-label="Fechar" onClick={onClose}>×</button>
        </header>
        {children}
      </section>
    </div>
  )
}

import type {
  Club,
  Lineup,
  MatchSummary,
  Player,
  PlayerList,
  Standing,
  TransactionHistory,
} from './types'

const API_URL =
  import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
      ...init?.headers,
    },
  })

  if (response.status === 204) {
    return undefined as T
  }

  const contentType = response.headers.get('content-type') ?? ''
  const payload: unknown = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const message =
      typeof payload === 'object' &&
      payload !== null &&
      'message' in payload &&
      typeof payload.message === 'string'
        ? payload.message
        : `A API respondeu com o status ${response.status}.`
    throw new ApiError(message, response.status)
  }

  return payload as T
}

function queryString(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') search.set(key, String(value))
  })
  const value = search.toString()
  return value ? `?${value}` : ''
}

export const api = {
  players(params: Record<string, string | number | undefined> = {}) {
    return request<PlayerList>(`/players${queryString(params)}`)
  },
  player(id: number) {
    return request<Player>(`/players/${id}`)
  },
  createPlayer(input: Record<string, string | number>) {
    return request<Player>('/players', {
      method: 'POST',
      body: JSON.stringify(input),
    })
  },
  updatePlayer(id: number, input: Record<string, string | number>) {
    return request<Player>(`/players/${id}`, {
      method: 'PUT',
      body: JSON.stringify(input),
    })
  },
  updateCondition(id: number, condition: string) {
    return request<Player>(`/players/${id}/condition`, {
      method: 'PATCH',
      body: JSON.stringify({ condition }),
    })
  },
  deletePlayer(id: number) {
    return request<void>(`/players/${id}`, { method: 'DELETE' })
  },
  clubs(sort = 'name') {
    return request<Club[]>(`/clubs${queryString({ sort })}`)
  },
  club(id: number) {
    return request<Club>(`/clubs/${id}`)
  },
  createClub(input: { name: string; acronym: string }) {
    return request<Club>('/clubs', {
      method: 'POST',
      body: JSON.stringify(input),
    })
  },
  buy(id: number, input: { club_id: number; loyalty_until: string }) {
    return request<Record<string, unknown>>(`/players/${id}/buy`, {
      method: 'POST',
      body: JSON.stringify(input),
    })
  },
  sell(id: number) {
    return request<Record<string, unknown>>(`/players/${id}/sell`, {
      method: 'POST',
    })
  },
  transactions(
    clubId: number,
    params: { type?: string; player_id?: number } = {},
  ) {
    return request<TransactionHistory>(
      `/clubs/${clubId}/transactions${queryString(params)}`,
    )
  },
  exportTransactions(
    clubId: number,
    params: { type?: string; player_id?: number } = {},
  ) {
    return fetch(
      `${API_URL}/clubs/${clubId}/transactions/export${queryString(params)}`,
    ).then(async (response) => {
      if (!response.ok) {
        const payload: unknown = await response.json()
        const message =
          typeof payload === 'object' &&
          payload !== null &&
          'message' in payload &&
          typeof payload.message === 'string'
            ? payload.message
            : `A API respondeu com o status ${response.status}.`
        throw new ApiError(message, response.status)
      }
      return response.blob()
    })
  },
  lineup(clubId: number) {
    return request<Lineup>(`/clubs/${clubId}/lineup`)
  },
  saveLineup(
    clubId: number,
    input: { formation: string; player_ids: number[] },
  ) {
    return request<Lineup>(`/clubs/${clubId}/lineup`, {
      method: 'PUT',
      body: JSON.stringify(input),
    })
  },
  playMatch(input: { home_club_id: number; away_club_id: number }) {
    return request<MatchSummary>('/matches', {
      method: 'POST',
      body: JSON.stringify(input),
    })
  },
  matches(clubId?: number) {
    return request<MatchSummary[]>(
      `/matches${queryString({ club_id: clubId })}`,
    )
  },
  match(id: number) {
    return request<MatchSummary>(`/matches/${id}`)
  },
  standings() {
    return request<Standing[]>('/standings')
  },
}

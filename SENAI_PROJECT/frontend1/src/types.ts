export type Position = 'GOL' | 'ZAG' | 'LAT' | 'MEI' | 'ATA'
export type Condition = 'APTO' | 'MAL_CONDICIONADO' | 'DOENTE'
export type Formation = '3-1' | '2-2' | '2-1-1' | '1-2-1'

export interface Player {
  id: number
  name: string
  position: Position
  agility: number
  age: number
  condition: Condition
  base_value: number
  market_value: number
  pace: number
  shooting: number
  passing: number
  dribbling: number
  defending: number
  physical: number
  potential: number
  overall: number
  club_id: number | null
  contract?: ContractDetails
}

export interface ContractDetails {
  purchase_value: number
  loyalty_until: string
  remaining_days: number
  penalty_rate: number
}

export interface Club {
  id: number
  name: string
  acronym: string
  cash: number
  squad_value: number
  net_worth: number
  players?: Player[]
}

export interface PlayerList {
  data: Player[]
  meta: {
    page: number
    limit: number
    total_items: number
    total_pages: number
  }
}

export interface Transaction {
  id: number
  club_id: number
  player_id: number
  player_name: string
  type: 'COMPRA' | 'VENDA'
  value: number
  fee: number
  penalty: number
  profit: number | null
  cash_change: number
  created_at: string
}

export interface TransactionHistory {
  data: Transaction[]
  summary: {
    total_spent: number
    total_received: number
    total_fees: number
    total_penalties: number
    total_profit: number
  }
}

export interface Lineup {
  club_id: number
  formation: Formation | null
  complete: boolean
  players: Player[]
}

export interface DuelPlayer {
  player_id: number
  player_name: string
  position: Position
  condition: Exclude<Condition, 'DOENTE'>
  attribute: string
  value: number
}

export interface MatchDuel {
  order: number
  attacking_club_id: number
  attacker: DuelPlayer
  defender: DuelPlayer
  goal: boolean
}

export interface MatchSummary {
  id: number
  played_at: string
  home: {
    club_id: number
    club_name: string
    formation: Formation
    goals: number
  }
  away: {
    club_id: number
    club_name: string
    formation: Formation
    goals: number
  }
  result: 'MANDANTE' | 'VISITANTE' | 'EMPATE'
  duels?: MatchDuel[]
}

export interface Standing {
  position: number
  club_id: number
  club_name: string
  played: number
  wins: number
  draws: number
  losses: number
  goals_for: number
  goals_against: number
  goal_difference: number
  points: number
}

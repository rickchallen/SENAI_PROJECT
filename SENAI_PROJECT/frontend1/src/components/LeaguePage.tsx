import { useEffect, useState, type FormEvent } from 'react'

import { api } from '../api'
import { localDate } from '../format'
import type { Club, MatchSummary, Standing } from '../types'
import type { ActionRunner } from './shared'

export function LeaguePage({
  refreshToken,
  busy,
  run,
}: {
  refreshToken: number
  busy: boolean
  run: ActionRunner
}) {
  const [tab, setTab] = useState<'matches' | 'standings'>('matches')
  const [clubs, setClubs] = useState<Club[]>([])
  const [clubFilter, setClubFilter] = useState('')
  const [homeClub, setHomeClub] = useState('')
  const [awayClub, setAwayClub] = useState('')
  const [matches, setMatches] = useState<MatchSummary[]>([])
  const [latestMatch, setLatestMatch] = useState<MatchSummary | null>(null)
  const [selectedMatch, setSelectedMatch] = useState<MatchSummary | null>(null)
  const [standings, setStandings] = useState<Standing[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    let active = true
    api.clubs()
      .then((items) => {
        if (active) setClubs(items)
      })
      .catch((error: Error) => {
        if (active) setLoadError(error.message)
      })
    return () => {
      active = false
    }
  }, [refreshToken])

  useEffect(() => {
    let active = true
    const filterId = clubFilter ? Number(clubFilter) : undefined
    Promise.all([api.matches(filterId), api.standings()])
      .then(([matchList, table]) => {
        if (!active) return
        setLoadError('')
        setMatches(matchList)
        setStandings(table)
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
  }, [clubFilter, refreshToken])

  const play = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!homeClub || !awayClub || homeClub === awayClub) return
    const match = await run(
      () =>
        api.playMatch({
          home_club_id: Number(homeClub),
          away_club_id: Number(awayClub),
        }),
      'Partida realizada. Placar e duelos retornados pela API.',
    )
    if (match) {
      const response = match as MatchSummary
      setLatestMatch(response)
      setSelectedMatch(response)
    }
  }

  const openMatch = async (matchId: number) => {
    try {
      setSelectedMatch(await api.match(matchId))
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : 'Não foi possível abrir a partida.')
    }
  }

  return (
    <section className="page-stack">
      <header className="page-heading">
        <div>
          <p className="eyebrow">COMPETIÇÃO</p>
          <h1>Liga</h1>
          <p>Dispute partidas com escalações completas e acompanhe a tabela.</p>
        </div>
        <nav className="segmented-control" aria-label="Área da liga">
          <button className={tab === 'matches' ? 'segment-active' : ''} onClick={() => setTab('matches')}>Partidas</button>
          <button className={tab === 'standings' ? 'segment-active' : ''} onClick={() => setTab('standings')}>Classificação</button>
        </nav>
      </header>

      {tab === 'matches' ? (
        <>
          <section className="panel match-create">
            <div className="panel-heading">
              <div>
                <h2>Jogar partida</h2>
                <p>O resultado é calculado pela API a partir dos seis duelos.</p>
              </div>
              <span className="eyebrow">6 DUELOS</span>
            </div>
            <form className="match-form" onSubmit={play}>
              <label>
                Mandante
                <select required value={homeClub} onChange={(event) => setHomeClub(event.target.value)}>
                  <option value="">Selecione o clube</option>
                  {clubs.map((club) => <option key={club.id} value={club.id}>{club.name}</option>)}
                </select>
              </label>
              <span className="versus">×</span>
              <label>
                Visitante
                <select required value={awayClub} onChange={(event) => setAwayClub(event.target.value)}>
                  <option value="">Selecione o clube</option>
                  {clubs.map((club) => <option key={club.id} value={club.id}>{club.name}</option>)}
                </select>
              </label>
              <button
                className="button button-primary"
                disabled={busy || !homeClub || !awayClub || homeClub === awayClub}
              >
                ▶ Jogar partida
              </button>
            </form>
            <p className="form-hint">Se algum time estiver sem escalação completa, a API informará o motivo.</p>
          </section>

          {latestMatch && selectedMatch?.id === latestMatch.id && (
            <MatchResult match={latestMatch} />
          )}

          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Histórico de partidas</h2>
                <p>Da mais recente para a mais antiga</p>
              </div>
              <label>
                Filtrar clube
                <select value={clubFilter} onChange={(event) => setClubFilter(event.target.value)}>
                  <option value="">Todos os clubes</option>
                  {clubs.map((club) => <option key={club.id} value={club.id}>{club.name}</option>)}
                </select>
              </label>
            </div>
            {loading ? (
              <div className="state-message">Carregando partidas…</div>
            ) : loadError ? (
              <div className="state-message state-error">{loadError}</div>
            ) : !matches.length ? (
              <div className="state-message">Nenhuma partida disputada ainda.</div>
            ) : (
              <div className="table-scroll">
                <table>
                  <thead><tr><th>Data e hora</th><th>Mandante</th><th>Placar</th><th>Visitante</th><th /></tr></thead>
                  <tbody>
                    {matches.map((match) => (
                      <tr key={match.id}>
                        <td>{localDate(match.played_at)}</td>
                        <td>{match.home.club_name}</td>
                        <td><strong>{match.home.goals} × {match.away.goals}</strong></td>
                        <td>{match.away.club_name}</td>
                        <td>
                          <button className="button button-small" onClick={() => void openMatch(match.id)}>
                            Ver duelos
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {selectedMatch && selectedMatch.id !== latestMatch?.id && (
            <MatchResult match={selectedMatch} />
          )}
        </>
      ) : (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Classificação</h2>
              <p>Critérios: pontos, saldo de gols, gols marcados e nome.</p>
            </div>
            <span className="eyebrow">{standings.length} CLUBES</span>
          </div>
          {loading ? (
            <div className="state-message">Calculando classificação…</div>
          ) : loadError ? (
            <div className="state-message state-error">{loadError}</div>
          ) : !standings.length ? (
            <div className="state-message">Cadastre clubes para montar a classificação.</div>
          ) : (
            <div className="table-scroll">
              <table className="standings-table">
                <thead>
                  <tr><th>#</th><th>Clube</th><th>J</th><th>V</th><th>E</th><th>D</th><th>GM</th><th>GS</th><th>SG</th><th>Pts</th></tr>
                </thead>
                <tbody>
                  {standings.map((entry) => (
                    <tr key={entry.club_id} className={entry.position === 1 ? 'leader-row' : ''}>
                      <td><span className="rank-number">{String(entry.position).padStart(2, '0')}</span></td>
                      <td><strong>{entry.club_name}</strong></td>
                      <td>{entry.played}</td><td>{entry.wins}</td><td>{entry.draws}</td>
                      <td>{entry.losses}</td><td>{entry.goals_for}</td>
                      <td>{entry.goals_against}</td>
                      <td>{entry.goal_difference > 0 ? '+' : ''}{entry.goal_difference}</td>
                      <td><strong>{entry.points}</strong></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="table-legend">J jogos · V vitórias · E empates · D derrotas · GM gols marcados · GS gols sofridos · SG saldo · Pts pontos</p>
            </div>
          )}
        </section>
      )}
    </section>
  )
}

function MatchResult({ match }: { match: MatchSummary }) {
  return (
    <section className="panel match-result">
      <div className="scoreboard">
        <div>
          <span className="score-club">{match.home.club_name}</span>
          <strong>{match.home.goals}</strong>
          <small>{match.home.formation}</small>
        </div>
        <span className="score-separator">×</span>
        <div>
          <span className="score-club">{match.away.club_name}</span>
          <strong>{match.away.goals}</strong>
          <small>{match.away.formation}</small>
        </div>
        <div className="score-result">
          <span className="eyebrow">RESULTADO</span>
          <strong>{match.result}</strong>
          <small>{localDate(match.played_at)}</small>
        </div>
      </div>
      <div className="panel-heading duel-heading">
        <div><h3>Duelos da partida</h3><p>Valores calculados pela API no momento do jogo.</p></div>
      </div>
      <div className="duel-grid">
        {match.duels?.map((duel) => (
          <article className={`duel-card ${duel.goal ? 'duel-goal' : ''}`} key={duel.order}>
            <div className="duel-card-heading">
              <span>Duelo {String(duel.order).padStart(2, '0')}</span>
              {duel.goal && <strong>GOL</strong>}
            </div>
            <div className="duel-players">
              <div>
                <small>ATAQUE · {duel.attacker.attribute}</small>
                <strong>{duel.attacker.player_name}</strong>
                <span>{duel.attacker.position} · {duel.attacker.condition}</span>
                <b>{duel.attacker.value}</b>
              </div>
              <span className="duel-vs">×</span>
              <div>
                <small>DEFESA · {duel.defender.attribute}</small>
                <strong>{duel.defender.player_name}</strong>
                <span>{duel.defender.position} · {duel.defender.condition}</span>
                <b>{duel.defender.value}</b>
              </div>
            </div>
          </article>
        ))}
      </div>
      {!match.duels?.length && <p className="state-message">Não há duelos disponíveis para esta partida.</p>}
    </section>
  )
}

import { useState } from 'react'

import './App.css'
import { ClubsPage } from './components/ClubsPage'
import { LeaguePage } from './components/LeaguePage'
import { PlayersPage } from './components/PlayersPage'
import type { ActionRunner } from './components/shared'

type Page = 'players' | 'clubs' | 'league'
type Notice = { type: 'success' | 'error'; message: string } | null

function App() {
  const [page, setPage] = useState<Page>('players')
  const [notice, setNotice] = useState<Notice>(null)
  const [busy, setBusy] = useState(false)
  const [refreshToken, setRefreshToken] = useState(0)

  const run: ActionRunner = async (action, successMessage) => {
    setBusy(true)
    try {
      const response = await action()
      setNotice({ type: 'success', message: successMessage })
      setRefreshToken((current) => current + 1)
      return response
    } catch (error) {
      setNotice({
        type: 'error',
        message: error instanceof Error ? error.message : 'Não foi possível concluir a ação.',
      })
      return undefined
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="app-shell min-h-screen bg-[#f4f6f3] text-[#18231e] antialiased">
      <header className="topbar sticky top-0 z-10 flex items-center justify-between">
        <a className="brand" href="#" onClick={(event) => { event.preventDefault(); setPage('players') }}>
          <span className="brand-icon">⚽</span>
          <span>
            <strong>LIGA<span>5</span></strong>
            <small>GESTÃO DE FUTEBOL</small>
          </span>
        </a>
        <nav className="main-nav" aria-label="Navegação principal">
          <NavButton active={page === 'players'} onClick={() => setPage('players')} icon="◉">
            Jogadores
          </NavButton>
          <NavButton active={page === 'clubs'} onClick={() => setPage('clubs')} icon="▦">
            Clubes
          </NavButton>
          <NavButton active={page === 'league'} onClick={() => setPage('league')} icon="⌁">
            Liga
          </NavButton>
        </nav>
        <div className="topbar-status">
          <span className="live-indicator" />
          <span>Temporada ativa</span>
        </div>
      </header>

      <main className="main-content">
        {notice && (
          <div
            className={`notice notice-${notice.type} rounded-lg shadow-sm`}
            role={notice.type === 'error' ? 'alert' : 'status'}
          >
            <span>{notice.type === 'error' ? '!' : '✓'}</span>
            <p>{notice.message}</p>
            <button
              className="icon-button"
              aria-label="Fechar mensagem"
              onClick={() => setNotice(null)}
            >
              ×
            </button>
          </div>
        )}
        {busy && <div className="busy-strip fixed top-0 z-50 h-1" aria-label="Enviando ação" />}
        {page === 'players' && (
          <PlayersPage refreshToken={refreshToken} busy={busy} run={run} />
        )}
        {page === 'clubs' && (
          <ClubsPage refreshToken={refreshToken} busy={busy} run={run} />
        )}
        {page === 'league' && (
          <LeaguePage refreshToken={refreshToken} busy={busy} run={run} />
        )}
      </main>
      <footer className="app-footer">
        <span>LIGA5 · Gestão esportiva</span>
        <span>Valores e regras processados pela API</span>
      </footer>
    </div>
  )
}

function NavButton({
  active,
  icon,
  onClick,
  children,
}: {
  active: boolean
  icon: string
  onClick: () => void
  children: string
}) {
  return (
    <button
      className={`nav-button ${active ? 'nav-button-active' : ''}`}
      aria-current={active ? 'page' : undefined}
      onClick={onClick}
    >
      <span aria-hidden="true">{icon}</span>
      {children}
    </button>
  )
}

export default App

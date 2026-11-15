import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { playlistAPI } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

export default function SongMix() {
  const { isAuthenticated, loading } = useAuth()
  const [library, setLibrary] = useState(null)
  const [seeds, setSeeds] = useState([])
  const [query, setQuery] = useState('')
  const [length, setLength] = useState(20)
  const [mix, setMix] = useState(null)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  useEffect(() => {
    if (isAuthenticated) api.get('/api/playlists/liked-seeds', { timeout: 90000 }).then(r => setLibrary(r.data.tracks))
      .catch(() => setMessage('Could not load Liked Songs. Reconnect Spotify and try again.'))
  }, [isAuthenticated])
  async function generate() {
    setBusy(true)
    setMessage('')
    setMix(null)
    try {
      const r = await api.post('/api/playlists/song-mix', { seeds, length }, { timeout: 90000 })
      setMix(r.data)
    } catch (e) {
      setMessage(e.response?.data?.detail || 'Could not build this mix. Please try again.')
    } finally { setBusy(false) }
  }
  async function save() {
    setBusy(true)
    try {
      await playlistAPI.saveToSpotify(mix.id)
      setMessage('Playlist saved to Spotify.')
    } catch (e) { setMessage(e.response?.data?.detail || 'Could not save the playlist.') }
    finally { setBusy(false) }
  }
  if (loading) return <p>Loading…</p>
  if (!isAuthenticated) return <Link className="btn-primary" to="/login">Connect Spotify</Link>
  const matches = (library || []).filter(s => [s.name, ...s.artists].join(' ').toLowerCase().includes(query.toLowerCase()))
  return <div className="max-w-3xl mx-auto space-y-6">
    <h1 className="text-4xl font-bold">Start with a song</h1>
    <p>Pick one song to find related tracks, or blend up to five. Select liked songs to discover tracks with similar mood, energy and danceability.</p>
    <section className="card space-y-4">
      <p>Your Liked Songs</p>
      <label className="block">Search by song or artist<input className="input-field w-full" value={query} onChange={e => setQuery(e.target.value)} /></label>
      {library && !library.length && <p>Save a song to Liked Songs on Spotify, then refresh this page.</p>}
      {!library && !message && <p>Loading library…</p>}
      <div className="max-h-64 overflow-y-auto space-y-1">{matches.map(s => <label key={s.id} className="block p-2">
        <input type="checkbox" checked={seeds.includes(s.id)} disabled={busy || (!seeds.includes(s.id) && seeds.length >= 5)}
          onChange={e => setSeeds(e.target.checked ? [...seeds, s.id] : seeds.filter(id => id !== s.id))} /> {s.name} · {s.artists.join(', ')}
      </label>)}</div>
      {seeds.length > 0 && <p>Starting songs: {seeds.map(id => library.find(s => s.id === id)?.name).join(', ')}</p>}
      <label className="block">Up to {length} matches <input type="range" min="1" max="50" value={length} onChange={e => setLength(Number(e.target.value))} /></label>
      <button className="btn-primary" disabled={!seeds.length || busy} onClick={generate}>{busy ? 'Working…' : 'Find related songs'}</button>
    </section>
    {message && <p role="status">{message}</p>}
    {mix && <section className="card space-y-4"><h2 className="text-2xl font-bold">{mix.tracks.length} related songs</h2>
      {mix.catalog_unavailable && <p>Spotify catalog search was unavailable. Some catalog matches may be missing.</p>}
      {mix.tracks.map(t => <div key={t.id}><a className="text-spotify-green" href={'https://open.spotify.com/track/' + t.id} target="_blank" rel="noreferrer">{t.name} · {t.artists.join(', ')}</a><p className="text-gray-400">{t.reason}</p></div>)}
      <button className="btn-primary" disabled={busy} onClick={save}>Save to Spotify</button>
    </section>}
  </div>
}

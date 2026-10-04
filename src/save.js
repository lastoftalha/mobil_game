// Persistent progress. Storage can be unavailable (private mode), so every access is guarded.
const Save = (() => {
  const KEY = 'nova-armada-v1';
  const defaults = () => ({
    credits: 0, best: 0, bestSector: 1, ship: 'sahin', owned: { sahin: true },
    up: { power: 0, rate: 0, hull: 0, magnet: 0, nova: 0 },
    music: true, sfx: true, vibe: true, tutorial: true, runs: 0,
  });
  let data = defaults();
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const d = JSON.parse(raw);
      data = Object.assign(defaults(), d, { up: Object.assign(defaults().up, d.up), owned: Object.assign({ sahin: true }, d.owned) });
    }
  } catch (e) { /* ignore */ }
  return {
    get d() { return data; },
    write() { try { localStorage.setItem(KEY, JSON.stringify(data)); } catch (e) { /* ignore */ } },
    reset() { data = defaults(); this.write(); },
    ship() { return SHIPS.find(s => s.id === data.ship) || SHIPS[0]; },
  };
})();

function vibrate(ms) {
  if (!Save.d.vibe) return;
  try { navigator.vibrate && navigator.vibrate(ms); } catch (e) { /* ignore */ }
}

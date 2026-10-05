// Thin wrapper over Phaser sound: music crossfades, per-key rate limiting for busy SFX.
const Sfx = {
  game: null, music: null, musicKey: null, last: {},
  init(game) { this.game = game; },
  play(key, opts = {}) {
    if (!Save.d.sfx || !this.game || !this.game.cache.audio.exists(key)) return;
    const now = performance.now();
    const gap = opts.gap ?? 40;
    if (this.last[key] && now - this.last[key] < gap) return;
    this.last[key] = now;
    try { this.game.sound.play(key, { volume: opts.volume ?? 0.6, rate: opts.rate ?? 1, detune: opts.detune ?? 0 }); } catch (e) { /* ignore */ }
  },
  playMusic(key, volume = 0.45) {
    if (this.musicKey === key && this.music) return;
    const old = this.music;
    if (old) this.fade(old, 0, 600, () => old.destroy());
    this.musicKey = key;
    this.music = null;
    // A track that failed to load or decode must never stop the game from running.
    if (!key || !Save.d.music || !this.game || !this.game.cache.audio.exists(key)) return;
    try {
      this.music = this.game.sound.add(key, { loop: true, volume: 0 });
      this.music.play();
      this.fade(this.music, volume, 900);
    } catch (e) { this.music = null; }
  },
  fade(snd, to, ms, done) {
    const from = snd.volume, start = performance.now();
    const step = () => {
      const k = Math.min(1, (performance.now() - start) / ms);
      try { snd.setVolume(from + (to - from) * k); } catch (e) { return; }
      if (k < 1) requestAnimationFrame(step); else if (done) done();
    };
    step();
  },
  setMusicEnabled(on) {
    Save.d.music = on; Save.write();
    const key = this.musicKey;
    if (!on && this.music) { this.music.destroy(); this.music = null; }
    else if (on && key) { this.musicKey = null; this.playMusic(key); }
  },
};

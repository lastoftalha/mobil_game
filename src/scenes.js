// Boot, menu, hangar and overlay scenes.

class BootScene extends Phaser.Scene {
  constructor() { super('Boot'); }
  preload() {
    const H = this.scale.height;
    this.cameras.main.setBackgroundColor(COLORS.ink);
    const title = this.add.text(W / 2, H / 2 - 70, 'NOVA ARMADA', { fontFamily: FONT, fontSize: '44px', fontStyle: '800', color: CSS.text }).setOrigin(0.5);
    title.setLetterSpacing(6);
    const frame = this.add.graphics();
    frame.lineStyle(2, COLORS.line, 0.6).strokeRect(W / 2 - 220, H / 2, 440, 18);
    const bar = this.add.graphics();
    const pct = this.add.text(W / 2, H / 2 + 52, 'YÜKLENİYOR', { fontFamily: FONT, fontSize: '20px', color: CSS.muted }).setOrigin(0.5);
    this.load.on('progress', (p) => {
      bar.clear().fillStyle(COLORS.line, 1).fillRect(W / 2 - 216, H / 2 + 4, 432 * p, 10);
      pct.setText('YÜKLENİYOR  %' + Math.round(p * 100));
    });
    this.load.atlas('game', 'assets/img/game.png', 'assets/img/game.json');
    this.load.atlas('planets', 'assets/img/planets.png', 'assets/img/planets.json');
    ['black', 'blue', 'darkPurple', 'purple'].forEach(b => this.load.image('bg_' + b, `assets/img/bg_${b}.png`));
    ['shoot', 'eshoot', 'hit', 'explode', 'explode_big', 'coin', 'powerup', 'shield_up', 'shield_down', 'hurt', 'lose', 'nova',
      'warning', 'click', 'select', 'buy', 'error', 'wave', 'win', 'gameover', 'missile', 'music_menu', 'music_game', 'music_boss']
      .forEach(k => this.load.audio(k, `assets/audio/${k}.mp3`));
  }
  create() {
    makeTextures(this);
    Sfx.init(this.game);
    const go = () => this.scene.start('Menu');
    if (document.fonts && document.fonts.load) {
      Promise.race([
        Promise.all([document.fonts.load(`800 40px ${FONT}`), document.fonts.load(`600 20px ${FONT}`)]),
        new Promise(r => setTimeout(r, 2500)),
      ]).then(go, go);
    } else go();
  }
}

// Makes the ship sprite with an animated engine flame; reused in menu, hangar and game.
function shipWithFlame(scene, x, y, ship, scale = 1) {
  const c = scene.add.container(x, y);
  const flame = scene.add.image(0, 34 * 1, 'game', 'fire08').setOrigin(0.5, 0).setBlendMode('ADD').setTint(ship.tint);
  const glow = scene.add.image(0, 44, 'game', 'fx_light_01').setScale(0.6).setBlendMode('ADD').setTint(ship.tint).setAlpha(0.6);
  const body = scene.add.image(0, 0, 'game', ship.frame);
  c.add([glow, flame, body]);
  c.setScale(scale);
  scene.tweens.add({ targets: flame, scaleY: { from: 0.8, to: 1.25 }, scaleX: { from: 1, to: 0.85 }, duration: 90, yoyo: true, repeat: -1 });
  c.body_ = body; c.flame = flame;
  return c;
}

class MenuScene extends Phaser.Scene {
  constructor() { super('Menu'); }
  create() {
    const H = this.scale.height, safe = safeInsets(this);
    this.bg = new SpaceBG(this, 0);
    Sfx.playMusic('music_menu', 0.4);
    this.cameras.main.fadeIn(500, 7, 11, 26);

    // Distant flagship silhouette for scale and threat.
    const boss = this.add.image(W * 0.5, H * 0.2, 'game', 'spaceShips_005').setScale(1.5).setTint(0x1a2448).setAlpha(0.85).setDepth(-50);
    this.tweens.add({ targets: boss, y: H * 0.2 + 24, duration: 4000, yoyo: true, repeat: -1, ease: 'Sine.InOut' });

    const ty = safe.top + H * 0.17;
    const nova = txt(this, W / 2, ty, 'NOVA', 150, CSS.text, { weight: '800', glow: '#47E0FF', glowBlur: 28 });
    const grad = nova.context.createLinearGradient(0, 0, 0, nova.height);
    grad.addColorStop(0.15, '#FFFFFF'); grad.addColorStop(0.6, '#8BEFFF'); grad.addColorStop(1, '#2C8DD6');
    nova.setFill(grad);
    nova.setLetterSpacing(10);
    txt(this, W / 2, ty + 92, 'A  R  M  A  D  A', 40, CSS.gold, { weight: '800', spacing: 6 });
    const line = this.add.graphics();
    line.lineStyle(2, COLORS.line, 0.6).lineBetween(W / 2 - 250, ty + 130, W / 2 - 40, ty + 130).lineBetween(W / 2 + 40, ty + 130, W / 2 + 250, ty + 130);
    line.fillStyle(COLORS.line, 1).fillRect(W / 2 - 6, ty + 124, 12, 12);
    txt(this, W / 2, ty + 166, 'Sektörleri temizle. Amiralleri düşür.', 24, CSS.muted, { weight: '600' });

    const ship = Save.ship();
    this.ship = shipWithFlame(this, W / 2, H * 0.53, ship, 1.5);
    this.tweens.add({ targets: this.ship, y: H * 0.53 - 18, duration: 1800, yoyo: true, repeat: -1, ease: 'Sine.InOut' });
    this.add.particles(0, 0, 'game', {
      frame: 'fx_circle_05', follow: this.ship, followOffset: { x: 0, y: 70 }, lifespan: 600, speedY: { min: 200, max: 320 },
      speedX: { min: -20, max: 20 }, scale: { start: 0.22, end: 0 }, alpha: { start: 0.6, end: 0 }, blendMode: 'ADD',
      tint: ship.tint, frequency: 30,
    }).setDepth(-1);

    const by = H * 0.69;
    button(this, W / 2, by, 460, 104, 'SAVAŞA BAŞLA', () => this.go('Game'), 'primary', { size: 38 });
    button(this, W / 2 - 118, by + 132, 222, 84, 'HANGAR', () => this.go('Hangar'), 'ghost', { size: 26 });
    button(this, W / 2 + 118, by + 132, 222, 84, 'AYARLAR', () => this.scene.launch('Settings', { from: 'Menu' }) && this.scene.pause(), 'ghost', { size: 26 });

    chip(this, 30, safe.top + 46, 'star_gold', Save.d.credits.toLocaleString('tr-TR'), CSS.gold, 0);
    chip(this, W - 30, safe.top + 46, 'things_gold', 'REKOR ' + Save.d.best.toLocaleString('tr-TR'), CSS.text, 1);

    txt(this, W / 2, H - safe.bottom - 34, 'v1.0  ·  Görseller ve sesler: Kenney.nl, OpenGameArt (CC0)', 18, CSS.muted, { weight: '600' }).setAlpha(0.7);
    this.input.keyboard?.on('keydown-ENTER', () => this.go('Game'));
  }
  go(key) {
    if (this.leaving) return;
    this.leaving = true;
    this.cameras.main.fadeOut(300, 7, 11, 26);
    this.cameras.main.once('camerafadeoutcomplete', () => this.scene.start(key));
  }
  update(_, dms) { this.bg.update(dms / 1000); }
}

class HangarScene extends Phaser.Scene {
  constructor() { super('Hangar'); }
  create() {
    const H = this.scale.height, safe = safeInsets(this);
    this.bg = new SpaceBG(this, 1);
    this.cameras.main.fadeIn(300, 7, 11, 26);
    const top = safe.top + 50;
    button(this, 86, top, 132, 70, 'GERİ', () => this.back(), 'ghost', { size: 24, sound: 'select' });
    txt(this, W / 2, top, 'HANGAR', 40, CSS.text, { weight: '800', spacing: 6 });
    this.credits = chip(this, W - 26, top, 'star_gold', '', CSS.gold, 1);

    // Ship selector
    this.idx = Math.max(0, SHIPS.findIndex(s => s.id === Save.d.ship));
    const sy = top + 70;
    panel(this, W / 2, sy + 255, 660, 510);
    this.shipName = txt(this, W / 2, sy + 48, '', 40, CSS.text, { weight: '800', spacing: 4 });
    this.shipDesc = txt(this, W / 2, sy + 90, '', 22, CSS.muted, { weight: '600' });
    const pad = this.add.image(W / 2, sy + 230, 'ring').setScale(1.0, 0.32).setTint(COLORS.line).setAlpha(0.6).setBlendMode('ADD');
    this.tweens.add({ targets: pad, alpha: 0.25, duration: 1200, yoyo: true, repeat: -1 });
    this.preview = null; this.previewY = sy + 175;
    button(this, 70, sy + 175, 72, 96, '‹', () => this.cycle(-1), 'ghost', { size: 56, sound: 'select' });
    button(this, W - 70, sy + 175, 72, 96, '›', () => this.cycle(1), 'ghost', { size: 56, sound: 'select' });

    this.stats = ['GÖVDE', 'GÜÇ', 'ATIŞ HIZI', 'MANEVRA'].map((label, i) => {
      const y = sy + 290 + i * 34;
      txt(this, 80, y, label, 20, CSS.muted, { weight: '700', ox: 0 });
      const g = this.add.graphics();
      return { y, g };
    });
    this.shipBtn = button(this, W / 2, sy + 455, 400, 78, '', () => this.shipAction(), 'primary', { size: 28 });

    // Upgrades
    const uy = sy + 545;
    txt(this, 40, uy, 'KALICI YÜKSELTMELER', 22, CSS.line, { weight: '800', ox: 0, spacing: 3 });
    const rowH = Math.min(112, (H - safe.bottom - uy - 40) / UPGRADES.length);
    this.rows = UPGRADES.map((u, i) => {
      const y = uy + 36 + rowH * i + rowH / 2;
      panel(this, W / 2, y, 660, rowH - 12, { flat: true });
      this.add.image(70, y, 'game', u.icon).setScale(Math.min(1.1, rowH / 85));
      txt(this, 112, y - 16, u.name, 24, CSS.text, { weight: '800', ox: 0 });
      txt(this, 112, y + 16, u.desc, 18, CSS.muted, { weight: '600', ox: 0 });
      const pips = this.add.graphics();
      const btn = button(this, W - 104, y, 150, Math.min(66, rowH - 30), '', () => this.buy(u), 'gold', { size: 24, icon: 'star_gold', iconScale: 0.7, sound: 'buy' });
      return { u, y, pips, btn };
    });
    this.refresh();
    this.input.keyboard?.on('keydown-ESC', () => this.back());
  }
  cycle(d) {
    this.idx = (this.idx + d + SHIPS.length) % SHIPS.length;
    const s = SHIPS[this.idx];
    if (Save.d.owned[s.id]) { Save.d.ship = s.id; Save.write(); }
    this.refresh(d);
  }
  shipAction() {
    const s = SHIPS[this.idx];
    if (Save.d.owned[s.id]) { Save.d.ship = s.id; Save.write(); this.refresh(); return; }
    if (Save.d.credits < s.cost) { Sfx.play('error'); this.cameras.main.shake(120, 0.004); return; }
    Save.d.credits -= s.cost; Save.d.owned[s.id] = true; Save.d.ship = s.id; Save.write();
    Sfx.play('buy'); Sfx.play('powerup');
    this.refresh();
    this.burst(W / 2, this.previewY);
  }
  buy(u) {
    const lvl = Save.d.up[u.id];
    if (lvl >= 5) { Sfx.play('error'); return; }
    const cost = UPGRADE_COST[lvl];
    if (Save.d.credits < cost) { this.cameras.main.shake(120, 0.004); Sfx.play('error'); return; }
    Save.d.credits -= cost; Save.d.up[u.id]++; Save.write();
    this.refresh();
    const row = this.rows.find(r => r.u === u);
    this.burst(W - 104, row.y);
  }
  burst(x, y) {
    const p = this.add.particles(x, y, 'game', { frame: 'fx_star_06', lifespan: 600, speed: { min: 120, max: 320 }, scale: { start: 0.3, end: 0 },
      blendMode: 'ADD', tint: [COLORS.gold, COLORS.line], emitting: false });
    p.explode(24);
    this.time.delayedCall(800, () => p.destroy());
  }
  refresh(dir = 0) {
    const s = SHIPS[this.idx];
    const owned = !!Save.d.owned[s.id];
    this.credits.setValue(Save.d.credits.toLocaleString('tr-TR'));
    this.shipName.setText(s.name).setColor(Phaser.Display.Color.IntegerToColor(s.tint).rgba);
    this.shipDesc.setText(s.desc);
    if (this.preview) {
      const old = this.preview;
      this.tweens.add({ targets: old, x: W / 2 - dir * 300, alpha: 0, duration: 220, onComplete: () => old.destroy() });
    }
    this.preview = shipWithFlame(this, W / 2 + dir * 300, this.previewY, s, 1.45).setAlpha(dir ? 0 : 1);
    if (!owned) this.preview.body_.setTint(0x55607e);
    this.tweens.add({ targets: this.preview, x: W / 2, alpha: 1, duration: 260, ease: 'Cubic.Out' });
    const vals = [s.hull / 7, s.power / 1.4, s.rate / 1.35, s.speed / 1.15];
    this.stats.forEach((st, i) => {
      st.g.clear();
      for (let k = 0; k < 10; k++) {
        const on = k < Math.round(vals[i] * 10);
        st.g.fillStyle(on ? s.tint : COLORS.panelHi, on ? 1 : 0.9).fillRect(230 + k * 41, st.y - 8, 35, 16);
      }
    });
    if (owned && Save.d.ship === s.id) { this.shipBtn.setLabel('KULLANIMDA'); this.shipBtn.setVariant('ghost'); }
    else if (owned) { this.shipBtn.setLabel('SEÇ'); this.shipBtn.setVariant('primary'); }
    else { this.shipBtn.setLabel('SATIN AL  ' + s.cost.toLocaleString('tr-TR')); this.shipBtn.setVariant(Save.d.credits >= s.cost ? 'gold' : 'off'); }
    this.rows.forEach(r => {
      const lvl = Save.d.up[r.u.id];
      r.pips.clear();
      for (let k = 0; k < 5; k++) {
        r.pips.fillStyle(k < lvl ? COLORS.line : COLORS.muted, k < lvl ? 1 : 0.3).fillRect(412 + k * 22, r.y - 22, 16, 8);
      }
      if (lvl >= 5) { r.btn.setLabel('MAKS'); r.btn.setVariant('off'); }
      else { const c = UPGRADE_COST[lvl]; r.btn.setLabel(c.toLocaleString('tr-TR')); r.btn.setVariant(Save.d.credits >= c ? 'gold' : 'off'); }
    });
  }
  back() {
    this.cameras.main.fadeOut(250, 7, 11, 26);
    this.cameras.main.once('camerafadeoutcomplete', () => this.scene.start('Menu'));
  }
  update(_, dms) { this.bg.update(dms / 1000); }
}

// Modal overlay helpers shared by Settings, Pause and Game Over.
function overlayBase(scene, w, h) {
  const H = scene.scale.height;
  const shade = scene.add.image(W / 2, H / 2, 'shade').setDisplaySize(W, H).setInteractive();
  const p = panel(scene, W / 2, H / 2, w, h);
  const items = scene.add.container(0, 0);
  [shade, p].forEach(o => o.setAlpha(0));
  scene.tweens.add({ targets: shade, alpha: 1, duration: 200 });
  p.setScale(0.9);
  scene.tweens.add({ targets: p, alpha: 1, scale: 1, duration: 260, ease: 'Back.Out' });
  return { top: H / 2 - h / 2, H };
}

function toggleRow(scene, y, label, get, set) {
  txt(scene, 130, y, label, 28, CSS.text, { weight: '700', ox: 0 });
  const b = button(scene, W - 190, y, 150, 64, '', () => { set(!get()); paint(); }, 'primary', { size: 24, sound: 'select' });
  const paint = () => { b.setLabel(get() ? 'AÇIK' : 'KAPALI'); b.setVariant(get() ? 'primary' : 'off'); };
  paint();
  return b;
}

class SettingsScene extends Phaser.Scene {
  constructor() { super('Settings'); }
  create(data) {
    const { top } = overlayBase(this, 600, 640);
    txt(this, W / 2, top + 60, 'AYARLAR', 38, CSS.text, { weight: '800', spacing: 6 });
    toggleRow(this, top + 160, 'Müzik', () => Save.d.music, (v) => Sfx.setMusicEnabled(v));
    toggleRow(this, top + 250, 'Ses Efektleri', () => Save.d.sfx, (v) => { Save.d.sfx = v; Save.write(); });
    toggleRow(this, top + 340, 'Titreşim', () => Save.d.vibe, (v) => { Save.d.vibe = v; Save.write(); vibrate(40); });
    let armed = false;
    const reset = button(this, W / 2, top + 450, 420, 70, 'İLERLEMEYİ SIFIRLA', () => {
      if (!armed) { armed = true; reset.setLabel('EMİN MİSİN? TEKRAR DOKUN'); return; }
      Save.reset(); Sfx.setMusicEnabled(true);
      this.scene.stop(data.from); this.scene.start(data.from);
    }, 'danger', { size: 22 });
    button(this, W / 2, top + 560, 300, 80, 'TAMAM', () => { this.scene.resume(data.from); this.scene.stop(); }, 'primary', { size: 30 });
  }
}

class PauseScene extends Phaser.Scene {
  constructor() { super('Pause'); }
  create() {
    const { top } = overlayBase(this, 600, 620);
    txt(this, W / 2, top + 64, 'DURAKLATILDI', 40, CSS.text, { weight: '800', spacing: 6 });
    toggleRow(this, top + 170, 'Müzik', () => Save.d.music, (v) => Sfx.setMusicEnabled(v));
    toggleRow(this, top + 255, 'Ses Efektleri', () => Save.d.sfx, (v) => { Save.d.sfx = v; Save.write(); });
    button(this, W / 2, top + 385, 400, 92, 'DEVAM ET', () => this.resume(), 'primary', { size: 34 });
    button(this, W / 2, top + 515, 400, 76, 'ANA MENÜ', () => {
      this.scene.get('Game').endRun(true);
      this.scene.stop('Game'); this.scene.stop(); this.scene.start('Menu');
    }, 'ghost', { size: 26 });
    this.input.keyboard?.on('keydown-ESC', () => this.resume());
    this.input.keyboard?.on('keydown-P', () => this.resume());
  }
  resume() { this.scene.resume('Game'); this.scene.stop(); }
}

class GameOverScene extends Phaser.Scene {
  constructor() { super('GameOver'); }
  create(r) {
    const { top } = overlayBase(this, 640, 820);
    Sfx.playMusic('music_menu', 0.35);
    txt(this, W / 2, top + 70, 'GEMİ KAYBEDİLDİ', 40, CSS.danger, { weight: '800', spacing: 4 });
    txt(this, W / 2, top + 130, 'SKOR', 22, CSS.muted, { weight: '700', spacing: 4 });
    const score = txt(this, W / 2, top + 192, '0', 84, CSS.text, { weight: '800', glow: '#47E0FF', glowBlur: 20 });
    this.tweens.addCounter({ from: 0, to: r.score, duration: 900, ease: 'Cubic.Out', onUpdate: (t) => score.setText(Math.round(t.getValue()).toLocaleString('tr-TR')) });
    if (r.record) {
      const b = txt(this, W / 2, top + 262, 'YENİ REKOR!', 30, CSS.gold, { weight: '800', spacing: 4, glow: '#FFC23D' });
      this.tweens.add({ targets: b, scale: 1.12, duration: 500, yoyo: true, repeat: -1 });
      Sfx.play('win', { volume: 0.7 });
    } else {
      txt(this, W / 2, top + 262, 'Rekor: ' + Save.d.best.toLocaleString('tr-TR'), 24, CSS.muted, { weight: '600' });
    }
    const rows = [
      ['Ulaşılan sektör', `${r.sector}  ·  ${SECTORS[(r.sector - 1) % SECTORS.length].name}`],
      ['Yok edilen düşman', r.kills.toLocaleString('tr-TR')],
      ['En yüksek kombo', 'x' + r.maxCombo],
      ['Kazanılan kredi', '+' + r.credits.toLocaleString('tr-TR')],
    ];
    const g = this.add.graphics();
    rows.forEach((row, i) => {
      const y = top + 330 + i * 62;
      g.lineStyle(1, COLORS.line, 0.18).lineBetween(W / 2 - 260, y + 31, W / 2 + 260, y + 31);
      txt(this, W / 2 - 260, y, row[0], 24, CSS.muted, { weight: '600', ox: 0 });
      txt(this, W / 2 + 260, y, row[1], 26, i === 3 ? CSS.gold : CSS.text, { weight: '800', ox: 1 });
    });
    button(this, W / 2, top + 615, 460, 96, 'TEKRAR DENE', () => this.go('Game'), 'primary', { size: 34 });
    button(this, W / 2 - 117, top + 735, 226, 76, 'HANGAR', () => this.go('Hangar'), 'ghost', { size: 24 });
    button(this, W / 2 + 117, top + 735, 226, 76, 'ANA MENÜ', () => this.go('Menu'), 'ghost', { size: 24 });
  }
  go(key) { this.scene.stop('Game'); this.scene.start(key); }
}

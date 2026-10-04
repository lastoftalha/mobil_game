// Core gameplay: player, waves, enemies, bosses, pickups, HUD and effects.
// Movement and collisions are done by hand (circle tests) to keep the frame budget small on phones.

const ENEMY = {
  drone: { n: 1, hp: 2, score: 100, scale: 0.72, cr: 1, nova: 3 },
  weaver: { n: 2, hp: 3, score: 150, scale: 0.72, cr: 1, nova: 4 },
  gunner: { n: 3, hp: 7, score: 300, scale: 0.85, cr: 2, nova: 7 },
  diver: { n: 4, hp: 3, score: 200, scale: 0.72, cr: 1, nova: 5 },
  tank: { n: 5, hp: 20, score: 700, scale: 1.0, cr: 5, nova: 14 },
  ufo: { frame: 'ufoYellow', hp: 14, score: 1000, scale: 0.9, cr: 16, nova: 10 },
  missile: { frame: 'spaceMissiles_004', hp: 2, score: 50, scale: 1.0, cr: 0, nova: 1 },
  meteorL: { hp: 9, score: 120, scale: 1.0, cr: 1, nova: 4 },
  meteorM: { hp: 4, score: 60, scale: 1.0, cr: 0, nova: 2 },
  meteorS: { hp: 1, score: 30, scale: 1.0, cr: 0, nova: 1 },
};
const PICKUP = {
  credit: { frame: 'star_gold', scale: 0.62 },
  bolt: { frame: 'powerupBlue_bolt', scale: 0.95 },
  shield: { frame: 'powerupGreen_shield', scale: 0.95 },
  heal: { frame: 'pill_red', scale: 1.1 },
  nova: { frame: 'powerupYellow_star', scale: 0.95 },
};
// Weapon spread per level: [x offset, angle in degrees]
const PATTERNS = [
  [[-9, 0], [9, 0]],
  [[-15, 0], [0, -2], [15, 0]],
  [[-11, 0], [11, 0], [-24, -7], [24, 7]],
  [[-16, 0], [0, 0], [16, 0], [-26, -9], [26, 9]],
  [[-16, 0], [0, 0], [16, 0], [-26, -8], [26, 8], [-32, -17], [32, 17]],
];

class Pool {
  constructor(scene, make) { this.scene = scene; this.make = make; this.items = []; }
  get() {
    let o = this.items.find(i => !i.active);
    if (!o) { o = this.make(); this.items.push(o); }
    o.setActive(true).setVisible(true);
    return o;
  }
  kill(o) { o.setActive(false).setVisible(false); }
  clear() { this.items.forEach(o => this.kill(o)); }
}

class GameScene extends Phaser.Scene {
  constructor() { super('Game'); }

  create() {
    const H = this.H = this.scale.height;
    this.safe = safeInsets(this);
    const ship = this.shipDef = Save.ship();
    const up = Save.d.up;
    this.maxHp = ship.hull + up.hull;
    this.dmg = ship.power * (1 + 0.12 * up.power);
    this.fireInterval = 1000 / (7.2 * ship.rate * (1 + 0.08 * up.rate));
    this.magnet = 120 + 45 * up.magnet;
    this.novaRate = 1 + 0.2 * up.nova;
    Object.assign(this, {
      score: 0, combo: 0, comboT: 0, mult: 1, maxCombo: 1, kills: 0, creditsRun: 0, sector: 0, wave: 0,
      weapon: 1, hp: this.maxHp, shield: 0, nova: 0, invuln: 0, alive: true, controls: false, ended: false,
      boss: null, pending: 0, waveActive: false, fireCd: 0, missileCd: 0, enemies: [], pickups: [], bossEvents: [],
      beams: [], shownScore: 0,
    });

    this.bg = new SpaceBG(this, 0);
    Sfx.playMusic('music_game', 0.38);
    this.cameras.main.fadeIn(400, 7, 11, 26);

    // Pools
    this.pBullets = new Pool(this, () => this.add.image(0, 0, 'game', ship.laser).setDepth(8));
    this.eBullets = new Pool(this, () => this.add.image(0, 0, 'orb_red').setDepth(12).setBlendMode('ADD'));

    // Effects
    this.sparks = this.add.particles(0, 0, 'game', { frame: 'fx_spark_05', lifespan: 260, speed: { min: 80, max: 260 },
      scale: { start: 0.2, end: 0 }, blendMode: 'ADD', emitting: false, tint: 0xfff1b0 }).setDepth(14);
    this.embers = this.add.particles(0, 0, 'game', { frame: 'fx_circle_05', lifespan: { min: 300, max: 700 }, speed: { min: 120, max: 420 },
      scale: { start: 0.16, end: 0 }, alpha: { start: 1, end: 0 }, blendMode: 'ADD', emitting: false, tint: [0xffd27a, 0xff8a3d, 0xffffff] }).setDepth(14);

    // Player
    this.player = this.add.container(W / 2, H + 120).setDepth(10);
    this.pFlame = this.add.image(0, 30, 'game', 'fire08').setOrigin(0.5, 0).setBlendMode('ADD').setTint(ship.tint);
    this.pGlow = this.add.image(0, 44, 'game', 'fx_light_01').setScale(0.55).setBlendMode('ADD').setTint(ship.tint).setAlpha(0.55);
    this.pBody = this.add.image(0, 0, 'game', ship.frame);
    this.pDamage = this.add.image(0, 0, 'game', ship.dmgFrame + '1').setVisible(false);
    this.pShield = this.add.image(0, -4, 'game', 'shield2').setVisible(false).setBlendMode('ADD');
    this.player.add([this.pGlow, this.pFlame, this.pBody, this.pDamage, this.pShield]);
    this.player.setScale(0.9);
    this.tweens.add({ targets: this.pFlame, scaleY: { from: 0.75, to: 1.2 }, duration: 80, yoyo: true, repeat: -1 });
    this.trail = this.add.particles(0, 0, 'game', { frame: 'fx_circle_05', follow: this.player, followOffset: { x: 0, y: 52 },
      lifespan: 380, speedY: { min: 220, max: 340 }, speedX: { min: -25, max: 25 }, scale: { start: 0.18, end: 0 },
      alpha: { start: 0.55, end: 0 }, blendMode: 'ADD', tint: ship.tint, frequency: 22 }).setDepth(9);
    this.tx = W / 2; this.ty = H * 0.78;
    this.tweens.add({ targets: this.player, y: this.ty, duration: 1100, ease: 'Cubic.Out', onComplete: () => { this.controls = true; } });

    this.setupInput();
    this.buildHUD();
    this.time.delayedCall(700, () => this.startSector());

    const onHide = () => { if (this.alive && this.scene.isActive()) this.pauseGame(); };
    this.game.events.on('hidden', onHide);
    this.events.once('shutdown', () => this.game.events.off('hidden', onHide));
  }

  // ---------------------------------------------------------------- input
  setupInput() {
    this.input.addPointer(1);
    this.drag = null;
    this.input.on('pointerdown', (p, over) => {
      this.pauseBtnDown = over.length > 0;
      if (over.length || !this.controls) return;
      this.drag = { id: p.id, px: p.x, py: p.y, sx: this.tx, sy: this.ty };
    });
    this.input.on('pointermove', (p) => {
      // A finger that went down during the intro (or on nothing) still takes control once it moves.
      if (!this.drag && p.isDown && this.controls && !this.pauseBtnDown) this.drag = { id: p.id, px: p.x, py: p.y, sx: this.tx, sy: this.ty };
      if (!this.drag || this.drag.id !== p.id || !this.controls) return;
      const k = 1.25 * this.shipDef.speed;
      this.tx = this.drag.sx + (p.x - this.drag.px) * k;
      this.ty = this.drag.sy + (p.y - this.drag.py) * k;
      this.clampTarget();
      if (this.hint && Math.abs(p.x - this.drag.px) + Math.abs(p.y - this.drag.py) > 60) this.clearHint();
    });
    this.input.on('pointerup', (p) => { this.pauseBtnDown = false; if (this.drag && this.drag.id === p.id) this.drag = null; });
    const kb = this.input.keyboard;
    if (kb) {
      this.keys = kb.addKeys('W,A,S,D,UP,DOWN,LEFT,RIGHT');
      kb.on('keydown-SPACE', () => this.fireNova());
      kb.on('keydown-ESC', () => this.pauseGame());
      kb.on('keydown-P', () => this.pauseGame());
    }
  }
  clampTarget() {
    this.tx = Phaser.Math.Clamp(this.tx, 40, W - 40);
    this.ty = Phaser.Math.Clamp(this.ty, this.H * 0.22, this.H - this.safe.bottom - 150);
  }
  pauseGame() {
    if (!this.alive || this.ended || this.scene.isPaused()) return;
    this.drag = null;
    this.scene.launch('Pause');
    this.scene.pause();
  }

  // ---------------------------------------------------------------- HUD
  buildHUD() {
    const H = this.H, top = this.safe.top + 50, bot = H - this.safe.bottom;
    const D = 100;
    txt(this, 28, top - 24, 'SKOR', 18, CSS.muted, { weight: '700', ox: 0, spacing: 3 }).setDepth(D);
    this.scoreText = txt(this, 28, top + 10, '0', 40, CSS.text, { weight: '800', ox: 0, glow: '#47E0FF', glowBlur: 10 }).setDepth(D);
    this.comboText = txt(this, 28, top + 56, '', 24, CSS.gold, { weight: '800', ox: 0 }).setDepth(D);
    this.comboBar = this.add.graphics().setDepth(D);
    this.waveText = txt(this, W / 2 + 20, top - 12, '', 18, CSS.muted, { weight: '700', spacing: 2 }).setDepth(D);
    this.waveText2 = txt(this, W / 2 + 20, top + 14, '', 22, CSS.text, { weight: '800', spacing: 2 }).setDepth(D);
    this.creditChip = chip(this, W - 112, top, 'star_gold', '0', CSS.gold, 1).setDepth(D);
    button(this, W - 52, top, 76, 76, 'II', () => this.pauseGame(), 'ghost', { size: 30, sound: 'select' }).setDepth(D);

    // Hull + weapon (bottom-left)
    this.hullIcons = [];
    const iy = bot - 46;
    txt(this, 28, iy - 50, 'GÖVDE', 16, CSS.muted, { weight: '700', ox: 0, spacing: 3 }).setDepth(D);
    for (let i = 0; i < this.maxHp; i++) {
      this.hullIcons.push(this.add.image(44 + i * 38, iy, 'game', this.shipDef.life).setScale(0.95).setDepth(D));
    }
    txt(this, 120, iy - 50, 'SİLAH', 16, CSS.muted, { weight: '700', ox: 0, spacing: 3 }).setDepth(D);
    this.weaponPips = this.add.graphics().setDepth(D);
    this.weaponPipsY = iy - 50;

    // Nova button (bottom-right)
    const nx = W - 92, ny = bot - 92;
    this.novaPos = { x: nx, y: ny };
    this.novaGlow = this.add.image(nx, ny, 'game', 'fx_light_01').setScale(1.6).setBlendMode('ADD').setTint(COLORS.gold).setAlpha(0).setDepth(D);
    this.novaG = this.add.graphics().setDepth(D);
    this.novaIcon = this.add.image(nx, ny - 10, 'game', 'powerupYellow_star').setScale(0.9).setDepth(D);
    this.novaLabel = txt(this, nx, ny + 34, 'NOVA', 18, CSS.text, { weight: '800', spacing: 3 }).setDepth(D);
    const hit = this.add.zone(nx, ny, 140, 140).setInteractive().setDepth(D);
    hit.on('pointerdown', () => this.fireNova());

    // Boss bar
    this.bossUI = this.add.container(0, top + 112).setDepth(D).setVisible(false);
    this.bossName = txt(this, W / 2, -24, '', 22, CSS.danger, { weight: '800', spacing: 4 });
    this.bossBar = this.add.graphics();
    this.bossUI.add([this.bossBar, this.bossName]);

    this.refreshHUD(true);

    if (Save.d.tutorial) {
      this.hint = this.add.container(W / 2, H * 0.62).setDepth(D);
      const ring = this.add.image(0, 0, 'ring').setScale(0.4).setTint(COLORS.line).setBlendMode('ADD');
      const dot = this.add.image(0, 0, 'dot').setScale(3);
      const t = txt(this, 0, 96, 'Gemiyi yönetmek için ekranda\nparmağını sürükle', 28, CSS.text, { weight: '700', glow: '#000000' });
      this.hint.add([ring, dot, t]);
      this.tweens.add({ targets: [ring, dot], x: { from: -120, to: 120 }, duration: 1100, yoyo: true, repeat: -1, ease: 'Sine.InOut' });
      this.tweens.add({ targets: ring, scale: 0.55, alpha: 0.4, duration: 550, yoyo: true, repeat: -1 });
    }
  }
  clearHint() {
    const h = this.hint; this.hint = null;
    this.tweens.add({ targets: h, alpha: 0, duration: 300, onComplete: () => h.destroy() });
    Save.d.tutorial = false; Save.write();
  }
  refreshHUD(force) {
    this.hullIcons.forEach((ic, i) => {
      const on = i < this.hp;
      ic.setAlpha(on ? 1 : 0.22);
      if (on) ic.clearTint(); else ic.setTint(0x334466);
    });
    this.weaponPips.clear();
    for (let i = 0; i < 5; i++) {
      this.weaponPips.fillStyle(i < this.weapon ? COLORS.line : COLORS.panelHi, i < this.weapon ? 1 : 0.9)
        .fillRect(190 + i * 22, this.weaponPipsY - 6, 16, 12);
    }
    this.creditChip.setValue(this.creditsRun.toLocaleString('tr-TR'));
    const r = this.hp / this.maxHp;
    this.pDamage.setVisible(r < 0.8 && this.hp > 0);
    if (r < 0.8) this.pDamage.setFrame(this.shipDef.dmgFrame + (r < 0.3 ? 3 : r < 0.55 ? 2 : 1));
    this.pShield.setVisible(this.shield > 0).setAlpha([0, 0.45, 0.7, 1][this.shield]);
    this.drawNova();
  }
  drawNova() {
    const { x, y } = this.novaPos, g = this.novaG, full = this.nova >= 100;
    g.clear();
    g.fillStyle(COLORS.ink, 0.75).fillCircle(x, y, 62);
    g.lineStyle(6, COLORS.panelHi, 1).strokeCircle(x, y, 56);
    if (this.nova > 0) {
      g.lineStyle(8, full ? COLORS.gold : COLORS.line, 1).beginPath()
        .arc(x, y, 56, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * Math.min(1, this.nova / 100)).strokePath();
    }
    this.novaIcon.setAlpha(full ? 1 : 0.45);
    this.novaLabel.setColor(full ? CSS.gold : CSS.muted).setText(full ? 'HAZIR' : `%${Math.floor(this.nova)}`);
    if (full && !this.novaPulse) {
      this.novaPulse = this.tweens.add({ targets: this.novaGlow, alpha: { from: 0.2, to: 0.75 }, duration: 450, yoyo: true, repeat: -1 });
    } else if (!full && this.novaPulse) { this.novaPulse.stop(); this.novaPulse = null; this.novaGlow.setAlpha(0); }
  }
  banner(title, sub, color = CSS.text) {
    const y = this.H * 0.4;
    const c = this.add.container(W / 2, y).setDepth(90);
    const g = this.add.graphics();
    g.fillStyle(COLORS.ink, 0.55).fillRect(-W / 2, -62, W, 124);
    g.lineStyle(2, Phaser.Display.Color.HexStringToColor(color).color, 0.8).lineBetween(-W / 2, -62, W / 2, -62).lineBetween(-W / 2, 62, W / 2, 62);
    const t = txt(this, 0, sub ? -16 : 0, title, 50, color, { weight: '800', spacing: 8, glow: color, glowBlur: 18 });
    c.add([g, t]);
    if (sub) c.add(txt(this, 0, 34, sub, 24, CSS.muted, { weight: '700', spacing: 4 }));
    c.setScale(1, 0).setAlpha(0);
    this.tweens.chain({ targets: c, tweens: [
      { scaleY: 1, alpha: 1, duration: 260, ease: 'Back.Out' },
      { alpha: 0, scaleY: 0.2, duration: 300, delay: 1500, onComplete: () => c.destroy() },
    ] });
  }
  floatText(x, y, s, color = CSS.text, size = 26) {
    const t = txt(this, x, y, s, size, color, { weight: '800' }).setDepth(30);
    this.tweens.add({ targets: t, y: y - 70, alpha: 0, duration: 800, ease: 'Cubic.Out', onComplete: () => t.destroy() });
  }

  // ---------------------------------------------------------------- flow
  get diff() {
    const s = this.sector, w = this.wave;
    return { hp: 1 + 0.55 * s + 0.05 * w, fire: 1 + 0.3 * s, bs: Math.min(270 + 38 * s + 6 * w, 480), n: Math.floor(s * 1.3) };
  }
  startSector() {
    const s = SECTORS[this.sector % SECTORS.length];
    this.banner(`SEKTÖR ${this.sector + 1}`, s.name, CSS.line);
    Sfx.play('wave', { volume: 0.5 });
    this.time.delayedCall(2000, () => this.startWave());
  }
  startWave() {
    if (!this.alive) return;
    this.waveActive = true;
    this.refreshWaveText();
    if (this.wave > 0) this.floatText(W / 2, this.H * 0.3, `DALGA ${this.wave + 1}`, CSS.line, 34);
    const d = this.diff, n = d.n, shoot = this.sector > 0;
    const plan = [
      [[0, () => this.formLine(5 + n, 'drone', shoot)], [2600, () => this.formVee(5 + n, shoot)]],
      [[0, () => this.stream(6 + n, 'weaver', 0.28)], [1900, () => this.stream(6 + n, 'weaver', 0.72)], [3400, () => this.meteors(3 + n)]],
      [[0, () => this.gunners(2 + (n > 1 ? 1 : 0))], [1600, () => this.formLine(6 + n, 'drone', true)], [4200, () => this.divers(3 + n)]],
      [[0, () => this.divers(4 + n)], [1600, () => this.meteors(5 + n)], [3600, () => this.stream(7 + n, 'weaver', 0.3)]],
      [[0, () => this.tanks(1 + (n > 1 ? 1 : 0))], [900, () => this.formVee(7 + n, true)], [4200, () => this.gunners(2 + (n > 0 ? 1 : 0))]],
      [[0, () => this.formLine(6 + n, 'drone', true)], [1500, () => this.divers(4 + n)], [2300, () => this.ufo()],
        [3200, () => this.tanks(1 + (n > 0 ? 1 : 0))], [5200, () => this.stream(6 + n, 'weaver', 0.7)]],
    ][this.wave];
    plan.forEach(([t, fn]) => this.schedule(t, fn));
  }
  refreshWaveText() {
    this.waveText.setText(`SEKTÖR ${this.sector + 1}`);
    this.waveText2.setText(this.boss ? 'AMİRAL' : `DALGA ${Math.min(this.wave + 1, WAVES_PER_SECTOR)}/${WAVES_PER_SECTOR}`);
  }
  schedule(ms, fn) {
    this.pending++;
    this.time.delayedCall(ms, () => { this.pending--; if (this.alive) fn(); });
  }
  waveCleared() {
    this.waveActive = false;
    this.wave++;
    if (this.weapon < 3 && Math.random() < 0.7) this.spawnPickup('bolt', Phaser.Math.Between(150, W - 150), -30);
    if (this.wave >= WAVES_PER_SECTOR) this.time.delayedCall(1200, () => this.bossWarning());
    else this.time.delayedCall(1300, () => this.startWave());
  }

  // ---------------------------------------------------------------- spawning
  spawn(kind, x, y, props = {}) {
    const def = ENEMY[kind];
    const livery = SECTORS[this.sector % SECTORS.length].enemy;
    let frame = def.frame || `enemy${livery}${def.n}`;
    if (kind.startsWith('meteor')) {
      const tone = Math.random() < 0.5 ? 'Brown' : 'Grey';
      frame = kind === 'meteorL' ? `meteor${tone}_big${Phaser.Math.Between(1, 4)}`
        : kind === 'meteorM' ? (tone === 'Brown' ? `meteorBrown_med${Phaser.Math.RND.pick([1, 3])}` : `meteorGrey_med${Phaser.Math.Between(1, 2)}`)
          : `meteor${tone}_small${Phaser.Math.Between(1, 2)}`;
    }
    const e = this.add.image(x, y, 'game', frame).setScale(def.scale).setDepth(kind === 'missile' ? 11 : 6);
    const hp = Math.ceil(def.hp * (kind === 'missile' ? 1 : this.diff.hp));
    Object.assign(e, { kind, def, hp, maxHp: hp, t: 0, ax: x, ay: y, phase: Math.random() * 6.28, amp: 0, vx: 0, vy: 160,
      fireAt: Phaser.Math.FloatBetween(0.8, 2.0), flash: 0, r: Math.min(e.displayWidth, e.displayHeight) * 0.42, entered: false }, props);
    this.enemies.push(e);
    return e;
  }
  formLine(n, kind, shoots) {
    n = Math.min(n, 8);
    for (let i = 0; i < n; i++) {
      const x = W * 0.12 + (W * 0.76) * (n === 1 ? 0.5 : i / (n - 1));
      this.schedule(i * 70, () => this.spawn(kind, x, -60, { vy: 170, shoots, amp: 18 }));
    }
  }
  formVee(n, shoots) {
    n = Math.min(n, 9);
    const cx = Phaser.Math.Between(W * 0.35, W * 0.65);
    for (let i = 0; i < n; i++) {
      const k = Math.ceil(i / 2) * (i % 2 ? -1 : 1);
      this.spawn('drone', Phaser.Math.Clamp(cx + k * 68, 40, W - 40), -60 - Math.abs(k) * 55, { vy: 200, shoots, amp: 0 });
    }
  }
  stream(n, kind, side) {
    for (let i = 0; i < n; i++) this.schedule(i * 330, () => this.spawn(kind, W * side, -60, { vy: 165, amp: 150, phase: 0 }));
  }
  gunners(n) {
    for (let i = 0; i < n; i++) {
      const x = W * (n === 1 ? 0.5 : 0.2 + 0.6 * i / (n - 1));
      this.schedule(i * 250, () => this.spawn('gunner', x, -70, { targetY: this.H * Phaser.Math.FloatBetween(0.14, 0.26) + this.safe.top }));
    }
  }
  divers(n) {
    for (let i = 0; i < n; i++) {
      this.schedule(i * 480, () => this.spawn('diver', Phaser.Math.Between(70, W - 70), -60, { targetY: this.H * Phaser.Math.FloatBetween(0.16, 0.34) }));
    }
  }
  tanks(n) {
    for (let i = 0; i < n; i++) {
      this.schedule(i * 1400, () => this.spawn('tank', n === 1 ? W / 2 : W * (0.3 + 0.4 * i), -90, { targetY: this.H * 0.2 + this.safe.top + i * 40 }));
    }
  }
  meteors(n) {
    for (let i = 0; i < n; i++) {
      this.schedule(i * 520, () => this.spawn(Math.random() < 0.6 ? 'meteorL' : 'meteorM', Phaser.Math.Between(60, W - 60), -80,
        { vx: Phaser.Math.Between(-60, 60), vy: Phaser.Math.Between(150, 240), spin: Phaser.Math.FloatBetween(-2, 2) }));
    }
  }
  ufo() {
    const left = Math.random() < 0.5;
    this.spawn('ufo', left ? -70 : W + 70, this.H * 0.18, { vx: left ? 170 : -170, ay: this.H * 0.18 + this.safe.top, bonus: true });
    Sfx.play('select', { volume: 0.6 });
  }

  // ---------------------------------------------------------------- enemy brains
  updateEnemy(e, dt) {
    e.t += dt;
    const p = this.player, d = this.diff;
    switch (e.kind) {
      case 'drone':
        e.y += e.vy * dt;
        e.x = e.ax + Math.sin(e.t * 2.2 + e.phase) * e.amp;
        if (e.shoots && e.t > e.fireAt && e.y > 40 && e.y < this.H * 0.6) {
          e.fireAt = e.t + Phaser.Math.FloatBetween(1.8, 3.0) / d.fire;
          this.aimShot(e, d.bs, 'orb_red');
        }
        break;
      case 'weaver':
        e.y += e.vy * dt;
        e.x = Phaser.Math.Clamp(e.ax + Math.sin(e.t * 2.4 + e.phase) * e.amp, 30, W - 30);
        e.rotation = Math.cos(e.t * 2.4 + e.phase) * 0.35;
        if (this.sector > 0 && e.t > e.fireAt + 1 && e.y > 40) { e.fireAt = e.t + 2.6 / d.fire; this.aimShot(e, d.bs * 0.9, 'orb_pink'); }
        break;
      case 'gunner':
        if (e.t < 1.2) e.y = Phaser.Math.Linear(e.ay, e.targetY, Phaser.Math.Easing.Cubic.Out(e.t / 1.2));
        else if (e.t < 9) {
          e.x = Phaser.Math.Clamp(e.ax + Math.sin((e.t - 1.2) * 1.1) * 130, 50, W - 50);
          if (e.t > e.fireAt + 1.2) {
            e.fireAt = e.t + 2.0 / d.fire;
            for (let i = 0; i < 3; i++) this.time.delayedCall(i * 140, () => { if (e.active && this.enemies.includes(e)) this.aimShot(e, d.bs * 1.1, 'orb_red'); });
            Sfx.play('eshoot', { volume: 0.3 });
          }
        } else e.y += 260 * dt;
        break;
      case 'diver':
        if (e.t < 0.9) e.y = Phaser.Math.Linear(-60, e.targetY, Phaser.Math.Easing.Cubic.Out(e.t / 0.9));
        else if (e.t < 1.5) {
          e.x += Math.sin(e.t * 60) * 1.5;
          if (!e.locked) { e.locked = true; e.setTint(0xff9a9a); }
        } else {
          if (!e.dashing) {
            e.dashing = true; e.clearTint();
            const a = Phaser.Math.Angle.Between(e.x, e.y, p.x, p.y);
            e.vx = Math.cos(a) * 720; e.vy = Math.sin(a) * 720;
            e.rotation = a - Math.PI / 2;
          }
          e.x += e.vx * dt; e.y += e.vy * dt;
        }
        break;
      case 'tank':
        if (e.y < e.targetY) e.y += 75 * dt;
        e.x = e.ax + Math.sin(e.t * 0.6) * 80;
        if (e.t > e.fireAt + 1.5 && e.y > 40) {
          e.fireAt = e.t + 2.5 / d.fire;
          const a = Phaser.Math.Angle.Between(e.x, e.y, p.x, p.y);
          const n = 5 + Math.min(4, this.sector);
          for (let i = 0; i < n; i++) this.shot(e.x, e.y + 30, a + (i - (n - 1) / 2) * 0.17, d.bs * 0.85, 'orb_gold');
          Sfx.play('eshoot', { volume: 0.35 });
        }
        if (e.t > 13) e.y += 140 * dt;
        break;
      case 'ufo':
        e.x += e.vx * dt;
        e.y = e.ay + Math.sin(e.t * 2) * 30;
        e.rotation += 2.5 * dt;
        if (this.sector > 0 && e.t > e.fireAt + 1) {
          e.fireAt = e.t + 2.2;
          for (let i = 0; i < 10; i++) this.shot(e.x, e.y, i * Math.PI / 5 + e.t, d.bs * 0.7, 'orb_pink');
        }
        break;
      case 'missile': {
        if (e.t < 2.6) {
          const a = Phaser.Math.Angle.Between(e.x, e.y, p.x, p.y);
          const cur = Math.atan2(e.vy, e.vx);
          const na = Phaser.Math.Angle.RotateTo(cur, a, 2.4 * dt);
          const sp = 330;
          e.vx = Math.cos(na) * sp; e.vy = Math.sin(na) * sp;
        }
        e.x += e.vx * dt; e.y += e.vy * dt;
        e.rotation = Math.atan2(e.vy, e.vx) + Math.PI / 2;
        if (Math.random() < 0.5) this.embers.emitParticleAt(e.x - e.vx * 0.06, e.y - e.vy * 0.06, 1);
        break;
      }
      default: // meteors
        e.x += e.vx * dt; e.y += e.vy * dt; e.rotation += (e.spin || 0) * dt;
    }
    if (!e.entered && e.y > 0 && e.x > 0 && e.x < W) e.entered = true;
    if (e.flash > 0) { e.flash -= dt; if (e.flash <= 0) { if (e.locked && !e.dashing) e.setTint(0xff9a9a); else e.clearTint(); } }
    const H = this.H;
    if (e.y > H + 160 || e.y < -500 || (e.entered && (e.x < -220 || e.x > W + 220)) || (!e.entered && e.t > 12)) this.removeEnemy(e);
  }
  removeEnemy(e) {
    const i = this.enemies.indexOf(e);
    if (i >= 0) this.enemies.splice(i, 1);
    e.destroy();
  }
  shot(x, y, a, speed, tex = 'orb_red') {
    const b = this.eBullets.get();
    b.setTexture(tex).setPosition(x, y).setScale(tex === 'orb_gold' ? 1.0 : 0.9);
    b.vx = Math.cos(a) * speed; b.vy = Math.sin(a) * speed; b.r = 9;
    return b;
  }
  aimShot(e, speed, tex) {
    const p = this.player;
    this.shot(e.x, e.y + 20, Phaser.Math.Angle.Between(e.x, e.y, p.x, p.y), speed, tex);
    Sfx.play('eshoot', { volume: 0.22, gap: 90 });
  }

  // ---------------------------------------------------------------- player weapons
  firePlayer() {
    const s = this.shipDef, p = this.player;
    const pat = PATTERNS[this.weapon - 1];
    pat.forEach(([ox, deg]) => {
      const b = this.pBullets.get();
      const a = Phaser.Math.DegToRad(deg * s.spread);
      b.setTexture('game', Math.abs(deg) > 0 ? s.laser2 : s.laser).setPosition(p.x + ox, p.y - 40).setScale(1).setRotation(a).setBlendMode('NORMAL');
      b.vx = Math.sin(a) * 1250; b.vy = -Math.cos(a) * 1250; b.dmg = this.dmg; b.homing = false;
    });
    Sfx.play('shoot', { volume: 0.16, gap: 110, detune: Phaser.Math.Between(-80, 80) });
    if (this.weapon >= 5 && this.missileCd <= 0) {
      this.missileCd = 0.75;
      [-1, 1].forEach(side => {
        const b = this.pBullets.get();
        b.setTexture('game', 'spaceMissiles_001').setPosition(p.x + side * 30, p.y).setScale(0.9).setRotation(0);
        b.vx = side * 260; b.vy = -380; b.dmg = this.dmg * 2.5; b.homing = true;
      });
    }
  }
  nearestTarget(x, y) {
    let best = null, bd = 1e12;
    if (this.boss && !this.boss.entering) { best = this.boss; bd = Phaser.Math.Distance.Squared(x, y, best.x, best.y); }
    for (const e of this.enemies) {
      if (!e.entered) continue;
      const d = Phaser.Math.Distance.Squared(x, y, e.x, e.y);
      if (d < bd) { bd = d; best = e; }
    }
    return best;
  }
  fireNova() {
    if (!this.alive || this.nova < 100 || !this.controls) return;
    this.nova = 0;
    this.invuln = Math.max(this.invuln, 1.0);
    Sfx.play('nova', { volume: 0.9 }); Sfx.play('explode_big', { volume: 0.6 });
    vibrate(80);
    this.cameras.main.flash(250, 140, 230, 255);
    this.cameras.main.shake(400, 0.012);
    const p = this.player;
    [0, 120].forEach((delay, i) => {
      const ring = this.add.image(p.x, p.y, 'ring').setTint(i ? COLORS.gold : COLORS.line).setBlendMode('ADD').setScale(0.2).setDepth(20);
      this.tweens.add({ targets: ring, scale: 9, alpha: 0, delay, duration: 750, ease: 'Cubic.Out', onComplete: () => ring.destroy() });
    });
    this.eBullets.items.forEach(b => { if (b.active) { this.sparks.emitParticleAt(b.x, b.y, 2); this.eBullets.kill(b); } });
    [...this.enemies].forEach(e => { if (e.y > -20) this.hitEnemy(e, 30 * this.dmg + 10); });
    if (this.boss && !this.boss.entering) this.hitBoss(this.boss.maxHp * 0.07);
    this.refreshHUD();
  }

  // ---------------------------------------------------------------- damage
  hitEnemy(e, dmg) {
    if (!this.enemies.includes(e)) return;
    e.hp -= dmg;
    if (e.hp <= 0) return this.killEnemy(e);
    e.setTintFill(0xffffff); e.flash = 0.05;
    Sfx.play('hit', { volume: 0.2, gap: 70 });
  }
  killEnemy(e) {
    this.removeEnemy(e);
    const big = e.kind === 'tank' || e.kind === 'ufo' || e.kind === 'meteorL';
    this.explode(e.x, e.y, big ? 1.5 : e.kind === 'missile' ? 0.6 : 1, e.kind.startsWith('meteor'));
    this.combo++; this.comboT = 2.4;
    this.mult = Math.min(8, 1 + Math.floor(this.combo / 6));
    this.maxCombo = Math.max(this.maxCombo, this.mult);
    const pts = e.def.score * this.mult;
    this.score += pts;
    this.kills++;
    this.nova = Math.min(100, this.nova + e.def.nova * this.novaRate);
    if (pts >= 300) this.floatText(e.x, e.y - 20, '+' + pts, this.mult > 1 ? CSS.gold : CSS.text, big ? 30 : 24);
    let cr = e.def.cr;
    if (e.kind === 'drone' || e.kind === 'weaver' || e.kind === 'diver') cr = Math.random() < 0.6 ? 1 : 0;
    for (let i = 0; i < cr; i++) this.spawnPickup('credit', e.x, e.y, true);
    const roll = Math.random();
    const chance = e.kind === 'ufo' ? 1 : e.kind === 'tank' ? 0.5 : e.kind === 'gunner' ? 0.18 : 0.06;
    if (roll < chance) {
      const kinds = this.weapon < 5 ? ['bolt', 'bolt', 'shield', 'heal', 'nova'] : ['shield', 'heal', 'nova'];
      this.spawnPickup(Phaser.Math.RND.pick(kinds), e.x, e.y);
    }
    if (e.kind === 'meteorL' || e.kind === 'meteorM') {
      const next = e.kind === 'meteorL' ? 'meteorM' : 'meteorS';
      for (let i = 0; i < 2; i++) {
        this.spawn(next, e.x, e.y, { vx: (i ? 1 : -1) * Phaser.Math.Between(60, 140), vy: Phaser.Math.Between(140, 220),
          spin: Phaser.Math.FloatBetween(-3, 3), entered: true });
      }
    }
    this.drawNova();
  }
  explode(x, y, size = 1, rock = false) {
    Sfx.play(size > 1.3 ? 'explode_big' : 'explode', { volume: size > 1.3 ? 0.65 : 0.4, gap: 45, detune: Phaser.Math.Between(-200, 200) });
    const flash = this.add.image(x, y, 'game', 'fx_light_01').setBlendMode('ADD').setTint(rock ? 0xffe2b0 : 0xffb04a).setScale(0.6 * size).setDepth(15);
    this.tweens.add({ targets: flash, scale: 1.8 * size, alpha: 0, duration: 260, onComplete: () => flash.destroy() });
    const puffs = Math.round(4 * size);
    for (let i = 0; i < puffs; i++) {
      const a = Math.random() * Math.PI * 2, d = Phaser.Math.Between(20, 55) * size;
      const pf = this.add.image(x, y, 'game', `spaceEffects_0${Phaser.Math.Between(11, 17)}`).setDepth(13)
        .setScale(0.35 * size).setRotation(a).setTint(rock ? 0xc9b9a6 : Phaser.Math.RND.pick([0xffd38a, 0xff9e5a, 0xd8d8e8]));
      this.tweens.add({ targets: pf, x: x + Math.cos(a) * d, y: y + Math.sin(a) * d, scale: (0.8 + Math.random() * 0.5) * size,
        alpha: 0, rotation: a + 1, duration: Phaser.Math.Between(450, 750), ease: 'Cubic.Out', onComplete: () => pf.destroy() });
    }
    this.embers.explode(Math.round(10 * size), x, y);
    if (size >= 1.4) {
      const ring = this.add.image(x, y, 'ring').setBlendMode('ADD').setTint(0xffc27a).setScale(0.1).setDepth(15);
      this.tweens.add({ targets: ring, scale: 0.9 * size, alpha: 0, duration: 420, ease: 'Cubic.Out', onComplete: () => ring.destroy() });
      this.cameras.main.shake(180, 0.006 * size);
    }
  }
  hurt() {
    if (this.invuln > 0 || !this.alive) return;
    if (this.shield > 0) {
      this.shield--; this.invuln = 0.6;
      Sfx.play('shield_down', { volume: 0.7 });
      this.tweens.add({ targets: this.pShield, scale: { from: 1.3, to: 1 }, duration: 200 });
      this.refreshHUD();
      return;
    }
    this.hp--;
    this.weapon = Math.max(1, this.weapon - 1);
    this.invuln = 1.7;
    this.combo = 0; this.mult = 1; this.comboT = 0;
    Sfx.play('hurt', { volume: 0.8 });
    vibrate(150);
    this.cameras.main.shake(260, 0.014);
    this.cameras.main.flash(160, 255, 60, 90);
    this.sparks.explode(18, this.player.x, this.player.y);
    this.refreshHUD();
    if (this.hp <= 0) this.die();
  }
  die() {
    this.alive = false; this.controls = false; this.drag = null;
    this.trail.stop();
    this.explode(this.player.x, this.player.y, 2.2);
    this.time.delayedCall(250, () => this.explode(this.player.x + 30, this.player.y - 20, 1.4));
    this.player.setVisible(false);
    Sfx.play('lose', { volume: 0.8 });
    Sfx.playMusic(null);
    vibrate([100, 60, 200]);
    this.time.delayedCall(1700, () => {
      const r = this.endRun(false);
      Sfx.play('gameover', { volume: 0.7 });
      this.scene.launch('GameOver', r);
      this.scene.pause();
    });
  }
  endRun(quit) {
    if (this.ended) return this.result;
    this.ended = true;
    const record = this.score > Save.d.best;
    Save.d.credits += this.creditsRun;
    Save.d.best = Math.max(Save.d.best, this.score);
    Save.d.bestSector = Math.max(Save.d.bestSector, this.sector + 1);
    Save.d.runs++;
    Save.write();
    this.result = { score: this.score, record: record && !quit, sector: this.sector + 1, kills: this.kills, maxCombo: this.maxCombo, credits: this.creditsRun };
    return this.result;
  }

  // ---------------------------------------------------------------- pickups
  spawnPickup(kind, x, y, burst) {
    const def = PICKUP[kind];
    const p = this.add.image(x, y, 'game', def.frame).setScale(def.scale).setDepth(7);
    const a = Math.random() * Math.PI * 2;
    Object.assign(p, { kind, life: 11, vx: burst ? Math.cos(a) * Phaser.Math.Between(80, 220) : 0, vy: burst ? Math.sin(a) * 200 - 60 : 90, pulled: false });
    if (kind !== 'credit') {
      const glow = this.add.image(x, y, 'game', 'fx_light_01').setBlendMode('ADD').setScale(0.7).setAlpha(0.5).setDepth(6)
        .setTint({ bolt: COLORS.line, shield: COLORS.good, heal: COLORS.danger, nova: COLORS.gold }[kind]);
      p.glow = glow;
      this.tweens.add({ targets: p, scale: def.scale * 1.12, duration: 400, yoyo: true, repeat: -1 });
    }
    this.pickups.push(p);
  }
  collect(p) {
    switch (p.kind) {
      case 'credit':
        this.creditsRun += 1 + this.sector; this.score += 10;
        Sfx.play('coin', { volume: 0.32, gap: 35, rate: 1 + Math.min(0.5, (this.coinChain = (this.coinChain || 0) + 0.03)) });
        break;
      case 'bolt':
        if (this.weapon < 5) { this.weapon++; this.floatText(p.x, p.y, this.weapon === 5 ? 'SİLAH MAKS!' : 'SİLAH +1', CSS.line, 28); }
        else { this.score += 500; this.floatText(p.x, p.y, '+500', CSS.line); }
        Sfx.play('powerup', { volume: 0.7 });
        break;
      case 'shield':
        this.shield = 3; Sfx.play('shield_up', { volume: 0.7 }); this.floatText(p.x, p.y, 'KALKAN', CSS.good, 28);
        break;
      case 'heal':
        if (this.hp < this.maxHp) { this.hp++; this.floatText(p.x, p.y, 'ONARIM', CSS.danger, 28); }
        else { this.score += 500; this.floatText(p.x, p.y, '+500', CSS.text); }
        Sfx.play('powerup', { volume: 0.6, rate: 0.8 });
        break;
      case 'nova':
        this.nova = Math.min(100, this.nova + 50); Sfx.play('powerup', { volume: 0.6, rate: 1.2 }); this.floatText(p.x, p.y, 'NOVA +50', CSS.gold, 28);
        break;
    }
    if (p.kind !== 'credit') vibrate(25);
    this.removePickup(p);
    this.refreshHUD();
  }
  removePickup(p) {
    const i = this.pickups.indexOf(p);
    if (i >= 0) this.pickups.splice(i, 1);
    if (p.glow) p.glow.destroy();
    this.tweens.killTweensOf(p);
    p.destroy();
  }

  // ---------------------------------------------------------------- boss
  bossWarning() {
    if (!this.alive) return;
    Sfx.playMusic(null);
    const H = this.H;
    const c = this.add.container(0, 0).setDepth(95);
    const tint = this.add.rectangle(W / 2, H / 2, W, H, COLORS.danger, 0.12);
    const bars = [H * 0.33, H * 0.47].map(y => this.add.rectangle(W / 2, y, W, 40, COLORS.danger, 0.85));
    const t = txt(this, W / 2, H * 0.4, 'UYARI', 72, CSS.text, { weight: '800', spacing: 18, glow: CSS.danger, glowBlur: 24 });
    const sub = txt(this, W / 2, H * 0.47 + 62, 'AMİRAL GEMİSİ YAKLAŞIYOR', 26, CSS.danger, { weight: '800', spacing: 5 });
    const stripes = bars.map(b => txt(this, W / 2, b.y, '▲ TEHLİKE ▲ TEHLİKE ▲ TEHLİKE ▲ TEHLİKE ▲ TEHLİKE ▲', 22, CSS.ink, { weight: '800', spacing: 4 }));
    c.add([tint, ...bars, ...stripes, t, sub]);
    this.tweens.add({ targets: stripes, x: '-=120', duration: 2800 });
    this.tweens.add({ targets: [t, tint], alpha: 0.35, duration: 280, yoyo: true, repeat: 4 });
    for (let i = 0; i < 3; i++) this.time.delayedCall(i * 800, () => Sfx.play('warning', { volume: 0.8 }));
    vibrate([80, 120, 80, 120, 80]);
    this.time.delayedCall(2900, () => {
      this.tweens.add({ targets: c, alpha: 0, duration: 300, onComplete: () => c.destroy() });
      this.spawnBoss();
    });
  }
  spawnBoss() {
    const def = BOSSES[this.sector % BOSSES.length];
    Sfx.playMusic('music_boss', 0.45);
    const b = this.add.image(W / 2, -260, 'game', def.frame).setScale(def.scale).setDepth(5);
    const hp = Math.round(420 * (1 + 0.75 * this.sector));
    Object.assign(b, { def, hp, maxHp: hp, entering: true, t: 0, phase: 1, flash: 0, rx: b.displayWidth * 0.42, ry: b.displayHeight * 0.38 });
    this.boss = b;
    this.bossBaseY = this.H * 0.2 + this.safe.top + 40;
    this.tweens.add({ targets: b, y: this.bossBaseY, duration: 2600, ease: 'Cubic.Out', onComplete: () => {
      b.entering = false; this.bossPatternIdx = 0; this.time.delayedCall(500, () => this.nextPattern());
    } });
    this.bossName.setText(def.name);
    this.bossUI.setVisible(true).setAlpha(0);
    this.tweens.add({ targets: this.bossUI, alpha: 1, duration: 600 });
    this.drawBossBar();
    this.refreshWaveText();
  }
  drawBossBar() {
    const g = this.bossBar, w = 520, x = W / 2 - w / 2, k = Math.max(0, this.boss ? this.boss.hp / this.boss.maxHp : 0);
    g.clear();
    g.fillStyle(COLORS.ink, 0.8).fillRect(x - 4, -4, w + 8, 22);
    g.fillStyle(COLORS.danger, 1).fillRect(x, 0, w * k, 14);
    g.fillStyle(0xffffff, 0.25).fillRect(x, 0, w * k, 4);
    g.lineStyle(2, COLORS.danger, 0.6).strokeRect(x - 4, -4, w + 8, 22);
    [1 / 3, 2 / 3].forEach(m => g.fillStyle(COLORS.ink, 1).fillRect(x + w * m - 1, -4, 3, 22));
  }
  bossEvent(cfg) { const ev = this.time.addEvent(cfg); this.bossEvents.push(ev); return ev; }
  nextPattern() {
    const b = this.boss;
    if (!b || !this.alive || b.dead) return;
    const pool = ['radial', 'aimed', 'spiral'];
    if (b.phase >= 2) pool.push('missiles', 'summon');
    if (b.phase >= 3) pool.push('beam', 'radial');
    const name = pool[this.bossPatternIdx++ % pool.length];
    const dur = this['pat_' + name](b);
    this.bossEvent({ delay: dur + (b.phase >= 3 ? 450 : 750), callback: () => this.nextPattern() });
  }
  pat_radial(b) {
    const n = 16 + b.phase * 4, bs = this.diff.bs * 0.8;
    this.bossEvent({ delay: 520, repeat: 2, callback: () => {
      const off = Math.random() * Math.PI;
      for (let i = 0; i < n; i++) this.shot(b.x, b.y + 40, off + i * Math.PI * 2 / n, bs, 'orb_pink');
      Sfx.play('eshoot', { volume: 0.4 });
      this.sparks.explode(6, b.x, b.y + 50);
    } });
    return 1600;
  }
  pat_aimed(b) {
    const bs = this.diff.bs * 1.1;
    this.bossEvent({ delay: 340, repeat: 4, callback: () => {
      const a = Phaser.Math.Angle.Between(b.x, b.y, this.player.x, this.player.y);
      [-1, 1].forEach(s => {
        for (let i = -2; i <= 2; i++) this.shot(b.x + s * b.rx * 0.6, b.y + 30, a + i * 0.13, bs, 'orb_red');
      });
      Sfx.play('eshoot', { volume: 0.4 });
    } });
    return 1800;
  }
  pat_spiral(b) {
    let ang = 0;
    const bs = this.diff.bs * 0.75;
    this.bossEvent({ delay: 80, repeat: 30 + b.phase * 4, callback: () => {
      ang += 0.31;
      const arms = b.phase >= 3 ? 3 : 2;
      for (let k = 0; k < arms; k++) this.shot(b.x, b.y + 30, ang + k * Math.PI * 2 / arms, bs, 'orb_gold');
      Sfx.play('eshoot', { volume: 0.2, gap: 160 });
    } });
    return 2900;
  }
  pat_missiles(b) {
    const n = 2 + b.phase;
    let k = 0;
    this.bossEvent({ delay: 300, repeat: n - 1, callback: () => {
      const side = k++ % 2 ? -1 : 1;
      this.spawn('missile', b.x + side * b.rx * 0.8, b.y + 20, { vx: side * 200, vy: 120, entered: true });
      Sfx.play('missile', { volume: 0.5 });
    } });
    return 300 * n + 1400;
  }
  pat_summon(b) {
    for (let i = 0; i < 4; i++) {
      this.spawn('drone', b.x + (i - 1.5) * 70, b.y + 40, { vy: 230, shoots: true, amp: 30, entered: true });
    }
    Sfx.play('select', { volume: 0.5 });
    return 1400;
  }
  pat_beam(b) {
    const H = this.H;
    const xs = [this.player.x, Phaser.Math.Clamp(this.player.x + Phaser.Math.RND.pick([-180, 180]), 60, W - 60)];
    xs.forEach((x, i) => {
      const warn = this.add.rectangle(x, H / 2, 6, H, COLORS.danger, 0.7).setDepth(4);
      this.tweens.add({ targets: warn, alpha: 0.15, duration: 120, yoyo: true, repeat: 3 });
      Sfx.play('warning', { volume: 0.5 });
      this.bossEvent({ delay: 950, callback: () => {
        warn.destroy();
        const beam = this.add.image(x, b.y + 60, 'game', 'spaceEffects_010').setOrigin(0.5, 0).setBlendMode('ADD').setTint(0xff6a8a)
          .setDisplaySize(84, H).setDepth(4);
        const core = this.add.image(x, b.y + 60, 'game', 'spaceEffects_007').setOrigin(0.5, 0).setBlendMode('ADD').setDisplaySize(26, H).setDepth(4);
        beam.hx = 36; beam.x0 = x;
        this.beams.push(beam);
        this.cameras.main.shake(800, 0.004);
        Sfx.play('nova', { volume: 0.5, rate: 0.7 });
        this.tweens.add({ targets: [beam, core], scaleX: '*=1.15', duration: 60, yoyo: true, repeat: 6 });
        this.bossEvent({ delay: 900, callback: () => {
          this.beams.splice(this.beams.indexOf(beam), 1);
          this.tweens.add({ targets: [beam, core], alpha: 0, duration: 200, onComplete: () => { beam.destroy(); core.destroy(); } });
        } });
      } });
    });
    return 2300;
  }
  hitBoss(dmg) {
    const b = this.boss;
    if (!b || b.entering || b.dead) return;
    b.hp -= dmg;
    b.setTintFill(0xffffff); b.flash = 0.04;
    Sfx.play('hit', { volume: 0.18, gap: 80, rate: 0.7 });
    const k = b.hp / b.maxHp;
    if (b.phase === 1 && k < 0.66 || b.phase === 2 && k < 0.33) {
      b.phase++;
      this.floatText(b.x, b.y + 120, b.phase === 3 ? 'SON EVRE!' : 'ÖFKELENDİ!', CSS.danger, 34);
      this.explode(b.x + Phaser.Math.Between(-80, 80), b.y, 1.4);
      this.nova = Math.min(100, this.nova + 15);
      this.drawNova();
    }
    if (b.hp <= 0) this.killBoss();
    this.drawBossBar();
  }
  killBoss() {
    const b = this.boss;
    b.dead = true;
    this.bossEvents.forEach(ev => ev.remove(false));
    this.bossEvents = [];
    this.beams.forEach(bm => bm.setVisible(false)); this.beams = [];
    this.eBullets.items.forEach(x => { if (x.active) { this.sparks.emitParticleAt(x.x, x.y, 1); this.eBullets.kill(x); } });
    [...this.enemies].forEach(e => this.killEnemy(e));
    Sfx.playMusic(null);
    this.invuln = 4;
    for (let i = 0; i < 9; i++) {
      this.time.delayedCall(i * 160, () => {
        this.explode(b.x + Phaser.Math.Between(-b.rx, b.rx), b.y + Phaser.Math.Between(-b.ry, b.ry), Phaser.Math.FloatBetween(1, 1.6));
        vibrate(30);
      });
    }
    this.tweens.add({ targets: b, x: b.x + 8, duration: 40, yoyo: true, repeat: 18 });
    this.time.delayedCall(1550, () => {
      this.explode(b.x, b.y, 3.2);
      this.cameras.main.flash(400, 255, 240, 210);
      this.cameras.main.shake(600, 0.02);
      vibrate(300);
      const bonus = 5000 * (this.sector + 1), crBonus = 100 + 60 * this.sector;
      this.score += bonus; this.creditsRun += crBonus;
      this.refreshHUD();
      for (let i = 0; i < 36 + this.sector * 12; i++) this.spawnPickup('credit', b.x, b.y, true);
      this.spawnPickup(this.weapon < 5 ? 'bolt' : 'nova', b.x - 50, b.y);
      this.spawnPickup('heal', b.x + 50, b.y);
      b.destroy(); this.boss = null;
      this.tweens.add({ targets: this.bossUI, alpha: 0, duration: 500, onComplete: () => this.bossUI.setVisible(false) });
      Sfx.play('win', { volume: 0.8 });
      this.time.delayedCall(900, () => this.banner('SEKTÖR TEMİZLENDİ', `+${bonus.toLocaleString('tr-TR')} PUAN  ·  +${crBonus} KREDİ`, CSS.gold));
      this.time.delayedCall(3600, () => {
        if (!this.alive) return;
        this.sector++; this.wave = 0;
        this.bg.setSector(this.sector);
        this.tweens.add({ targets: this.bg, speed: 6, duration: 600, yoyo: true, hold: 900 });
        Sfx.playMusic('music_game', 0.38);
        this.refreshWaveText();
        this.time.delayedCall(1800, () => this.startSector());
      });
    });
  }

  // ---------------------------------------------------------------- main loop
  update(time, dms) {
    const dt = Math.min(dms, 50) / 1000;
    const H = this.H, p = this.player;
    this.bg.update(dt);

    if (this.alive && this.controls) {
      if (this.keys) {
        const k = this.keys, sp = 640 * this.shipDef.speed * dt;
        if (k.LEFT.isDown || k.A.isDown) this.tx -= sp;
        if (k.RIGHT.isDown || k.D.isDown) this.tx += sp;
        if (k.UP.isDown || k.W.isDown) this.ty -= sp;
        if (k.DOWN.isDown || k.S.isDown) this.ty += sp;
        this.clampTarget();
      }
      const f = Math.min(1, dt * 16);
      const dx = (this.tx - p.x) * f;
      p.x += dx; p.y += (this.ty - p.y) * f;
      this.pBody.rotation = this.pDamage.rotation = Phaser.Math.Clamp(dx * 0.02, -0.25, 0.25);

      this.fireCd -= dms; this.missileCd -= dt;
      if (this.fireCd <= 0) { this.firePlayer(); this.fireCd += this.fireInterval; if (this.fireCd < 0) this.fireCd = 0; }
    }
    if (this.invuln > 0) {
      this.invuln -= dt;
      this.pBody.setAlpha(this.invuln > 0 && this.hp > 0 && Math.floor(this.invuln * 14) % 2 ? 0.35 : 1);
    }
    if (this.comboT > 0) { this.comboT -= dt; if (this.comboT <= 0) { this.combo = 0; this.mult = 1; } }

    // Player bullets
    for (const b of this.pBullets.items) {
      if (!b.active) continue;
      if (b.homing) {
        const tgt = this.nearestTarget(b.x, b.y);
        if (tgt) {
          const a = Phaser.Math.Angle.Between(b.x, b.y, tgt.x, tgt.y);
          const na = Phaser.Math.Angle.RotateTo(Math.atan2(b.vy, b.vx), a, 6 * dt);
          const sp = Math.min(900, Math.hypot(b.vx, b.vy) + 900 * dt);
          b.vx = Math.cos(na) * sp; b.vy = Math.sin(na) * sp;
        } else b.vy -= 900 * dt;
        b.rotation = Math.atan2(b.vy, b.vx) + Math.PI / 2;
      }
      b.x += b.vx * dt; b.y += b.vy * dt;
      if (b.y < -60 || b.x < -40 || b.x > W + 40 || b.y > H + 40) { this.pBullets.kill(b); continue; }
      let hit = false;
      for (const e of this.enemies) {
        const rr = e.r + 8;
        if (Math.abs(e.x - b.x) < rr && Math.abs(e.y - b.y) < rr && (e.x - b.x) ** 2 + (e.y - b.y) ** 2 < rr * rr) {
          this.hitEnemy(e, b.dmg); hit = true; break;
        }
      }
      const bo = this.boss;
      if (!hit && bo && !bo.entering && !bo.dead) {
        const nx = (b.x - bo.x) / bo.rx, ny = (b.y - bo.y) / bo.ry;
        if (nx * nx + ny * ny < 1) { this.hitBoss(b.dmg); hit = true; }
      }
      if (hit) { this.sparks.emitParticleAt(b.x, b.y - 10, 3); this.pBullets.kill(b); }
    }

    // Enemies
    for (let i = this.enemies.length - 1; i >= 0; i--) {
      const e = this.enemies[i];
      if (!e) continue;
      this.updateEnemy(e, dt);
      if (this.alive && this.enemies.includes(e)) {
        const rr = e.r * 0.75 + 20;
        if ((e.x - p.x) ** 2 + (e.y - p.y) ** 2 < rr * rr && this.invuln <= 0) {
          this.hurt();
          if (e.kind.startsWith('meteor') || e.kind === 'tank') this.hitEnemy(e, 6); else this.killEnemy(e);
        }
      }
    }

    // Boss
    const bo = this.boss;
    if (bo && !bo.dead) {
      bo.t += dt;
      if (!bo.entering) {
        bo.x = W / 2 + Math.sin(bo.t * 0.55) * (W * 0.26);
        bo.y = this.bossBaseY + Math.sin(bo.t * 1.3) * 18;
        const nx = (p.x - bo.x) / (bo.rx * 0.8), ny = (p.y - bo.y) / (bo.ry * 0.8);
        if (this.alive && nx * nx + ny * ny < 1) this.hurt();
      }
      if (bo.flash > 0) { bo.flash -= dt; if (bo.flash <= 0) bo.clearTint(); }
      if (Math.random() < 0.05 * bo.phase) this.embers.emitParticleAt(bo.x + Phaser.Math.Between(-bo.rx, bo.rx) * 0.6, bo.y - bo.ry * 0.5, 1);
    }
    for (const bm of this.beams) {
      if (this.alive && Math.abs(p.x - bm.x0) < bm.hx + 14 && p.y > bm.y) this.hurt();
    }

    // Enemy bullets
    for (const b of this.eBullets.items) {
      if (!b.active) continue;
      b.x += b.vx * dt; b.y += b.vy * dt;
      if (b.y > H + 30 || b.y < -40 || b.x < -30 || b.x > W + 30) { this.eBullets.kill(b); continue; }
      if (this.alive && (b.x - p.x) ** 2 + (b.y - p.y) ** 2 < (b.r + 13) ** 2) {
        this.eBullets.kill(b);
        this.hurt();
      }
    }

    // Pickups
    for (let i = this.pickups.length - 1; i >= 0; i--) {
      const q = this.pickups[i];
      q.life -= dt;
      const dx = p.x - q.x, dy = p.y - q.y, d2 = dx * dx + dy * dy;
      if (this.alive && (q.pulled || d2 < this.magnet * this.magnet)) {
        q.pulled = true;
        const d = Math.sqrt(d2) || 1, sp = 950;
        q.vx = Phaser.Math.Linear(q.vx, dx / d * sp, Math.min(1, dt * 8));
        q.vy = Phaser.Math.Linear(q.vy, dy / d * sp, Math.min(1, dt * 8));
      } else {
        q.vx *= Math.pow(0.1, dt);
        q.vy = Phaser.Math.Linear(q.vy, 120, Math.min(1, dt * 2));
      }
      q.x += q.vx * dt; q.y += q.vy * dt;
      if (q.kind === 'credit') q.scaleX = 0.62 * Math.cos(q.life * 6);
      if (q.glow) q.glow.setPosition(q.x, q.y);
      if (q.life < 2) q.setAlpha(Math.floor(q.life * 8) % 2 ? 0.3 : 1);
      if (this.alive && d2 < 52 * 52) this.collect(q);
      else if (q.life <= 0 || q.y > H + 40) this.removePickup(q);
    }
    if (this.coinChain) this.coinChain = Math.max(0, this.coinChain - dt * 0.4);

    // Wave completion
    if (this.waveActive && this.pending === 0 && this.enemies.length === 0) this.waveCleared();

    // HUD
    if (this.shownScore !== this.score) {
      this.shownScore += Math.ceil((this.score - this.shownScore) * Math.min(1, dt * 12));
      if (Math.abs(this.score - this.shownScore) < 3) this.shownScore = this.score;
      this.scoreText.setText(this.shownScore.toLocaleString('tr-TR'));
    }
    this.comboBar.clear();
    if (this.mult > 1) {
      this.comboText.setText(`x${this.mult} KOMBO`);
      this.comboBar.fillStyle(COLORS.gold, 0.9).fillRect(28, this.comboText.y + 18, 120 * Math.max(0, this.comboT / 2.4), 4);
    } else this.comboText.setText('');
    if (this.creditsShown !== this.creditsRun) { this.creditsShown = this.creditsRun; this.creditChip.setValue(this.creditsRun.toLocaleString('tr-TR')); }
  }
}

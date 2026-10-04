// Procedural textures, UI widgets and the parallax space background shared by every scene.

function hex(c, a = 1) {
  return `rgba(${(c >> 16) & 255},${(c >> 8) & 255},${c & 255},${a})`;
}

function canvasTex(scene, key, w, h, draw) {
  if (scene.textures.exists(key)) return key;
  const t = scene.textures.createCanvas(key, w, h);
  draw(t.getContext(), w, h);
  t.refresh();
  return key;
}

function notchPath(ctx, x, y, w, h, c) {
  ctx.beginPath();
  ctx.moveTo(x + c, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + h - c);
  ctx.lineTo(x + w - c, y + h); ctx.lineTo(x, y + h); ctx.lineTo(x, y + c); ctx.closePath();
}

// Generates all runtime textures once (called from Boot).
function makeTextures(scene) {
  const H = scene.scale.height;
  const orb = (key, core, mid) => canvasTex(scene, key, 40, 40, (ctx) => {
    const g = ctx.createRadialGradient(20, 20, 0, 20, 20, 20);
    g.addColorStop(0, '#ffffff'); g.addColorStop(0.28, core); g.addColorStop(0.55, mid); g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, 40, 40);
  });
  orb('orb_red', '#ff8a8a', 'rgba(255,40,80,0.55)');
  orb('orb_pink', '#ff9cf0', 'rgba(220,60,255,0.55)');
  orb('orb_gold', '#ffe28a', 'rgba(255,150,30,0.55)');
  orb('orb_cyan', '#a8f4ff', 'rgba(40,190,255,0.55)');

  canvasTex(scene, 'dot', 8, 8, (ctx) => { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(4, 4, 4, 0, Math.PI * 2); ctx.fill(); });

  const stars = (key, n, big) => canvasTex(scene, key, 512, 512, (ctx) => {
    for (let i = 0; i < n; i++) {
      const x = Math.random() * 512, y = Math.random() * 512, r = big ? 1 + Math.random() * 1.6 : 0.4 + Math.random() * 0.9;
      ctx.fillStyle = `rgba(${200 + Math.random() * 55 | 0},${215 + Math.random() * 40 | 0},255,${0.35 + Math.random() * 0.6})`;
      ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
      if (big && Math.random() < 0.25) {
        ctx.strokeStyle = 'rgba(200,235,255,0.5)'; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(x - 6, y); ctx.lineTo(x + 6, y); ctx.moveTo(x, y - 6); ctx.lineTo(x, y + 6); ctx.stroke();
      }
    }
  });
  stars('stars_far', 260, false);
  stars('stars_near', 40, true);

  canvasTex(scene, 'vignette', W, H, (ctx, w, h) => {
    const g = ctx.createRadialGradient(w / 2, h * 0.45, w * 0.35, w / 2, h * 0.5, h * 0.75);
    g.addColorStop(0, 'rgba(3,5,15,0)'); g.addColorStop(1, 'rgba(3,5,15,0.82)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
    const top = ctx.createLinearGradient(0, 0, 0, 220);
    top.addColorStop(0, 'rgba(4,6,18,0.85)'); top.addColorStop(1, 'rgba(4,6,18,0)');
    ctx.fillStyle = top; ctx.fillRect(0, 0, w, 220);
  });

  canvasTex(scene, 'ring', 256, 256, (ctx) => {
    ctx.strokeStyle = '#ffffff'; ctx.shadowColor = '#ffffff'; ctx.shadowBlur = 18; ctx.lineWidth = 8;
    ctx.beginPath(); ctx.arc(128, 128, 104, 0, Math.PI * 2); ctx.stroke();
  });

  canvasTex(scene, 'shade', 4, 4, (ctx) => { ctx.fillStyle = 'rgba(3,6,18,0.78)'; ctx.fillRect(0, 0, 4, 4); });
}

function panelTex(scene, w, h, opts = {}) {
  const accent = opts.accent ?? COLORS.line;
  const key = `panel_${w}x${h}_${accent}_${opts.flat ? 1 : 0}`;
  return canvasTex(scene, key, w + 8, h + 8, (ctx) => {
    const c = Math.min(22, h * 0.28);
    ctx.translate(4, 4);
    notchPath(ctx, 0, 0, w, h, c);
    const g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, hex(COLORS.panelHi, 0.96)); g.addColorStop(1, hex(COLORS.panel, 0.94));
    ctx.fillStyle = g; ctx.fill();
    ctx.lineWidth = 2; ctx.strokeStyle = hex(accent, 0.45); ctx.stroke();
    if (!opts.flat) {
      // bright accent edge + scanline texture
      ctx.save(); notchPath(ctx, 0, 0, w, h, c); ctx.clip();
      ctx.fillStyle = 'rgba(255,255,255,0.025)';
      for (let y = 0; y < h; y += 4) ctx.fillRect(0, y, w, 1);
      ctx.restore();
      ctx.strokeStyle = hex(accent, 1); ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(c + 6, 1); ctx.lineTo(Math.min(w * 0.45, c + 160), 1); ctx.stroke();
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(w - c - 2, h - 1); ctx.lineTo(w - c - 40, h - 1); ctx.stroke();
    }
  });
}

function buttonTex(scene, w, h, variant) {
  const key = `btn_${variant}_${w}x${h}`;
  return canvasTex(scene, key, w + 8, h + 12, (ctx) => {
    const c = Math.min(18, h * 0.32);
    ctx.translate(4, 4);
    const pal = {
      primary: ['#7cecff', '#1fa8e0', '#0b5d8a'],
      gold: ['#ffe07a', '#ffb52e', '#a8650a'],
      danger: ['#ff8a9c', '#e83656', '#7e1027'],
      ghost: [hex(COLORS.panelHi, 1), hex(COLORS.panel, 1), '#050916'],
      off: ['#3a4566', '#283152', '#151a2e'],
    }[variant];
    // depth
    notchPath(ctx, 0, 6, w, h, c); ctx.fillStyle = pal[2]; ctx.fill();
    notchPath(ctx, 0, 0, w, h, c);
    const g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, pal[0]); g.addColorStop(1, pal[1]);
    ctx.fillStyle = g; ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = variant === 'ghost' ? hex(COLORS.line, 0.7) : 'rgba(255,255,255,0.55)'; ctx.stroke();
    ctx.save(); notchPath(ctx, 0, 0, w, h, c); ctx.clip();
    ctx.fillStyle = 'rgba(255,255,255,0.14)'; ctx.fillRect(0, 0, w, h * 0.45);
    ctx.restore();
  });
}

function txt(scene, x, y, s, size, color = CSS.text, opts = {}) {
  const t = scene.add.text(x, y, s, {
    fontFamily: FONT, fontSize: size + 'px', fontStyle: opts.weight || '700', color,
    align: opts.align || 'center', wordWrap: opts.wrap ? { width: opts.wrap } : undefined,
    resolution: Math.min(2, window.devicePixelRatio || 1),
  });
  t.setOrigin(opts.ox ?? 0.5, opts.oy ?? 0.5);
  if (opts.spacing) t.setLetterSpacing(opts.spacing);
  if (opts.glow) t.setShadow(0, 0, opts.glow, opts.glowBlur ?? 16, false, true);
  return t;
}

// Tappable button with press feedback. Returns the container; call setLabel to change text.
function button(scene, x, y, w, h, label, onTap, variant = 'primary', opts = {}) {
  const c = scene.add.container(x, y);
  const bg = scene.add.image(0, 0, buttonTex(scene, w, h, variant)).setOrigin(0.5, (h / 2 + 4) / (h + 12));
  const dark = variant === 'primary' || variant === 'gold';
  const t = txt(scene, opts.icon ? 18 : 0, -1, label, opts.size || Math.round(h * 0.36), dark ? CSS.ink : CSS.text, { weight: '800', spacing: 2 });
  c.add([bg, t]);
  if (opts.icon) {
    const ic = scene.add.image(0, 0, 'game', opts.icon).setScale(opts.iconScale || 0.8);
    c.add(ic);
    c.layoutIcon = () => { ic.x = -t.width / 2 - 4; t.x = ic.displayWidth / 2 + 4; };
    c.layoutIcon();
  }
  c.label = t; c.bg = bg; c.variant = variant;
  c.setSize(w, h);
  c.setInteractive({ useHandCursor: true });
  c.on('pointerdown', () => { c.pressed = true; scene.tweens.add({ targets: c, scale: 0.94, duration: 70 }); });
  c.on('pointerout', () => { if (c.pressed) { c.pressed = false; scene.tweens.add({ targets: c, scale: 1, duration: 120 }); } });
  c.on('pointerup', () => {
    if (!c.pressed) return;
    c.pressed = false;
    scene.tweens.add({ targets: c, scale: 1, duration: 160, ease: 'Back.Out' });
    if (c.disabled) { Sfx.play('error'); return; }
    Sfx.play(opts.sound || 'click', { volume: 0.7 });
    onTap && onTap();
  });
  c.setLabel = (s) => { t.setText(s); c.layoutIcon && c.layoutIcon(); };
  c.setVariant = (v) => {
    c.variant = v;
    bg.setTexture(buttonTex(scene, w, h, v));
    t.setColor(v === 'primary' || v === 'gold' ? CSS.ink : (v === 'off' ? CSS.muted : CSS.text));
  };
  return c;
}

function panel(scene, x, y, w, h, opts) {
  return scene.add.image(x, y, panelTex(scene, w, h, opts)).setOrigin(0.5);
}

// Small "icon + value" chip used for credits and best score.
function chip(scene, x, y, icon, value, color = CSS.gold, origin = 0.5) {
  const c = scene.add.container(x, y);
  const t = txt(scene, 0, 0, value, 28, color, { weight: '800' });
  const ic = scene.add.image(0, 0, 'game', icon).setScale(0.9);
  const bg = scene.add.graphics();
  c.add([bg, ic, t]);
  c.setValue = (v) => {
    t.setText(v);
    const w = ic.displayWidth + t.width + 44;
    bg.clear();
    bg.fillStyle(COLORS.ink, 0.72); bg.lineStyle(2, COLORS.line, 0.35);
    bg.fillRoundedRect(-w * origin, -24, w, 48, 24); bg.strokeRoundedRect(-w * origin, -24, w, 48, 24);
    ic.x = -w * origin + 20 + ic.displayWidth / 2;
    t.x = ic.x + ic.displayWidth / 2 + 8 + t.width / 2;
  };
  c.setValue(value);
  return c;
}

function safeInsets(scene) {
  const s = scene.scale.displayScale ? scene.scale.displayScale.y : 1;
  return { top: (window.SAFE?.top || 0) * s, bottom: (window.SAFE?.bottom || 0) * s };
}

// Parallax starfield: tiled sky, drifting nebula clouds, a planet and two star layers.
class SpaceBG {
  constructor(scene, sector = 0) {
    this.scene = scene;
    const H = scene.scale.height;
    this.H = H;
    this.speed = 1;
    this.sky = scene.add.tileSprite(W / 2, H / 2, W, H, SECTORS[sector % SECTORS.length].bg).setTint(0xb8b8d8).setDepth(-100);
    this.nebula = [0, 1].map(i => scene.add.image(W * (i ? 0.85 : 0.15), H * (i ? 0.25 : 0.7), 'game', 'fx_smoke_07')
      .setScale(7 + i * 2).setAlpha(0.32).setBlendMode('ADD').setTint(SECTORS[sector % SECTORS.length].nebula).setDepth(-95));
    this.planet = scene.add.image(W * 0.8, H * 0.44, 'planets', SECTORS[sector % SECTORS.length].planet).setScale(0.6).setAlpha(0.8).setTint(0xb0b4d0).setDepth(-90);
    this.far = scene.add.tileSprite(W / 2, H / 2, W, H, 'stars_far').setDepth(-85);
    this.near = scene.add.tileSprite(W / 2, H / 2, W, H, 'stars_near').setDepth(-80);
    this.vig = scene.add.image(W / 2, H / 2, 'vignette').setDepth(-10);
    this.t = 0;
  }
  setSector(i) {
    const s = SECTORS[i % SECTORS.length];
    const scene = this.scene;
    const old = this.sky;
    this.sky = scene.add.tileSprite(W / 2, this.H / 2, W, this.H, s.bg).setTint(0xb8b8d8).setDepth(-99).setAlpha(0);
    this.sky.tilePositionY = old.tilePositionY;
    scene.tweens.add({ targets: this.sky, alpha: 1, duration: 2500, onComplete: () => { old.destroy(); this.sky.setDepth(-100); } });
    this.nebula.forEach(n => {
      const from = Phaser.Display.Color.IntegerToColor(n.tintTopLeft), to = Phaser.Display.Color.IntegerToColor(s.nebula);
      scene.tweens.addCounter({ from: 0, to: 100, duration: 2500, onUpdate: (tw) => {
        const c = Phaser.Display.Color.Interpolate.ColorWithColor(from, to, 100, tw.getValue());
        n.setTint(Phaser.Display.Color.GetColor(c.r, c.g, c.b));
      } });
    });
    this.nextPlanet = s.planet;
  }
  update(dt) {
    const v = this.speed;
    this.t += dt;
    this.sky.tilePositionY -= 12 * dt * v;
    this.far.tilePositionY -= 30 * dt * v;
    this.near.tilePositionY -= 95 * dt * v;
    this.planet.y += 9 * dt * v;
    if (this.planet.y > this.H + 260) {
      this.planet.y = -260;
      this.planet.x = Phaser.Math.Between(80, W - 80);
      if (this.nextPlanet) { this.planet.setFrame(this.nextPlanet); this.nextPlanet = null; }
      this.planet.setScale(Phaser.Math.FloatBetween(0.4, 0.7));
    }
    this.nebula.forEach((n, i) => {
      n.y += (5 + i * 3) * dt * v;
      n.rotation += 0.01 * dt * (i ? -1 : 1);
      if (n.y > this.H + 500) { n.y = -500; n.x = Phaser.Math.Between(0, W); }
    });
  }
}

// Boots Phaser with a portrait canvas whose height follows the device aspect ratio.
(function () {
  const probe = document.getElementById('safe-probe');
  const cs = probe ? getComputedStyle(probe) : null;
  window.SAFE = { top: cs ? parseFloat(cs.paddingTop) || 0 : 0, bottom: cs ? parseFloat(cs.paddingBottom) || 0 : 0 };
  const aspect = window.innerHeight / Math.max(1, window.innerWidth);
  const H = aspect < 1.2 ? 1280 : Math.round(Phaser.Math.Clamp(W * aspect, 1180, 1560));
  const game = new Phaser.Game({
    type: Phaser.AUTO,
    parent: 'game',
    backgroundColor: '#070B1A',
    width: W,
    height: H,
    scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
    input: { activePointers: 3 },
    render: { antialias: true, powerPreference: 'high-performance' },
    fps: { target: 60 },
    audio: { disableWebAudio: false },
    scene: [BootScene, MenuScene, HangarScene, GameScene, PauseScene, GameOverScene, SettingsScene],
  });
  window.__game = game;
  if ('serviceWorker' in navigator && location.protocol === 'https:' && window.top === window.self) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
})();

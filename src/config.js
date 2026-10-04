// Global game configuration, palette and balance data.
const W = 720;
const FONT = "'Exo 2', 'Trebuchet MS', sans-serif";

const COLORS = {
  ink: 0x070b1a,
  panel: 0x0c1430,
  panelHi: 0x16234d,
  line: 0x47e0ff,
  gold: 0xffc23d,
  danger: 0xff4d6a,
  good: 0x5cf29b,
  text: 0xe8f1ff,
  muted: 0x8aa0c8,
};
const CSS = {
  text: '#E8F1FF', muted: '#8AA0C8', line: '#47E0FF', gold: '#FFC23D', danger: '#FF4D6A', good: '#5CF29B', ink: '#070B1A',
};

const SHIPS = [
  {
    id: 'sahin', name: 'ŞAHİN', frame: 'playerShip1_blue', life: 'playerLife1_blue', dmgFrame: 'playerShip1_damage',
    laser: 'laserBlue01', laser2: 'laserBlue07', tint: 0x47e0ff, cost: 0,
    desc: 'Dengeli avcı. Her sektöre uyum sağlar.',
    hull: 5, rate: 1.0, power: 1.0, speed: 1.0, spread: 1.0,
  },
  {
    id: 'engerek', name: 'ENGEREK', frame: 'playerShip2_orange', life: 'playerLife2_orange', dmgFrame: 'playerShip2_damage',
    laser: 'laserRed01', laser2: 'laserRed07', tint: 0xff9a3d, cost: 2500,
    desc: 'Çok hızlı atış ve çevik manevra. Zırhı ince.',
    hull: 4, rate: 1.35, power: 0.9, speed: 1.15, spread: 0.65,
  },
  {
    id: 'titan', name: 'TİTAN', frame: 'playerShip3_green', life: 'playerLife3_green', dmgFrame: 'playerShip3_damage',
    laser: 'laserGreen01', laser2: 'laserGreen03', tint: 0x5cf29b, cost: 6000,
    desc: 'Ağır zırh ve geniş yaylım. Ağır ama yıkıcı.',
    hull: 7, rate: 0.85, power: 1.4, speed: 0.9, spread: 1.3,
  },
];

const UPGRADES = [
  { id: 'power', name: 'LAZER GÜCÜ', desc: 'Her atış %12 daha fazla hasar', icon: 'powerupRed_bolt' },
  { id: 'rate', name: 'ATIŞ HIZI', desc: 'Silahlar %8 daha hızlı ateşler', icon: 'powerupYellow_bolt' },
  { id: 'hull', name: 'GÖVDE ZIRHI', desc: '+1 gövde dayanıklılığı', icon: 'powerupGreen_shield' },
  { id: 'magnet', name: 'ÇEKİM ALANI', desc: 'Kredileri daha uzaktan toplar', icon: 'powerupBlue_star' },
  { id: 'nova', name: 'NOVA ÇEKİRDEĞİ', desc: 'Nova bombası %20 daha hızlı dolar', icon: 'powerupYellow_star' },
];
const UPGRADE_COST = [150, 350, 700, 1200, 2000];

// Each sector has its own sky, nebula hue, planet and enemy livery.
const SECTORS = [
  { name: 'ORION KAPISI', bg: 'bg_darkPurple', nebula: 0x6a3cff, planet: 'planet03', enemy: 'Green' },
  { name: 'MAVİ SİS', bg: 'bg_blue', nebula: 0x1f8bff, planet: 'planet06', enemy: 'Blue' },
  { name: 'KIZIL KUŞAK', bg: 'bg_purple', nebula: 0xff3c8a, planet: 'planet08', enemy: 'Red' },
  { name: 'HİÇLİK', bg: 'bg_black', nebula: 0x24d6b4, planet: 'planet01', enemy: 'Black' },
];
const BOSSES = [
  { name: 'DEMİR PENÇE', frame: 'spaceShips_005', scale: 0.9 },
  { name: 'GÖZCÜ-7', frame: 'spaceShips_004', scale: 1.0 },
  { name: 'KIZIL ÇENE', frame: 'spaceShips_002', scale: 1.05 },
  { name: 'HİÇLİK ÇOBANI', frame: 'spaceShips_003', scale: 1.05 },
  { name: 'SON AMİRAL', frame: 'spaceShips_008', scale: 1.2 },
];
const WAVES_PER_SECTOR = 6;

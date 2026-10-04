#!/usr/bin/env python3
"""Builds the game's texture atlas and audio from the original CC0 packs.

Usage: python3 tools/build_assets.py <downloads-dir>
The downloads dir must contain the unzipped Kenney packs and the OpenGameArt
music files (see CREDITS.md for sources). Output goes to assets/.
"""
import json, os, re, subprocess, sys
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else 'dl'
ROOT = os.path.join(os.path.dirname(__file__), '..', 'assets')
P = lambda *a: os.path.join(SRC, *a)


def xml_frames(xml):
    txt = open(xml).read()
    return {m[0].replace('.png', ''): tuple(map(int, m[1:])) for m in re.findall(
        r'name="([^"]+)" x="(\d+)" y="(\d+)" width="(\d+)" height="(\d+)"', txt)}


images = {}  # name -> PIL image


def from_sheet(png, xml, names, scale=1.0):
    sheet = Image.open(png).convert('RGBA')
    fr = xml_frames(xml)
    for n in names:
        x, y, w, h = fr[n]
        im = sheet.crop((x, y, x + w, y + h))
        if scale != 1.0:
            im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
        images[n] = im


def from_file(path, name, size=None):
    im = Image.open(path).convert('RGBA')
    if size:
        im = im.resize((size, round(im.height * size / im.width)), Image.LANCZOS)
    images[name] = im


# --- Space Shooter (Remastered) ---------------------------------------------
ss = P('space-shooter-remastered', 'Spritesheet')
names = []
for s, c in ((1, 'blue'), (2, 'orange'), (3, 'green')):
    names += [f'playerShip{s}_{c}', f'playerLife{s}_{c}'] + [f'playerShip{s}_damage{i}' for i in (1, 2, 3)]
names += [f'enemy{c}{i}' for c in ('Black', 'Blue', 'Green', 'Red') for i in range(1, 6)]
names += [f'ufo{c}' for c in ('Blue', 'Green', 'Red', 'Yellow')]
names += [f'laser{c}{i:02d}' for c in ('Blue', 'Green', 'Red') for i in range(1, 17)]
names += [n for n in xml_frames(os.path.join(ss, 'sheet.xml')) if n.startswith('meteor')]
names += [f'powerup{c}_{t}' for c in ('Blue', 'Green', 'Red', 'Yellow') for t in ('bolt', 'shield', 'star')]
names += [f'pill_{c}' for c in ('blue', 'green', 'red', 'yellow')]
names += ['shield1', 'shield2', 'shield3', 'speed', 'star1', 'star2', 'star3']
names += [f'fire{i:02d}' for i in range(20)]
names += [f'{t}_{m}' for t in ('star', 'shield', 'things') for m in ('gold', 'silver', 'bronze')] + ['bolt_gold']
from_sheet(os.path.join(ss, 'sheet.png'), os.path.join(ss, 'sheet.xml'), names)

# --- Space Shooter Extension (bosses, smoke, missiles, beams) ----------------
ex = P('space-shooter-extension', 'Spritesheet')
from_sheet(os.path.join(ex, 'spaceShooter2_spritesheet_2X.png'), os.path.join(ex, 'spaceShooter2_spritesheet_2X.xml'),
           [f'spaceShips_{i:03d}' for i in (2, 3, 4, 5, 8)])
from_sheet(os.path.join(ex, 'spaceShooter2_spritesheet_2X.png'), os.path.join(ex, 'spaceShooter2_spritesheet_2X.xml'),
           [f'spaceEffects_{i:03d}' for i in range(1, 19)] + [f'spaceMissiles_{i:03d}' for i in (1, 4, 7, 13, 19)], 0.6)

# --- Particle pack (white, tinted at runtime) -------------------------------
pp = P('particle-pack', 'PNG (Transparent)')
for n in ('flare_01', 'light_01', 'light_03', 'circle_05', 'spark_05', 'spark_06', 'star_06', 'star_07', 'smoke_07',
          'twirl_02', 'trace_01', 'magic_04', 'scorch_02'):
    from_file(os.path.join(pp, n + '.png'), 'fx_' + n, 128)

# --- Planets -----------------------------------------------------------------
for i in range(10):
    from_file(P('planets', 'Planets', f'planet{i:02d}.png'), f'planet{i:02d}', 320)


# --- Pack (shelf packer, tallest first) --------------------------------------
def pack(items, width):
    items = sorted(items, key=lambda kv: (-kv[1].height, -kv[1].width))
    x = y = shelf_h = 0
    pos = {}
    for n, im in items:
        w, h = im.width + 2, im.height + 2
        if x + w > width:
            x, y, shelf_h = 0, y + shelf_h, 0
        pos[n] = (x + 1, y + 1)
        x += w
        shelf_h = max(shelf_h, h)
    return pos, y + shelf_h


def write_atlas(name, subset, width=2048):
    pos, h = pack(list(subset.items()), width)
    h = 1 << (h - 1).bit_length()
    sheet = Image.new('RGBA', (width, h), (0, 0, 0, 0))
    frames = {}
    for n, (x, y) in pos.items():
        im = subset[n]
        sheet.paste(im, (x, y))
        frames[n] = {'frame': {'x': x, 'y': y, 'w': im.width, 'h': im.height}, 'rotated': False, 'trimmed': False,
                     'spriteSourceSize': {'x': 0, 'y': 0, 'w': im.width, 'h': im.height},
                     'sourceSize': {'w': im.width, 'h': im.height}}
    out = os.path.join(ROOT, 'img', name)
    sheet.save(out + '.png', optimize=True)
    json.dump({'frames': frames, 'meta': {'image': name + '.png', 'size': {'w': width, 'h': h}, 'scale': 1}},
              open(out + '.json', 'w'), separators=(',', ':'))
    print(name, width, 'x', h, len(frames), 'frames')


planets = {k: v for k, v in images.items() if k.startswith('planet')}
write_atlas('planets', planets, 1024)
write_atlas('game', {k: v for k, v in images.items() if k not in planets})

for bg in ('black', 'blue', 'darkPurple', 'purple'):
    Image.open(P('space-shooter-remastered', 'Backgrounds', bg + '.png')).save(os.path.join(ROOT, 'img', f'bg_{bg}.png'))

# --- Audio -------------------------------------------------------------------
AUD = os.path.join(ROOT, 'audio')
sfx = {
    'shoot': 'space-shooter-remastered/Bonus/sfx_laser1.ogg',
    'eshoot': 'sci-fi-sounds/Audio/laserSmall_001.ogg',
    'hit': 'impact-sounds/Audio/impactMetal_light_002.ogg',
    'explode': 'sci-fi-sounds/Audio/explosionCrunch_000.ogg',
    'explode_big': 'sci-fi-sounds/Audio/lowFrequency_explosion_000.ogg',
    'coin': 'digital-audio/Audio/pepSound2.ogg',
    'powerup': 'digital-audio/Audio/powerUp7.ogg',
    'shield_up': 'space-shooter-remastered/Bonus/sfx_shieldUp.ogg',
    'shield_down': 'space-shooter-remastered/Bonus/sfx_shieldDown.ogg',
    'hurt': 'sci-fi-sounds/Audio/impactMetal_002.ogg',
    'lose': 'space-shooter-remastered/Bonus/sfx_lose.ogg',
    'nova': 'sci-fi-sounds/Audio/laserLarge_003.ogg',
    'warning': 'sci-fi-sounds/Audio/forceField_001.ogg',
    'click': 'interface-sounds/Audio/click_002.ogg',
    'select': 'interface-sounds/Audio/select_003.ogg',
    'buy': 'interface-sounds/Audio/confirmation_002.ogg',
    'error': 'interface-sounds/Audio/error_004.ogg',
    'wave': 'digital-audio/Audio/phaserUp3.ogg',
    'win': 'music-jingles/Audio/Steel jingles/jingles_STEEL00.ogg',
    'gameover': 'music-jingles/Audio/Steel jingles/jingles_STEEL16.ogg',
    'missile': 'sci-fi-sounds/Audio/thrusterFire_001.ogg',
}
for k, f in sfx.items():
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', P(f), '-ac', '1', '-b:a', '80k', os.path.join(AUD, k + '.mp3')], check=True)
music = {
    'music_menu': ('music/gravity_turn_calm_6.mp3', None),
    'music_game': ('music/gravity_turn_action_2.mp3', None),
    'music_boss': ('music/Spacecrusher_0.ogg', None),
}
for k, (f, _) in music.items():
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', P(f), '-ac', '2', '-b:a', '96k', os.path.join(AUD, k + '.mp3')], check=True)
print('audio done')

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random
import struct

# Initialize Pygame with audio support
pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()
display = (800, 600)
screen = pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
pygame.display.set_caption("CYBER DUCK // NEON HUNT")

# OpenGL setup
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
glMatrixMode(GL_MODELVIEW)
glEnable(GL_DEPTH_TEST)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# Fonts
pygame.font.init()
font_large = pygame.font.SysFont("Courier New", 48, bold=True)
font_medium = pygame.font.SysFont("Courier New", 32, bold=True)
font_small = pygame.font.SysFont("Courier New", 22)
font_tiny = pygame.font.SysFont("Courier New", 16)


# --- Synthwave Music Generator ---

def generate_synthwave_music():
    """Generate layered synthwave/cyberpunk background music."""
    sample_rate = 22050

    # Channel 1: Deep bass synth (~4 sec loop)
    # Pulsing sub-bass with slight detune for thickness
    bass_dur = 4.0
    n_bass = int(sample_rate * bass_dur)
    bass_samples = []
    # Bass pattern: E1-E1-G1-A1 (quarter notes at ~120bpm = 0.5s each)
    bass_notes = [82.41, 82.41, 98.0, 110.0, 82.41, 73.42, 82.41, 98.0]
    note_len = n_bass // len(bass_notes)
    for i in range(n_bass):
        t = i / sample_rate
        note_idx = min(i // note_len, len(bass_notes) - 1)
        freq = bass_notes[note_idx]
        # Sub bass + slight saw character
        val = (math.sin(2 * math.pi * freq * t) * 0.3 +
               math.sin(2 * math.pi * freq * 2 * t) * 0.1 +
               math.sin(2 * math.pi * freq * 0.5 * t) * 0.15)
        # Pulse envelope per note
        pos_in_note = (i % note_len) / note_len
        env = max(0, 1.0 - pos_in_note * 0.6)
        # Loop fade
        fade = int(sample_rate * 0.1)
        if i < fade:
            env *= i / fade
        elif i > n_bass - fade:
            env *= (n_bass - i) / fade
        bass_samples.append(int(val * env * 32767))

    bass_bytes = struct.pack(f"<{len(bass_samples)}h", *bass_samples)
    bass_sound = pygame.mixer.Sound(buffer=bass_bytes)
    bass_sound.set_volume(0.18)

    # Channel 2: Synth arpeggio (~3 sec loop)
    arp_dur = 3.0
    n_arp = int(sample_rate * arp_dur)
    arp_samples = []
    # Minor arpeggio pattern (E-G-B-E')
    arp_notes = [329.63, 392.0, 493.88, 659.25, 493.88, 392.0]
    arp_note_len = n_arp // len(arp_notes)
    for i in range(n_arp):
        t = i / sample_rate
        note_idx = min(i // arp_note_len, len(arp_notes) - 1)
        freq = arp_notes[note_idx]
        # Square-ish wave for that retro synth feel
        sine = math.sin(2 * math.pi * freq * t)
        val = (sine * 0.2 +
               (1.0 if sine > 0 else -1.0) * 0.05)  # slight square mix
        # Sharp attack, quick decay
        pos_in_note = (i % arp_note_len) / arp_note_len
        env = max(0, 1.0 - pos_in_note * 1.5) if pos_in_note < 0.7 else 0
        fade = int(sample_rate * 0.08)
        if i < fade:
            env *= i / fade
        elif i > n_arp - fade:
            env *= (n_arp - i) / fade
        arp_samples.append(int(val * env * 32767))

    arp_bytes = struct.pack(f"<{len(arp_samples)}h", *arp_samples)
    arp_sound = pygame.mixer.Sound(buffer=arp_bytes)
    arp_sound.set_volume(0.10)

    # Channel 3: Atmospheric pad (~6 sec loop)
    pad_dur = 6.0
    n_pad = int(sample_rate * pad_dur)
    pad_samples = []
    for i in range(n_pad):
        t = i / sample_rate
        # Lush detuned pad - minor chord
        val = (math.sin(2 * math.pi * 164.81 * t) * 0.08 +   # E3
               math.sin(2 * math.pi * 165.5 * t) * 0.06 +    # E3 detuned
               math.sin(2 * math.pi * 196.0 * t) * 0.07 +    # G3
               math.sin(2 * math.pi * 246.94 * t) * 0.06 +   # B3
               math.sin(2 * math.pi * 329.63 * t) * 0.04)    # E4
        # Slow LFO modulation
        lfo = 0.7 + 0.3 * math.sin(2 * math.pi * 0.25 * t)
        val *= lfo
        fade = int(sample_rate * 0.5)
        if i < fade:
            val *= i / fade
        elif i > n_pad - fade:
            val *= (n_pad - i) / fade
        pad_samples.append(int(val * 32767))

    pad_bytes = struct.pack(f"<{len(pad_samples)}h", *pad_samples)
    pad_sound = pygame.mixer.Sound(buffer=pad_bytes)
    pad_sound.set_volume(0.14)

    # Channel 4: Rain/static texture (~2 sec loop)
    rain_dur = 2.0
    n_rain = int(sample_rate * rain_dur)
    rng = random.Random(777)
    raw = [rng.uniform(-1, 1) for _ in range(n_rain)]
    # Bandpass-ish filter for rain
    window = 15
    rain_samples = []
    running_sum = sum(raw[:window])
    for i in range(n_rain):
        avg = running_sum / window
        fade_env = 1.0
        fade = int(sample_rate * 0.1)
        if i < fade:
            fade_env = i / fade
        elif i > n_rain - fade:
            fade_env = (n_rain - i) / fade
        rain_samples.append(int(avg * fade_env * 0.12 * 32767))
        new_idx = i + window
        if new_idx < n_rain:
            running_sum += raw[new_idx] - raw[i]

    rain_bytes = struct.pack(f"<{len(rain_samples)}h", *rain_samples)
    rain_sound = pygame.mixer.Sound(buffer=rain_bytes)
    rain_sound.set_volume(0.06)

    return bass_sound, arp_sound, pad_sound, rain_sound


_music_started = False


def start_music():
    global _music_started
    if _music_started:
        return
    _music_started = True
    bass, arp, pad, rain = generate_synthwave_music()
    pygame.mixer.Channel(1).play(bass, loops=-1)
    pygame.mixer.Channel(2).play(arp, loops=-1)
    pygame.mixer.Channel(3).play(pad, loops=-1)
    pygame.mixer.Channel(4).play(rain, loops=-1)


# --- HUD rendering ---

def draw_text_2d(text, x, y, font, color=(255, 255, 0)):
    """Render text as a 2D overlay."""
    text_surface = font.render(text, True, color)
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    w, h = text_surface.get_size()

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, display[0], 0, display[1], -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glRasterPos2f(x, display[1] - y - h)
    glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    glEnable(GL_DEPTH_TEST)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# --- Neon colors ---
NEON_PINK = (1.0, 0.08, 0.58)
NEON_CYAN = (0.0, 1.0, 0.95)
NEON_YELLOW = (1.0, 0.95, 0.0)
NEON_PURPLE = (0.7, 0.0, 1.0)
NEON_ORANGE = (1.0, 0.4, 0.0)
NEON_GREEN = (0.2, 1.0, 0.3)
DARK_BG = (0.02, 0.01, 0.06)


# --- Rain particle ---

class RainDrop:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.uniform(-8, 8)
        self.y = random.uniform(5, 10)
        self.z = random.uniform(-12, -1)
        self.speed = random.uniform(0.08, 0.18)
        self.length = random.uniform(0.1, 0.3)

    def update(self):
        self.y -= self.speed
        if self.y < -1.5:
            self.reset()

    def draw(self):
        alpha = 0.15 + 0.1 * (1.0 - abs(self.z + 6) / 6.0)
        glColor4f(0.4, 0.5, 0.9, alpha)
        glBegin(GL_LINES)
        glVertex3f(self.x, self.y, self.z)
        glVertex3f(self.x - 0.01, self.y - self.length, self.z)
        glEnd()


# --- Cyber Duck ---

class Duck:
    # Neon color schemes for each duck
    SCHEMES = [
        (NEON_PINK, NEON_CYAN),
        (NEON_CYAN, NEON_PINK),
        (NEON_YELLOW, NEON_PURPLE),
        (NEON_GREEN, NEON_ORANGE),
        (NEON_PURPLE, NEON_GREEN),
    ]

    def __init__(self, scheme_idx=0):
        self.quad = gluNewQuadric()
        self.scheme_idx = scheme_idx % len(self.SCHEMES)
        self.body_color = self.SCHEMES[self.scheme_idx][0]
        self.accent_color = self.SCHEMES[self.scheme_idx][1]
        self.reset()

    def reset(self):
        self.x = random.uniform(-3, 3)
        self.y = random.uniform(0.5, 2.5)
        self.z = random.uniform(-8, -3)
        self.vx = random.choice([-1, 1]) * random.uniform(0.02, 0.06)
        self.vy = random.uniform(-0.01, 0.01)
        self.alive = True
        self.hit_flash = 0
        self.wing_angle = random.uniform(0, math.pi * 2)
        self.glow_phase = random.uniform(0, math.pi * 2)

    def update(self):
        if not self.alive:
            return
        self.x += self.vx
        self.y += self.vy
        if self.x > 4.5 or self.x < -4.5:
            self.vx *= -1
        if self.y > 3.0 or self.y < 0.2:
            self.vy *= -1
        if self.hit_flash > 0:
            self.hit_flash -= 1
        self.wing_angle += 0.15
        self.glow_phase += 0.05

    def _glow_color(self, base, intensity=1.0):
        """Pulsing neon glow."""
        pulse = 0.7 + 0.3 * math.sin(self.glow_phase)
        r, g, b = base
        return (r * pulse * intensity, g * pulse * intensity, b * pulse * intensity)

    def draw(self):
        if not self.alive:
            return
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)

        if self.vx < 0:
            glScalef(-1, 1, 1)

        bc = self._glow_color(self.body_color)
        ac = self._glow_color(self.accent_color)

        # --- Glow halo (additive blending effect) ---
        glPushMatrix()
        glScalef(1.3, 1.3, 1.3)
        glColor4f(bc[0] * 0.3, bc[1] * 0.3, bc[2] * 0.3, 0.15)
        gluSphere(self.quad, 0.3, 12, 12)
        glPopMatrix()

        # --- Body ---
        if self.hit_flash > 0:
            glColor3f(1.0, 1.0, 1.0)
        else:
            glColor3f(*bc)
        gluSphere(self.quad, 0.25, 20, 20)

        # --- Neon wireframe ring around body ---
        glColor4f(*ac, 0.6)
        glPushMatrix()
        glRotatef(90, 1, 0, 0)
        gluDisk(self.quad, 0.24, 0.26, 20, 1)
        glPopMatrix()

        # --- Head ---
        glPushMatrix()
        glTranslatef(0.2, 0.28, 0.0)
        if self.hit_flash > 0:
            glColor3f(1.0, 1.0, 1.0)
        else:
            glColor3f(*ac)
        gluSphere(self.quad, 0.14, 16, 16)

        # --- Visor/Eye (cyber eye) ---
        glPushMatrix()
        glTranslatef(0.1, 0.04, 0.0)
        glScalef(0.12, 0.04, 0.14)
        glColor3f(1.0, 0.1, 0.1)  # Red visor
        gluSphere(self.quad, 1.0, 8, 8)
        glPopMatrix()

        # Eye glow dot
        glPushMatrix()
        glTranslatef(0.12, 0.04, 0.05)
        glColor3f(1.0, 0.0, 0.0)
        gluSphere(self.quad, 0.02, 6, 6)
        glPopMatrix()

        # --- Beak (metallic) ---
        glPushMatrix()
        glTranslatef(0.13, -0.02, 0.0)
        glRotatef(90, 0, 1, 0)
        glColor3f(0.5, 0.5, 0.55)
        gluCylinder(self.quad, 0.04, 0.01, 0.14, 6, 2)
        glPopMatrix()

        glPopMatrix()  # end head

        # --- Wings (animated, neon edges) ---
        wing_flap = math.sin(self.wing_angle) * 0.18
        for z_side in [0.22, -0.22]:
            glPushMatrix()
            glTranslatef(-0.05, 0.05 + wing_flap * (1 if z_side > 0 else -1), z_side)
            glScalef(0.5, 0.2, 0.06)
            if self.hit_flash > 0:
                glColor3f(1.0, 1.0, 1.0)
            else:
                glColor4f(*bc, 0.8)
            gluSphere(self.quad, 0.35, 8, 8)
            glPopMatrix()

        # --- Tail (angular, cyber) ---
        glPushMatrix()
        glTranslatef(-0.3, 0.12, 0.0)
        glRotatef(-25, 0, 0, 1)
        glScalef(0.25, 0.08, 0.15)
        glColor3f(*ac)
        gluSphere(self.quad, 0.3, 6, 6)
        glPopMatrix()

        # --- Antenna ---
        glPushMatrix()
        glTranslatef(0.2, 0.42, 0.0)
        glColor4f(*ac, 0.8)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0.05, 0.15, 0)
        glEnd()
        # Tip glow
        glTranslatef(0.05, 0.15, 0)
        pulse = 0.5 + 0.5 * math.sin(self.glow_phase * 3)
        glColor4f(1.0, 0.2, 0.2, pulse)
        gluSphere(self.quad, 0.02, 6, 6)
        glPopMatrix()

        glPopMatrix()  # end duck

    def get_screen_pos(self, viewport, modelview, projection):
        win = gluProject(self.x, self.y, self.z, modelview, projection, viewport)
        return win[0], display[1] - win[1]

    def is_hit(self, mouse_x, mouse_y, viewport, modelview, projection):
        if not self.alive:
            return False
        sx, sy = self.get_screen_pos(viewport, modelview, projection)
        edge = gluProject(self.x + 0.25, self.y, self.z, modelview, projection, viewport)
        screen_radius = abs(edge[0] - sx) * 2.5
        dist = math.sqrt((mouse_x - sx) ** 2 + (mouse_y - sy) ** 2)
        return dist < max(screen_radius, 20)


# --- Holographic Particle ---

class Particle:
    def __init__(self, x, y, z, color_scheme):
        self.x = x
        self.y = y
        self.z = z
        self.vx = random.uniform(-0.07, 0.07)
        self.vy = random.uniform(0.02, 0.1)
        self.vz = random.uniform(-0.03, 0.03)
        self.life = 1.0
        self.quad = gluNewQuadric()
        body_col, accent_col = color_scheme
        self.color = random.choice([body_col, accent_col, (1.0, 1.0, 1.0)])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy -= 0.002
        self.life -= 0.03

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        r, g, b = self.color
        glColor4f(r, g, b, self.life * 0.8)
        gluSphere(self.quad, 0.035 * self.life, 6, 6)
        glPopMatrix()


# --- Building for city skyline ---

class Building:
    def __init__(self, x, z, rng):
        self.x = x
        self.z = z
        self.width = rng.uniform(0.4, 1.2)
        self.depth = rng.uniform(0.3, 0.8)
        self.height = rng.uniform(1.5, 6.0)
        self.base_color = (rng.uniform(0.03, 0.08),
                           rng.uniform(0.03, 0.07),
                           rng.uniform(0.08, 0.15))
        # Neon accent on top or side
        accent_choices = [NEON_PINK, NEON_CYAN, NEON_PURPLE, NEON_YELLOW, NEON_ORANGE]
        self.accent = accent_choices[rng.randint(0, len(accent_choices) - 1)]
        # Windows: list of (wx, wy) normalized positions + on/off
        self.windows = []
        n_floors = max(1, int(self.height / 0.4))
        n_cols = max(1, int(self.width / 0.25))
        for floor in range(n_floors):
            for col in range(n_cols):
                if rng.random() < 0.6:
                    wy = -1.0 + 0.3 + floor * 0.4
                    wx_offset = -self.width / 2 + 0.15 + col * 0.25
                    # Window color: warm yellow or cool cyan
                    wc = (0.9, 0.8, 0.3) if rng.random() < 0.7 else (0.2, 0.7, 0.9)
                    brightness = rng.uniform(0.3, 1.0)
                    self.windows.append((wx_offset, wy, wc, brightness))

    def draw(self, frame):
        glPushMatrix()
        glTranslatef(self.x, -1.0, self.z)

        # Building body
        r, g, b = self.base_color
        hw = self.width / 2
        hd = self.depth / 2
        h = self.height

        # Front face
        glBegin(GL_QUADS)
        glColor3f(r * 1.2, g * 1.2, b * 1.2)
        glVertex3f(-hw, 0, hd)
        glVertex3f(hw, 0, hd)
        glVertex3f(hw, h, hd)
        glVertex3f(-hw, h, hd)
        # Right face
        glColor3f(r * 0.8, g * 0.8, b * 0.8)
        glVertex3f(hw, 0, hd)
        glVertex3f(hw, 0, -hd)
        glVertex3f(hw, h, -hd)
        glVertex3f(hw, h, hd)
        # Left face
        glColor3f(r * 0.9, g * 0.9, b * 0.9)
        glVertex3f(-hw, 0, -hd)
        glVertex3f(-hw, 0, hd)
        glVertex3f(-hw, h, hd)
        glVertex3f(-hw, h, -hd)
        # Back face
        glColor3f(r * 0.6, g * 0.6, b * 0.6)
        glVertex3f(hw, 0, -hd)
        glVertex3f(-hw, 0, -hd)
        glVertex3f(-hw, h, -hd)
        glVertex3f(hw, h, -hd)
        # Top
        glColor3f(r * 0.5, g * 0.5, b * 0.7)
        glVertex3f(-hw, h, -hd)
        glVertex3f(hw, h, -hd)
        glVertex3f(hw, h, hd)
        glVertex3f(-hw, h, hd)
        glEnd()

        # Neon accent strip on top edge
        ar, ag, ab = self.accent
        pulse = 0.6 + 0.4 * math.sin(frame * 0.03 + self.x)
        glColor4f(ar * pulse, ag * pulse, ab * pulse, 0.9)
        glBegin(GL_QUADS)
        glVertex3f(-hw - 0.02, h, hd + 0.02)
        glVertex3f(hw + 0.02, h, hd + 0.02)
        glVertex3f(hw + 0.02, h + 0.05, hd + 0.02)
        glVertex3f(-hw - 0.02, h + 0.05, hd + 0.02)
        glEnd()

        # Windows on front face
        glBegin(GL_QUADS)
        for wx, wy, wc, bright in self.windows:
            if wy > h - 0.3:
                continue
            # Flicker
            flicker = bright * (0.85 + 0.15 * math.sin(frame * 0.07 + wx * 13.7 + wy * 7.3))
            glColor4f(wc[0] * flicker, wc[1] * flicker, wc[2] * flicker, 0.9)
            ws = 0.08
            glVertex3f(wx - ws, wy + 1.0, hd + 0.01)
            glVertex3f(wx + ws, wy + 1.0, hd + 0.01)
            glVertex3f(wx + ws, wy + 1.0 + 0.15, hd + 0.01)
            glVertex3f(wx - ws, wy + 1.0 + 0.15, hd + 0.01)
        glEnd()

        glPopMatrix()


# --- Main Game ---

class Game:
    def __init__(self):
        self.ducks = [Duck(i) for i in range(5)]
        self.score = 0
        self.misses = 0
        self.max_misses = 10
        self.clock = pygame.time.Clock()
        self.particles = []
        self.game_over = False
        self.shoot_cooldown = 0
        self.frame = 0
        self.muted = False
        self.scenery_quad = gluNewQuadric()

        # Rain
        self.rain = [RainDrop() for _ in range(150)]

        # City skyline - buildings at various depths
        rng = random.Random(42069)
        self.buildings = []
        # Far row
        for i in range(20):
            x = -12 + i * 1.3 + rng.uniform(-0.3, 0.3)
            self.buildings.append(Building(x, rng.uniform(-14, -12), rng))
        # Mid row
        for i in range(15):
            x = -10 + i * 1.5 + rng.uniform(-0.4, 0.4)
            self.buildings.append(Building(x, rng.uniform(-11, -9.5), rng))

        # Neon signs data (positioned on buildings)
        self.neon_signs = []
        sign_texts = ["CYBER", "NEON", "2077", "DUCK", "HUNT", "SYNTH"]
        for i in range(6):
            sx = rng.uniform(-6, 6)
            sy = rng.uniform(1.5, 4.0)
            sz = rng.uniform(-13, -10)
            color = [NEON_PINK, NEON_CYAN, NEON_YELLOW, NEON_PURPLE, NEON_ORANGE, NEON_GREEN][i]
            self.neon_signs.append((sx, sy, sz, sign_texts[i], color))

        # Ground grid color
        self.grid_color_1 = NEON_CYAN
        self.grid_color_2 = NEON_PINK

        start_music()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self.__init__()
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_m:
                    self.muted = not self.muted
                    if self.muted:
                        pygame.mixer.pause()
                    else:
                        pygame.mixer.unpause()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.game_over:
                    self.shoot(event.pos)
        return True

    def shoot(self, mouse_pos):
        if self.shoot_cooldown > 0:
            return
        self.shoot_cooldown = 5

        viewport = glGetIntegerv(GL_VIEWPORT)
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)

        mx, my = mouse_pos
        hit_any = False
        for duck in self.ducks:
            if duck.is_hit(mx, my, viewport, modelview, projection):
                duck.alive = False
                self.score += 1
                hit_any = True
                scheme = Duck.SCHEMES[duck.scheme_idx]
                for _ in range(20):
                    self.particles.append(Particle(duck.x, duck.y, duck.z, scheme))
                break

        if not hit_any:
            self.misses += 1
            if self.misses >= self.max_misses:
                self.game_over = True

    def update(self):
        self.frame += 1
        if self.game_over:
            return

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        for duck in self.ducks:
            duck.update()

        for i, duck in enumerate(self.ducks):
            if not duck.alive and duck.hit_flash == 0:
                self.ducks[i] = Duck(random.randint(0, 4))

        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

        for drop in self.rain:
            drop.update()

    # --- Drawing methods ---

    def draw_sky(self):
        """Dark cyberpunk sky gradient."""
        glBegin(GL_QUADS)
        # Bottom: dark purple haze
        glColor3f(0.05, 0.02, 0.1)
        glVertex3f(-20, -1.0, -15)
        glVertex3f(20, -1.0, -15)
        # Top: near black with slight blue
        glColor3f(0.01, 0.01, 0.04)
        glVertex3f(20, 8.0, -15)
        glVertex3f(-20, 8.0, -15)
        glEnd()

        # Distant neon horizon glow
        glBegin(GL_QUADS)
        t = self.frame * 0.01
        glow_r = 0.15 + 0.05 * math.sin(t)
        glow_b = 0.25 + 0.05 * math.sin(t * 0.7)
        glColor4f(glow_r, 0.02, glow_b, 0.8)
        glVertex3f(-20, -1.0, -14.99)
        glVertex3f(20, -1.0, -14.99)
        glColor4f(0, 0, 0, 0)
        glVertex3f(20, 2.0, -14.99)
        glVertex3f(-20, 2.0, -14.99)
        glEnd()

    def draw_city(self):
        """Draw the cyberpunk city skyline."""
        for bldg in self.buildings:
            bldg.draw(self.frame)

    def draw_neon_grid(self):
        """Draw the Tron-style neon grid floor."""
        # Dark ground base
        glBegin(GL_QUADS)
        glColor3f(0.02, 0.02, 0.04)
        glVertex3f(-10, -1.0, -15)
        glVertex3f(10, -1.0, -15)
        glVertex3f(10, -1.0, 2)
        glVertex3f(-10, -1.0, 2)
        glEnd()

        # Grid lines
        grid_spacing = 1.0
        t = self.frame * 0.015
        # Scrolling Z offset for movement illusion
        z_offset = (t * 0.5) % grid_spacing

        # Z-direction lines (horizontal stripes moving toward camera)
        for i in range(-15, 3):
            z = i + z_offset
            dist = abs(z + 5) / 10.0  # distance-based fade
            alpha = max(0, 0.3 - dist * 0.2)
            # Alternate colors
            cr, cg, cb = self.grid_color_1 if i % 2 == 0 else self.grid_color_2
            glColor4f(cr * 0.4, cg * 0.4, cb * 0.4, alpha)
            glBegin(GL_LINES)
            glVertex3f(-10, -0.99, z)
            glVertex3f(10, -0.99, z)
            glEnd()

        # X-direction lines
        for i in range(-10, 11):
            dist = abs(i) / 10.0
            alpha = max(0, 0.25 - dist * 0.15)
            cr, cg, cb = self.grid_color_1
            glColor4f(cr * 0.3, cg * 0.3, cb * 0.3, alpha)
            glBegin(GL_LINES)
            glVertex3f(i, -0.99, -15)
            glVertex3f(i, -0.99, 2)
            glEnd()

    def draw_rain(self):
        """Draw cyberpunk rain."""
        for drop in self.rain:
            drop.draw()

    def draw_hud(self):
        """Draw cyberpunk-styled HUD."""
        # Score with neon glow effect (draw twice offset for glow)
        draw_text_2d(f"SCORE: {self.score:04d}", 22, 22, font_large, (0, 80, 80))
        draw_text_2d(f"SCORE: {self.score:04d}", 20, 20, font_large, (0, 255, 240))

        misses_left = self.max_misses - self.misses
        if misses_left <= 3:
            color = (255, 20, 80)
            shadow = (80, 0, 30)
        else:
            color = (200, 180, 255)
            shadow = (60, 50, 80)
        draw_text_2d(f"AMMO: {'|' * misses_left}{'.' * self.misses}", 22, 82, font_small, shadow)
        draw_text_2d(f"AMMO: {'|' * misses_left}{'.' * self.misses}", 20, 80, font_small, color)

        # Bottom bar
        draw_text_2d("[LMB] FIRE  [M] MUTE  [ESC] EXIT", 20, display[1] - 35, font_tiny, (100, 80, 120))

        # Top right - system status
        pulse_alpha = int(128 + 127 * math.sin(self.frame * 0.05))
        draw_text_2d("SYS:ONLINE", display[0] - 165, 20, font_small, (0, pulse_alpha, 0))
        draw_text_2d(f"FRM:{self.frame:06d}", display[0] - 165, 45, font_tiny, (80, 80, 100))

        # Scanline effect hint (thin lines)
        if self.frame % 3 == 0:
            scan_y = (self.frame * 2) % display[1]
            draw_text_2d("_" * 100, 0, scan_y, font_tiny, (20, 20, 30))

        if self.game_over:
            # Glitch effect: offset text
            ox = random.randint(-3, 3) if self.frame % 5 == 0 else 0
            oy = random.randint(-2, 2) if self.frame % 7 == 0 else 0

            # Background flash
            draw_text_2d("SYSTEM FAILURE", display[0] // 2 - 190 + ox,
                         display[1] // 2 - 70 + oy, font_large, (255, 0, 60))
            draw_text_2d("SYSTEM FAILURE", display[0] // 2 - 188,
                         display[1] // 2 - 72, font_large, (80, 0, 20))

            draw_text_2d(f"FINAL SCORE: {self.score:04d}", display[0] // 2 - 160,
                         display[1] // 2 + 5, font_medium, (0, 255, 240))
            draw_text_2d("[R] REBOOT SYSTEM", display[0] // 2 - 130,
                         display[1] // 2 + 55, font_small, (180, 180, 200))

    def draw_crosshair(self):
        """Draw a neon crosshair at mouse position."""
        mx, my = pygame.mouse.get_pos()

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, display[0], display[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        size = 12
        gap = 4
        pulse = 0.7 + 0.3 * math.sin(self.frame * 0.1)

        glColor4f(0.0, 1.0, 0.9, pulse * 0.9)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        # Top
        glVertex2f(mx, my - size)
        glVertex2f(mx, my - gap)
        # Bottom
        glVertex2f(mx, my + gap)
        glVertex2f(mx, my + size)
        # Left
        glVertex2f(mx - size, my)
        glVertex2f(mx - gap, my)
        # Right
        glVertex2f(mx + gap, my)
        glVertex2f(mx + size, my)
        glEnd()

        # Center dot
        glColor4f(1.0, 0.1, 0.5, pulse)
        glPointSize(3.0)
        glBegin(GL_POINTS)
        glVertex2f(mx, my)
        glEnd()

        glLineWidth(1.0)
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def render(self):
        glClearColor(*DARK_BG, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        gluLookAt(0, 1, 2,
                  0, 1, -5,
                  0, 1, 0)

        self.draw_sky()
        self.draw_city()
        self.draw_neon_grid()
        self.draw_rain()

        for duck in self.ducks:
            duck.draw()

        for p in self.particles:
            p.draw()

        self.draw_crosshair()
        self.draw_hud()

        pygame.display.flip()

    def run(self):
        pygame.mouse.set_visible(False)
        running = True
        while running:
            running = self.handle_input()
            self.update()
            self.render()
            self.clock.tick(60)
        pygame.mouse.set_visible(True)
        pygame.quit()


game = Game()
game.run()

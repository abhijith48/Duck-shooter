import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random
import struct
import ctypes

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

# --- Fog ---
glEnable(GL_FOG)
glFogi(GL_FOG_MODE, GL_EXP2)
glFogfv(GL_FOG_COLOR, [0.02, 0.01, 0.06, 1.0])
glFogf(GL_FOG_DENSITY, 0.045)

# --- Lighting ---
glEnable(GL_LIGHTING)
glEnable(GL_COLOR_MATERIAL)
glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
glEnable(GL_NORMALIZE)
glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.12, 0.08, 0.15, 1.0])

# Light 0: dim overhead moonlight
glEnable(GL_LIGHT0)
glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.3, 0.3, 0.45, 1.0])
glLightfv(GL_LIGHT0, GL_SPECULAR, [0.15, 0.15, 0.25, 1.0])

# Light 1: neon pink point light
glEnable(GL_LIGHT1)
glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.9, 0.1, 0.5, 1.0])
glLightfv(GL_LIGHT1, GL_SPECULAR, [0.6, 0.05, 0.3, 1.0])
glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION, 0.04)

# Light 2: neon cyan point light
glEnable(GL_LIGHT2)
glLightfv(GL_LIGHT2, GL_DIFFUSE, [0.05, 0.7, 0.6, 1.0])
glLightfv(GL_LIGHT2, GL_SPECULAR, [0.0, 0.45, 0.35, 1.0])
glLightf(GL_LIGHT2, GL_QUADRATIC_ATTENUATION, 0.04)

# Fonts
pygame.font.init()
font_large = pygame.font.SysFont("Courier New", 48, bold=True)
font_medium = pygame.font.SysFont("Courier New", 32, bold=True)
font_small = pygame.font.SysFont("Courier New", 22)
font_tiny = pygame.font.SysFont("Courier New", 16)


# --- Synthwave Music Generator ---

def generate_synthwave_music():
    """Generate dark cyberpunk / darksynth background music."""
    sample_rate = 22050
    TWO_PI = 2 * math.pi

    def saw(phase):
        """Band-limited sawtooth approximation (5 harmonics)."""
        v = 0
        for k in range(1, 6):
            v += ((-1) ** (k + 1)) * math.sin(k * phase) / k
        return v * 0.63

    def pulse(phase, width=0.5):
        """Pulse wave via phase comparison."""
        return 1.0 if (phase % TWO_PI) / TWO_PI < width else -1.0

    # Channel 1: Heavy detuned saw bass (~4 sec loop, Am-F-Dm-E progression)
    bass_dur = 4.0
    n_bass = int(sample_rate * bass_dur)
    bass_samples = []
    # Dark minor progression: A1, F1, D2, E2 (each 1 second)
    bass_notes = [55.0, 43.65, 73.42, 82.41]
    note_len = n_bass // len(bass_notes)
    for i in range(n_bass):
        t = i / sample_rate
        note_idx = min(i // note_len, len(bass_notes) - 1)
        freq = bass_notes[note_idx]
        phase = TWO_PI * freq * t
        # Detuned saw oscillators for thick analog bass
        val = (saw(phase) * 0.25 +
               saw(phase * 1.005) * 0.2 +
               saw(phase * 0.998) * 0.2 +
               math.sin(phase * 0.5) * 0.2)  # sub-bass
        # Sidechain-style pumping envelope (4 pumps per note)
        pump_pos = (i % (note_len // 4)) / (note_len // 4) if note_len > 0 else 0
        pump = min(1.0, pump_pos * 5) * max(0, 1.0 - pump_pos * 0.4)
        # Note envelope
        pos_in_note = (i % note_len) / note_len if note_len > 0 else 0
        env = max(0, 1.0 - pos_in_note * 0.3) * pump
        # Simple low-pass: blend with smoothed version
        fade = int(sample_rate * 0.1)
        if i < fade:
            env *= i / fade
        elif i > n_bass - fade:
            env *= (n_bass - i) / fade
        bass_samples.append(int(val * env * 32767))
    bass_bytes = struct.pack(f"<{len(bass_samples)}h", *bass_samples)
    bass_sound = pygame.mixer.Sound(buffer=bass_bytes)
    bass_sound.set_volume(0.20)

    # Channel 2: Dark arpeggio — minor key, fast 16th-note pattern (~4 sec loop)
    arp_dur = 4.0
    n_arp = int(sample_rate * arp_dur)
    arp_samples = []
    # Am arpeggio pattern with octave jumps (A3-C4-E4-A4-E4-C4 repeated with variation)
    arp_pattern = [
        220.0, 261.63, 329.63, 440.0, 329.63, 261.63, 220.0, 329.63,
        174.61, 220.0, 261.63, 349.23, 261.63, 220.0, 174.61, 261.63,
        146.83, 174.61, 220.0, 293.66, 220.0, 174.61, 146.83, 220.0,
        164.81, 196.0, 246.94, 329.63, 246.94, 196.0, 164.81, 246.94,
    ]
    arp_note_len = n_arp // len(arp_pattern)
    prev_val = 0
    for i in range(n_arp):
        t = i / sample_rate
        note_idx = min(i // arp_note_len, len(arp_pattern) - 1)
        freq = arp_pattern[note_idx]
        phase = TWO_PI * freq * t
        # Pulse wave with modulating width for movement
        pw = 0.3 + 0.15 * math.sin(TWO_PI * 0.5 * t)
        val = pulse(phase, pw) * 0.12 + math.sin(phase) * 0.08
        # Sharp attack, quick decay
        pos = (i % arp_note_len) / arp_note_len if arp_note_len > 0 else 0
        attack = min(1.0, pos * 20)
        decay = max(0, 1.0 - pos * 2.0) if pos > 0.05 else 1.0
        env = attack * decay
        fade = int(sample_rate * 0.08)
        if i < fade:
            env *= i / fade
        elif i > n_arp - fade:
            env *= (n_arp - i) / fade
        raw = val * env
        # Simple one-pole filter for less harsh highs
        filtered = prev_val * 0.3 + raw * 0.7
        prev_val = filtered
        arp_samples.append(int(filtered * 32767))
    arp_bytes = struct.pack(f"<{len(arp_samples)}h", *arp_samples)
    arp_sound = pygame.mixer.Sound(buffer=arp_bytes)
    arp_sound.set_volume(0.09)

    # Channel 3: Dark atmospheric pad — dissonant minor with slow filter sweep (~8 sec)
    pad_dur = 8.0
    n_pad = int(sample_rate * pad_dur)
    pad_samples = []
    # Am9 voicing with slight dissonance
    pad_freqs = [110.0, 130.81, 164.81, 220.0, 246.94, 329.63]
    pad_detune = [0, 0.3, -0.2, 0.5, -0.4, 0.2]
    for i in range(n_pad):
        t = i / sample_rate
        val = 0
        for f, dt in zip(pad_freqs, pad_detune):
            phase = TWO_PI * (f + dt) * t
            # Mix saw and sine for rich texture
            val += (saw(phase) * 0.04 + math.sin(phase) * 0.05)
        # Slow filter sweep via LFO-modulated mix
        lfo = 0.5 + 0.5 * math.sin(TWO_PI * 0.12 * t)
        val *= (0.5 + lfo * 0.5)
        # Stereo-like chorus via slow detune wobble
        chorus = math.sin(TWO_PI * 110.2 * t + math.sin(TWO_PI * 0.3 * t) * 2) * 0.03
        val += chorus
        fade = int(sample_rate * 1.0)
        if i < fade:
            val *= i / fade
        elif i > n_pad - fade:
            val *= (n_pad - i) / fade
        pad_samples.append(int(val * 32767))
    pad_bytes = struct.pack(f"<{len(pad_samples)}h", *pad_samples)
    pad_sound = pygame.mixer.Sound(buffer=pad_bytes)
    pad_sound.set_volume(0.13)

    # Channel 4: Industrial rain/static texture with rhythmic gating (~2 sec)
    rain_dur = 2.0
    n_rain = int(sample_rate * rain_dur)
    rng = random.Random(777)
    raw = [rng.uniform(-1, 1) for _ in range(n_rain)]
    window = 12
    rain_samples = []
    running_sum = sum(raw[:window])
    for i in range(n_rain):
        avg = running_sum / window
        t = i / sample_rate
        # Rhythmic gate — pulsing static at ~8 Hz
        gate = 0.4 + 0.6 * max(0, math.sin(TWO_PI * 8 * t))
        fade_env = 1.0
        fade = int(sample_rate * 0.1)
        if i < fade:
            fade_env = i / fade
        elif i > n_rain - fade:
            fade_env = (n_rain - i) / fade
        rain_samples.append(int(avg * fade_env * gate * 0.1 * 32767))
        new_idx = i + window
        if new_idx < n_rain:
            running_sum += raw[new_idx] - raw[i]
    rain_bytes = struct.pack(f"<{len(rain_samples)}h", *rain_samples)
    rain_sound = pygame.mixer.Sound(buffer=rain_bytes)
    rain_sound.set_volume(0.05)

    return bass_sound, arp_sound, pad_sound, rain_sound


# --- Sound Effects Generator ---

def generate_gunshot():
    sr = 22050
    dur = 0.15
    n = int(sr * dur)
    samples = []
    rng = random.Random(999)
    for i in range(n):
        t = i / sr
        env = max(0, 1.0 - t / dur) ** 3
        noise = rng.uniform(-1, 1)
        thump = math.sin(2 * math.pi * 60 * t * (1 - t * 3))
        val = (noise * 0.5 + thump * 0.5) * env
        samples.append(int(val * 32767 * 0.8))
    data = struct.pack(f"<{len(samples)}h", *samples)
    snd = pygame.mixer.Sound(buffer=data)
    snd.set_volume(0.25)
    return snd


def generate_hit_sound():
    sr = 22050
    dur = 0.2
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        freq = 800 + t * 2000
        env = max(0, 1.0 - t / dur) ** 2
        val = math.sin(2 * math.pi * freq * t) * env * 0.3
        samples.append(int(val * 32767))
    data = struct.pack(f"<{len(samples)}h", *samples)
    snd = pygame.mixer.Sound(buffer=data)
    snd.set_volume(0.20)
    return snd


def generate_quack():
    sr = 22050
    dur = 0.12
    n = int(sr * dur)
    samples = []
    for i in range(n):
        t = i / sr
        freq = 220 + 80 * math.sin(2 * math.pi * 8 * t)
        env = math.sin(math.pi * t / dur)
        val = math.sin(2 * math.pi * freq * t) * env * 0.3
        val += math.sin(2 * math.pi * freq * 2 * t) * env * 0.15
        val += math.sin(2 * math.pi * freq * 3 * t) * env * 0.08
        samples.append(int(val * 32767))
    data = struct.pack(f"<{len(samples)}h", *samples)
    snd = pygame.mixer.Sound(buffer=data)
    snd.set_volume(0.15)
    return snd


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
    glDisable(GL_LIGHTING)
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


# --- Rain ---

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
        if self.y < -0.99:
            pos = (self.x, self.z)
            self.reset()
            return pos
        return None

    def draw(self):
        alpha = 0.15 + 0.1 * (1.0 - abs(self.z + 6) / 6.0)
        glColor4f(0.4, 0.5, 0.9, alpha)
        glBegin(GL_LINES)
        glVertex3f(self.x, self.y, self.z)
        glVertex3f(self.x - 0.01, self.y - self.length, self.z)
        glEnd()


class RainSplash:
    def __init__(self, x, z):
        self.x = x
        self.y = -0.98
        self.z = z
        self.life = 1.0
        self.angle = random.uniform(0, math.pi * 2)

    def update(self):
        self.life -= 0.1

    def draw(self):
        alpha = self.life * 0.3
        spread = (1.0 - self.life) * 0.08
        glColor4f(0.4, 0.6, 1.0, alpha)
        glBegin(GL_LINE_LOOP)
        for i in range(6):
            a = self.angle + i * math.pi / 3
            glVertex3f(self.x + math.cos(a) * spread,
                       self.y,
                       self.z + math.sin(a) * spread)
        glEnd()


# --- Confetti ---

class Confetti:
    """A 2D screen-space confetti piece that falls and spins."""
    def __init__(self):
        self.x = random.uniform(0, display[0])
        self.y = random.uniform(-20, -5)
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(1.5, 4.0)
        self.rot = random.uniform(0, 360)
        self.rot_speed = random.uniform(-8, 8)
        self.size = random.uniform(4, 10)
        self.life = 1.0
        self.decay = random.uniform(0.005, 0.012)
        self.color = random.choice([
            (1.0, 0.08, 0.58),   # pink
            (0.0, 1.0, 0.95),    # cyan
            (1.0, 0.95, 0.0),    # yellow
            (0.7, 0.0, 1.0),     # purple
            (1.0, 0.4, 0.0),     # orange
            (0.2, 1.0, 0.3),     # green
            (1.0, 1.0, 1.0),     # white
        ])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx += random.uniform(-0.3, 0.3)  # flutter
        self.rot += self.rot_speed
        self.life -= self.decay
        if self.y > display[1] + 20:
            self.life = 0

    def draw(self):
        if self.life <= 0:
            return
        r, g, b = self.color
        alpha = self.life * 0.9
        cx, cy = self.x, self.y
        s = self.size
        rad = math.radians(self.rot)
        cos_r, sin_r = math.cos(rad), math.sin(rad)
        # Rotated rectangle (2 triangles as a quad)
        corners = [(-s, -s * 0.4), (s, -s * 0.4), (s, s * 0.4), (-s, s * 0.4)]
        glColor4f(r, g, b, alpha)
        glBegin(GL_QUADS)
        for dx, dy in corners:
            rx = dx * cos_r - dy * sin_r
            ry = dx * sin_r + dy * cos_r
            glVertex2f(cx + rx, cy + ry)
        glEnd()


# --- Duck (classic mallard) ---

class Duck:
    def __init__(self):
        self.quad = gluNewQuadric()
        self.reset()

    def reset(self, speed_mult=1.0):
        self.x = random.uniform(-3, 3)
        self.y = random.uniform(0.5, 2.5)
        self.z = random.uniform(-8, -3)
        base_speed = random.uniform(0.02, 0.06)
        self.vx = random.choice([-1, 1]) * base_speed * speed_mult
        self.vy = random.uniform(-0.01, 0.01) * speed_mult
        self.alive = True
        self.dying = False
        self.death_time = 0
        self.death_vy = 0
        self.death_spin = 0
        self.death_spin_speed = 0
        self.hit_flash = 0
        self.wing_angle = random.uniform(0, math.pi * 2)
        self.bob_phase = random.uniform(0, math.pi * 2)
        self.bank_angle = 0.0
        self.hover_phase = random.uniform(0, math.pi * 2)

    def update(self):
        if not self.alive:
            return

        # Death animation
        if self.dying:
            self.death_time += 1
            self.death_vy -= 0.003
            self.y += self.death_vy
            self.death_spin += self.death_spin_speed
            self.x += self.vx * 0.3
            self.wing_angle += 0.3
            if self.y < -2.0:
                self.alive = False
            return

        self.x += self.vx
        self.y += self.vy

        # Gradual turns near edges instead of hard bounce
        if self.x > 4.0:
            self.vx -= 0.002
        elif self.x < -4.0:
            self.vx += 0.002
        self.vx = max(-0.08, min(0.08, self.vx))

        if self.y > 2.8:
            self.vy -= 0.001
        elif self.y < 0.3:
            self.vy += 0.001
        self.vy = max(-0.03, min(0.03, self.vy))

        if self.hit_flash > 0:
            self.hit_flash -= 1

        # Animation phases
        self.bob_phase += 0.04
        self.hover_phase += 0.025

        # Banking: lean into turns
        target_bank = self.vx * -150
        self.bank_angle += (target_bank - self.bank_angle) * 0.08

        # Variable wing flap speed
        flap_speed = 0.12 + abs(self.vx) * 2.5
        self.wing_angle += flap_speed

    def draw(self, alpha_override=None):
        if not self.alive:
            return
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)

        # Hover oscillation
        hover_offset = math.sin(self.hover_phase) * 0.04
        glTranslatef(0, hover_offset, 0)

        # Banking
        glRotatef(self.bank_angle, 0, 0, 1)

        # Body bob
        bob = math.sin(self.bob_phase) * 0.02
        glTranslatef(0, bob, 0)

        # Death tumble
        if self.dying:
            glRotatef(self.death_spin, 0.3, 1, 0.1)

        # Face direction
        if self.vx < 0:
            glScalef(-1, 1, 1)

        use_alpha = alpha_override is not None

        # --- Body ---
        if self.hit_flash > 0:
            if use_alpha:
                glColor4f(1.0, 0.2, 0.2, alpha_override)
            else:
                glColor3f(1.0, 0.2, 0.2)
        else:
            if use_alpha:
                glColor4f(1.0, 0.85, 0.0, alpha_override)
            else:
                glColor3f(1.0, 0.85, 0.0)
        gluSphere(self.quad, 0.25, 20, 20)

        # --- Head ---
        glPushMatrix()
        glTranslatef(0.2, 0.28, 0.0)
        if self.hit_flash > 0:
            if use_alpha:
                glColor4f(1.0, 0.2, 0.2, alpha_override)
            else:
                glColor3f(1.0, 0.2, 0.2)
        else:
            if use_alpha:
                glColor4f(0.0, 0.55, 0.15, alpha_override)
            else:
                glColor3f(0.0, 0.55, 0.15)
        gluSphere(self.quad, 0.14, 16, 16)

        # Beak
        glPushMatrix()
        glTranslatef(0.13, 0.0, 0.0)
        glRotatef(90, 0, 1, 0)
        if use_alpha:
            glColor4f(1.0, 0.5, 0.0, alpha_override)
        else:
            glColor3f(1.0, 0.5, 0.0)
        gluCylinder(self.quad, 0.04, 0.02, 0.12, 8, 4)
        glPopMatrix()

        # Eye
        glPushMatrix()
        glTranslatef(0.08, 0.06, 0.1)
        if use_alpha:
            glColor4f(0.0, 0.0, 0.0, alpha_override)
        else:
            glColor3f(0.0, 0.0, 0.0)
        gluSphere(self.quad, 0.03, 8, 8)
        glPopMatrix()

        # White eye ring
        glPushMatrix()
        glTranslatef(0.075, 0.06, 0.098)
        if use_alpha:
            glColor4f(1.0, 1.0, 1.0, alpha_override)
        else:
            glColor3f(1.0, 1.0, 1.0)
        gluSphere(self.quad, 0.04, 8, 8)
        glPopMatrix()

        glPopMatrix()  # end head

        # --- Wings (animated, snappy cubic motion) ---
        raw_flap = math.sin(self.wing_angle)
        wing_flap = (raw_flap ** 3) * 0.2 if raw_flap >= 0 else -((-raw_flap) ** 3) * 0.2

        for z_off in [0.22, -0.22]:
            glPushMatrix()
            flap_dir = wing_flap if z_off > 0 else -wing_flap
            glTranslatef(-0.05, 0.05 + flap_dir, z_off)
            glScalef(0.5, 0.25, 0.08)
            if self.hit_flash > 0:
                if use_alpha:
                    glColor4f(0.9, 0.2, 0.2, alpha_override)
                else:
                    glColor3f(0.9, 0.2, 0.2)
            else:
                if use_alpha:
                    glColor4f(0.55, 0.35, 0.15, alpha_override)
                else:
                    glColor3f(0.55, 0.35, 0.15)
            gluSphere(self.quad, 0.3, 10, 10)
            glPopMatrix()

        # --- Tail ---
        glPushMatrix()
        glTranslatef(-0.28, 0.1, 0.0)
        glRotatef(-20, 0, 0, 1)
        glScalef(0.3, 0.12, 0.12)
        if use_alpha:
            glColor4f(0.4, 0.25, 0.1, alpha_override)
        else:
            glColor3f(0.4, 0.25, 0.1)
        gluSphere(self.quad, 0.3, 8, 8)
        glPopMatrix()

        glPopMatrix()  # end duck

    def get_screen_pos(self, viewport, modelview, projection):
        win = gluProject(self.x, self.y, self.z, modelview, projection, viewport)
        return win[0], display[1] - win[1]

    def is_hit(self, mouse_x, mouse_y, viewport, modelview, projection):
        if not self.alive or self.dying:
            return False
        sx, sy = self.get_screen_pos(viewport, modelview, projection)
        edge = gluProject(self.x + 0.25, self.y, self.z, modelview, projection, viewport)
        screen_radius = abs(edge[0] - sx) * 2.5
        dist = math.sqrt((mouse_x - sx) ** 2 + (mouse_y - sy) ** 2)
        return dist < max(screen_radius, 20)


# --- Feather Particle ---

_particle_quad = None


class Particle:
    def __init__(self, x, y, z):
        global _particle_quad
        if _particle_quad is None:
            _particle_quad = gluNewQuadric()
        self.x = x
        self.y = y
        self.z = z
        self.vx = random.uniform(-0.07, 0.07)
        self.vy = random.uniform(0.02, 0.1)
        self.vz = random.uniform(-0.03, 0.03)
        self.life = 1.0
        self.color = random.choice([
            (1.0, 0.85, 0.0),
            (0.55, 0.35, 0.15),
            (0.0, 0.55, 0.15),
            (1.0, 0.5, 0.0),
        ])

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
        gluSphere(_particle_quad, 0.035 * self.life, 6, 6)
        glPopMatrix()


# --- Building ---

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
        accent_choices = [NEON_PINK, NEON_CYAN, NEON_PURPLE, NEON_YELLOW, NEON_ORANGE]
        self.accent = accent_choices[rng.randint(0, len(accent_choices) - 1)]
        self.windows = []
        n_floors = max(1, int(self.height / 0.4))
        n_cols = max(1, int(self.width / 0.25))
        for floor in range(n_floors):
            for col in range(n_cols):
                if rng.random() < 0.6:
                    wy = -1.0 + 0.3 + floor * 0.4
                    wx_offset = -self.width / 2 + 0.15 + col * 0.25
                    wc = (0.9, 0.8, 0.3) if rng.random() < 0.7 else (0.2, 0.7, 0.9)
                    brightness = rng.uniform(0.3, 1.0)
                    self.windows.append((wx_offset, wy, wc, brightness))

    def draw(self, frame):
        glPushMatrix()
        glTranslatef(self.x, -1.0, self.z)

        r, g, b = self.base_color
        hw = self.width / 2
        hd = self.depth / 2
        h = self.height

        # AO: base vertices darker (0.4x), top brighter (1.3x)
        def ao_color(base_r, base_g, base_b, is_bottom):
            mult = 0.4 if is_bottom else 1.3
            return (base_r * mult, base_g * mult, base_b * mult)

        glBegin(GL_QUADS)
        # Front face
        glNormal3f(0, 0, 1)
        fr, fg, fb = r * 1.2, g * 1.2, b * 1.2
        cr, cg, cb = ao_color(fr, fg, fb, True)
        glColor3f(cr, cg, cb)
        glVertex3f(-hw, 0, hd)
        glVertex3f(hw, 0, hd)
        cr, cg, cb = ao_color(fr, fg, fb, False)
        glColor3f(cr, cg, cb)
        glVertex3f(hw, h, hd)
        glVertex3f(-hw, h, hd)

        # Right face
        glNormal3f(1, 0, 0)
        fr, fg, fb = r * 0.8, g * 0.8, b * 0.8
        cr, cg, cb = ao_color(fr, fg, fb, True)
        glColor3f(cr, cg, cb)
        glVertex3f(hw, 0, hd)
        glVertex3f(hw, 0, -hd)
        cr, cg, cb = ao_color(fr, fg, fb, False)
        glColor3f(cr, cg, cb)
        glVertex3f(hw, h, -hd)
        glVertex3f(hw, h, hd)

        # Left face
        glNormal3f(-1, 0, 0)
        fr, fg, fb = r * 0.9, g * 0.9, b * 0.9
        cr, cg, cb = ao_color(fr, fg, fb, True)
        glColor3f(cr, cg, cb)
        glVertex3f(-hw, 0, -hd)
        glVertex3f(-hw, 0, hd)
        cr, cg, cb = ao_color(fr, fg, fb, False)
        glColor3f(cr, cg, cb)
        glVertex3f(-hw, h, hd)
        glVertex3f(-hw, h, -hd)

        # Back face
        glNormal3f(0, 0, -1)
        fr, fg, fb = r * 0.6, g * 0.6, b * 0.6
        cr, cg, cb = ao_color(fr, fg, fb, True)
        glColor3f(cr, cg, cb)
        glVertex3f(hw, 0, -hd)
        glVertex3f(-hw, 0, -hd)
        cr, cg, cb = ao_color(fr, fg, fb, False)
        glColor3f(cr, cg, cb)
        glVertex3f(-hw, h, -hd)
        glVertex3f(hw, h, -hd)

        # Top face
        glNormal3f(0, 1, 0)
        glColor3f(r * 0.7, g * 0.7, b * 0.9)
        glVertex3f(-hw, h, -hd)
        glVertex3f(hw, h, -hd)
        glVertex3f(hw, h, hd)
        glVertex3f(-hw, h, hd)
        glEnd()

        # Neon accent strip
        glDisable(GL_LIGHTING)
        ar, ag, ab = self.accent
        pulse = 0.6 + 0.4 * math.sin(frame * 0.03 + self.x)
        glColor4f(ar * pulse, ag * pulse, ab * pulse, 0.9)
        glBegin(GL_QUADS)
        glVertex3f(-hw - 0.02, h, hd + 0.02)
        glVertex3f(hw + 0.02, h, hd + 0.02)
        glVertex3f(hw + 0.02, h + 0.05, hd + 0.02)
        glVertex3f(-hw - 0.02, h + 0.05, hd + 0.02)
        glEnd()

        # Windows (emissive, no lighting)
        glBegin(GL_QUADS)
        for wx, wy, wc, bright in self.windows:
            if wy > h - 0.3:
                continue
            flicker = bright * (0.85 + 0.15 * math.sin(frame * 0.07 + wx * 13.7 + wy * 7.3))
            glColor4f(wc[0] * flicker, wc[1] * flicker, wc[2] * flicker, 0.9)
            ws = 0.08
            glVertex3f(wx - ws, wy + 1.0, hd + 0.01)
            glVertex3f(wx + ws, wy + 1.0, hd + 0.01)
            glVertex3f(wx + ws, wy + 1.0 + 0.15, hd + 0.01)
            glVertex3f(wx - ws, wy + 1.0 + 0.15, hd + 0.01)
        glEnd()
        glEnable(GL_LIGHTING)

        glPopMatrix()


# --- Main Game ---

class Game:
    def __init__(self):
        self.ducks = [Duck() for _ in range(5)]
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

        # Screen shake
        self.shake_timer = 0
        self.shake_intensity = 0.0

        # Muzzle flash
        self.muzzle_flash_timer = 0

        # Combo system
        self.combo = 0
        self.combo_timer = 0
        self.combo_display_timer = 0
        self.last_combo_text = ""

        # Rain + splashes
        self.rain = [RainDrop() for _ in range(150)]
        self.rain_splashes = []

        # Confetti
        self.confetti = []
        self.last_confetti_milestone = 0

        # Sound effects
        self.snd_gunshot = generate_gunshot()
        self.snd_hit = generate_hit_sound()
        self.snd_quack = generate_quack()

        # City skyline
        rng = random.Random(42069)
        self.buildings = []
        for i in range(20):
            x = -12 + i * 1.3 + rng.uniform(-0.3, 0.3)
            self.buildings.append(Building(x, rng.uniform(-14, -12), rng))
        for i in range(15):
            x = -10 + i * 1.5 + rng.uniform(-0.4, 0.4)
            self.buildings.append(Building(x, rng.uniform(-11, -9.5), rng))

        # Grid colors
        self.grid_color_1 = NEON_CYAN
        self.grid_color_2 = NEON_PINK

        start_music()

    @property
    def difficulty(self):
        return min(3.0, 1.0 + self.score * 0.05)

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

        # Muzzle flash + screen shake (base)
        self.muzzle_flash_timer = 4
        self.shake_timer = 6
        self.shake_intensity = 0.025

        # Gunshot sound
        pygame.mixer.Channel(5).play(self.snd_gunshot)

        viewport = glGetIntegerv(GL_VIEWPORT)
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)

        mx, my = mouse_pos
        hit_any = False
        for duck in self.ducks:
            if duck.is_hit(mx, my, viewport, modelview, projection):
                # Start death animation
                duck.dying = True
                duck.death_vy = 0.04
                duck.death_spin_speed = random.uniform(5, 12)

                # Combo system
                if self.combo_timer < 90:
                    self.combo += 1
                else:
                    self.combo = 1
                self.combo_timer = 0
                points = self.combo
                self.score += points

                # Confetti on every multiple of 50
                new_milestone = self.score // 50
                if new_milestone > self.last_confetti_milestone:
                    self.last_confetti_milestone = new_milestone
                    for _ in range(60):
                        self.confetti.append(Confetti())

                if self.combo >= 2:
                    self.combo_display_timer = 60
                    self.last_combo_text = f"x{self.combo} COMBO! +{points}"

                hit_any = True

                # Stronger shake on hit
                self.shake_timer = 10
                self.shake_intensity = 0.05

                # Hit sound
                pygame.mixer.Channel(6).play(self.snd_hit)

                # Spawn feather particles
                for _ in range(20):
                    self.particles.append(Particle(duck.x, duck.y, duck.z))
                break

        if not hit_any:
            self.misses += 1
            if self.misses >= self.max_misses:
                self.game_over = True

    def update(self):
        self.frame += 1

        # Combo timer always ticks
        self.combo_timer += 1
        if self.combo_timer > 90:
            self.combo = 0
        if self.combo_display_timer > 0:
            self.combo_display_timer -= 1

        if self.game_over:
            return

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        for duck in self.ducks:
            duck.update()

        # Respawn dead ducks (after death animation completes)
        for i, duck in enumerate(self.ducks):
            if not duck.alive:
                new_duck = Duck()
                new_duck.reset(speed_mult=self.difficulty)
                # Random quack on respawn
                if random.random() < 0.3:
                    pygame.mixer.Channel(7).play(self.snd_quack)
                self.ducks[i] = new_duck

        # Particles
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

        # Rain + splashes
        self.rain_splashes = [s for s in self.rain_splashes if s.life > 0]
        for drop in self.rain:
            result = drop.update()
            if result and len(self.rain_splashes) < 30:
                self.rain_splashes.append(RainSplash(result[0], result[1]))
        for s in self.rain_splashes:
            s.update()

        # Confetti
        self.confetti = [c for c in self.confetti if c.life > 0]
        for c in self.confetti:
            c.update()

    # --- Drawing ---

    def draw_sky(self):
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glBegin(GL_QUADS)
        glColor3f(0.08, 0.04, 0.15)
        glVertex3f(-20, -1.0, -15)
        glVertex3f(20, -1.0, -15)
        glColor3f(0.03, 0.02, 0.08)
        glVertex3f(20, 8.0, -15)
        glVertex3f(-20, 8.0, -15)
        glEnd()

        # Horizon glow
        t = self.frame * 0.01
        glow_r = 0.22 + 0.08 * math.sin(t)
        glow_b = 0.35 + 0.08 * math.sin(t * 0.7)
        glBegin(GL_QUADS)
        glColor4f(glow_r, 0.02, glow_b, 0.8)
        glVertex3f(-20, -1.0, -14.99)
        glVertex3f(20, -1.0, -14.99)
        glColor4f(0, 0, 0, 0)
        glVertex3f(20, 2.0, -14.99)
        glVertex3f(-20, 2.0, -14.99)
        glEnd()
        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)

    def draw_city(self):
        for bldg in self.buildings:
            bldg.draw(self.frame)

    def draw_neon_grid(self):
        glDisable(GL_LIGHTING)
        # Dark ground base
        glBegin(GL_QUADS)
        glColor3f(0.04, 0.04, 0.07)
        glVertex3f(-10, -1.0, -15)
        glVertex3f(10, -1.0, -15)
        glVertex3f(10, -1.0, 2)
        glVertex3f(-10, -1.0, 2)
        glEnd()

        # Grid lines
        grid_spacing = 1.0
        t = self.frame * 0.015
        z_offset = (t * 0.5) % grid_spacing

        for i in range(-15, 3):
            z = i + z_offset
            dist = abs(z + 5) / 10.0
            alpha = max(0, 0.3 - dist * 0.2)
            cr, cg, cb = self.grid_color_1 if i % 2 == 0 else self.grid_color_2
            glColor4f(cr * 0.6, cg * 0.6, cb * 0.6, alpha)
            glBegin(GL_LINES)
            glVertex3f(-10, -0.99, z)
            glVertex3f(10, -0.99, z)
            glEnd()

        for i in range(-10, 11):
            dist = abs(i) / 10.0
            alpha = max(0, 0.25 - dist * 0.15)
            cr, cg, cb = self.grid_color_1
            glColor4f(cr * 0.5, cg * 0.5, cb * 0.5, alpha)
            glBegin(GL_LINES)
            glVertex3f(i, -0.99, -15)
            glVertex3f(i, -0.99, 2)
            glEnd()
        glEnable(GL_LIGHTING)

    def draw_shadows(self):
        """Draw blob shadows under ducks on the ground."""
        glDisable(GL_LIGHTING)
        shadow_quad = self.scenery_quad
        for duck in self.ducks:
            if not duck.alive:
                continue
            height = max(0, duck.y - (-1.0))
            radius = 0.15 + height * 0.06
            alpha = 0.35 * max(0, 1.0 - height / 4.0)
            if alpha <= 0:
                continue
            glPushMatrix()
            glTranslatef(duck.x, -0.98, duck.z)
            glRotatef(90, 1, 0, 0)
            glColor4f(0.0, 0.0, 0.0, alpha)
            gluDisk(shadow_quad, 0, radius, 16, 1)
            glPopMatrix()
        glEnable(GL_LIGHTING)

    def draw_reflections(self):
        """Draw wet street reflections of ducks below the grid."""
        glDisable(GL_LIGHTING)
        # Clip everything above the ground plane
        clip_eq = (ctypes.c_double * 4)(0.0, -1.0, 0.0, -1.0)
        glEnable(GL_CLIP_PLANE0)
        glClipPlane(GL_CLIP_PLANE0, clip_eq)

        glPushMatrix()
        # Mirror across y = -1 plane
        glTranslatef(0, -2.0, 0)
        glScalef(1, -1, 1)

        # Flip face culling since we flipped Y
        glFrontFace(GL_CW)

        for duck in self.ducks:
            if duck.alive:
                duck.draw(alpha_override=0.15)

        glFrontFace(GL_CCW)
        glPopMatrix()

        glDisable(GL_CLIP_PLANE0)
        glEnable(GL_LIGHTING)

    def draw_rain(self):
        glDisable(GL_LIGHTING)
        for drop in self.rain:
            drop.draw()
        for splash in self.rain_splashes:
            splash.draw()
        glEnable(GL_LIGHTING)

    def draw_confetti(self):
        if not self.confetti:
            return
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, display[0], display[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)

        for c in self.confetti:
            c.draw()

        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def draw_muzzle_flash(self):
        if self.muzzle_flash_timer <= 0:
            return
        self.muzzle_flash_timer -= 1
        intensity = self.muzzle_flash_timer / 4.0

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, display[0], 0, display[1], -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)

        glBegin(GL_QUADS)
        glColor4f(1.0, 0.9, 0.6, intensity * 0.5)
        glVertex2f(display[0] * 0.3, 0)
        glVertex2f(display[0] * 0.7, 0)
        glColor4f(1.0, 0.7, 0.3, 0.0)
        glVertex2f(display[0] * 0.8, display[1] * 0.25)
        glVertex2f(display[0] * 0.2, display[1] * 0.25)
        glEnd()

        glEnable(GL_DEPTH_TEST)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def draw_hud(self):
        glDisable(GL_LIGHTING)
        # Score
        draw_text_2d(f"SCORE: {self.score:04d}", 22, 22, font_large, (0, 80, 80))
        draw_text_2d(f"SCORE: {self.score:04d}", 20, 20, font_large, (0, 255, 240))

        misses_left = self.max_misses - self.misses
        if misses_left <= 3:
            color = (255, 20, 80)
            shadow = (80, 0, 30)
        else:
            color = (200, 180, 255)
            shadow = (60, 50, 80)
        draw_text_2d(f"Health: {'|' * misses_left}{'.' * self.misses}", 22, 82, font_small, shadow)
        draw_text_2d(f"Health: {'|' * misses_left}{'.' * self.misses}", 20, 80, font_small, color)

        # Difficulty indicator
        diff_text = f"DIFF: {self.difficulty:.1f}x"
        draw_text_2d(diff_text, 20, 110, font_tiny, (150, 100, 50))

        # Bottom bar
        draw_text_2d("[LMB] FIRE  [M] MUTE  [ESC] EXIT", 20, display[1] - 35, font_tiny, (100, 80, 120))

        # Top right
        pulse_alpha = int(128 + 127 * math.sin(self.frame * 0.05))
        draw_text_2d("SYS:ONLINE", display[0] - 165, 20, font_small, (0, pulse_alpha, 0))
        draw_text_2d(f"FRM:{self.frame:06d}", display[0] - 165, 45, font_tiny, (80, 80, 100))

        # Scanline
        if self.frame % 3 == 0:
            scan_y = (self.frame * 2) % display[1]
            draw_text_2d("_" * 100, 0, scan_y, font_tiny, (20, 20, 30))

        # Combo display
        if self.combo_display_timer > 0:
            alpha_val = min(255, self.combo_display_timer * 6)
            if self.combo >= 5:
                combo_color = (255, 0, 255)
            elif self.combo >= 3:
                combo_color = (255, 150, 0)
            else:
                combo_color = (0, 255, 200)
            # Scale alpha into color
            r = int(combo_color[0] * alpha_val / 255)
            g = int(combo_color[1] * alpha_val / 255)
            b = int(combo_color[2] * alpha_val / 255)
            draw_text_2d(self.last_combo_text, display[0] // 2 - 80,
                         display[1] // 2 - 120, font_medium, (r, g, b))

        if self.game_over:
            ox = random.randint(-3, 3) if self.frame % 5 == 0 else 0
            oy = random.randint(-2, 2) if self.frame % 7 == 0 else 0

            draw_text_2d("SYSTEM FAILURE", display[0] // 2 - 190 + ox,
                         display[1] // 2 - 70 + oy, font_large, (255, 0, 60))
            draw_text_2d("SYSTEM FAILURE", display[0] // 2 - 188,
                         display[1] // 2 - 72, font_large, (80, 0, 20))

            draw_text_2d(f"FINAL SCORE: {self.score:04d}", display[0] // 2 - 160,
                         display[1] // 2 + 5, font_medium, (0, 255, 240))
            draw_text_2d("[R] REBOOT SYSTEM", display[0] // 2 - 130,
                         display[1] // 2 + 55, font_small, (180, 180, 200))
        glEnable(GL_LIGHTING)

    def draw_crosshair(self):
        glDisable(GL_LIGHTING)
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
        glVertex2f(mx, my - size)
        glVertex2f(mx, my - gap)
        glVertex2f(mx, my + gap)
        glVertex2f(mx, my + size)
        glVertex2f(mx - size, my)
        glVertex2f(mx - gap, my)
        glVertex2f(mx + gap, my)
        glVertex2f(mx + size, my)
        glEnd()

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
        glEnable(GL_LIGHTING)

    def render(self):
        glClearColor(*DARK_BG, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Screen shake
        shake_x, shake_y = 0, 0
        if self.shake_timer > 0:
            decay = self.shake_timer / 10.0
            shake_x = random.uniform(-1, 1) * self.shake_intensity * decay
            shake_y = random.uniform(-1, 1) * self.shake_intensity * decay
            self.shake_timer -= 1

        gluLookAt(0 + shake_x, 1 + shake_y, 2,
                  0, 1, -5,
                  0, 1, 0)

        # Update pulsing neon light positions
        t = self.frame * 0.03
        pink_pulse = 0.6 + 0.4 * math.sin(t)
        cyan_pulse = 0.6 + 0.4 * math.sin(t * 0.7 + 1.0)
        glLightfv(GL_LIGHT0, GL_POSITION, [0, 10, -5, 0])
        glLightfv(GL_LIGHT1, GL_POSITION, [-3, 1.5, -6, 1])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.9 * pink_pulse, 0.1, 0.5 * pink_pulse, 1.0])
        glLightfv(GL_LIGHT2, GL_POSITION, [3, 2.0, -4, 1])
        glLightfv(GL_LIGHT2, GL_DIFFUSE, [0.05, 0.7 * cyan_pulse, 0.6 * cyan_pulse, 1.0])

        # Draw scene back to front
        self.draw_sky()
        self.draw_city()
        self.draw_neon_grid()
        self.draw_reflections()
        self.draw_shadows()
        self.draw_rain()

        # Ducks (with lighting)
        for duck in self.ducks:
            duck.draw()

        # Particles
        for p in self.particles:
            p.draw()

        # Effects + HUD (no lighting)
        self.draw_muzzle_flash()
        self.draw_confetti()
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

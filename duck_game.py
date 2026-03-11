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
pygame.display.set_caption("Duck Shooter 3D")

# Set up projection matrix correctly
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
glMatrixMode(GL_MODELVIEW)
glEnable(GL_DEPTH_TEST)

# Font for HUD
pygame.font.init()
font_large = pygame.font.SysFont("Arial", 48, bold=True)
font_small = pygame.font.SysFont("Arial", 28)


# --- Procedural Background Music ---

def generate_tone(freq, duration, sample_rate=22050, volume=0.3):
    """Generate a sine wave tone as raw bytes."""
    n_samples = int(sample_rate * duration)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        # Smooth fade in/out to avoid clicks
        envelope = 1.0
        fade = int(sample_rate * 0.05)
        if i < fade:
            envelope = i / fade
        elif i > n_samples - fade:
            envelope = (n_samples - i) / fade
        val = math.sin(2 * math.pi * freq * t) * volume * envelope
        samples.append(int(val * 32767))
    return samples


def generate_ambient_music():
    """Generate layered ambient background music."""
    sample_rate = 22050

    # Channel 1: Ambient pad/drone (~4 seconds loop)
    pad_duration = 4.0
    n_pad = int(sample_rate * pad_duration)
    pad_samples = []
    for i in range(n_pad):
        t = i / sample_rate
        # C3 + G3 fifth interval with slow tremolo
        tremolo = 0.8 + 0.2 * math.sin(2 * math.pi * 0.5 * t)
        val = (math.sin(2 * math.pi * 130.81 * t) * 0.15 +
               math.sin(2 * math.pi * 196.0 * t) * 0.10 +
               math.sin(2 * math.pi * 261.63 * t) * 0.05) * tremolo
        # Smooth loop boundary
        fade = int(sample_rate * 0.3)
        if i < fade:
            val *= i / fade
        elif i > n_pad - fade:
            val *= (n_pad - i) / fade
        pad_samples.append(int(val * 32767))

    pad_bytes = struct.pack(f"<{len(pad_samples)}h", *pad_samples)
    pad_sound = pygame.mixer.Sound(buffer=pad_bytes)
    pad_sound.set_volume(0.15)

    # Channel 2: Bird chirps (~6 seconds loop)
    chirp_duration = 6.0
    n_chirp = int(sample_rate * chirp_duration)
    chirp_samples = [0] * n_chirp
    # Place 4 chirps at random-ish positions
    rng = random.Random(42)  # deterministic
    chirp_times = sorted([rng.uniform(0.3, 5.5) for _ in range(4)])
    for ct in chirp_times:
        start = int(ct * sample_rate)
        chirp_len = int(0.08 * sample_rate)
        base_freq = rng.uniform(1200, 2200)
        for j in range(chirp_len):
            if start + j >= n_chirp:
                break
            t = j / sample_rate
            # Frequency sweep down
            freq = base_freq * (1.0 - 0.4 * (j / chirp_len))
            env = 1.0 - (j / chirp_len)  # decay envelope
            val = math.sin(2 * math.pi * freq * t) * env * 0.25
            chirp_samples[start + j] += int(val * 32767)
    # Clamp
    chirp_samples = [max(-32767, min(32767, s)) for s in chirp_samples]
    chirp_bytes = struct.pack(f"<{len(chirp_samples)}h", *chirp_samples)
    chirp_sound = pygame.mixer.Sound(buffer=chirp_bytes)
    chirp_sound.set_volume(0.12)

    # Channel 3: Wind texture (~3 seconds loop)
    wind_duration = 3.0
    n_wind = int(sample_rate * wind_duration)
    rng2 = random.Random(99)
    raw_noise = [rng2.uniform(-1, 1) for _ in range(n_wind)]
    # Simple moving average low-pass filter
    window = 30
    wind_samples = []
    running_sum = sum(raw_noise[:window])
    for i in range(n_wind):
        avg = running_sum / window
        # Fade at boundaries
        fade = int(sample_rate * 0.2)
        env = 1.0
        if i < fade:
            env = i / fade
        elif i > n_wind - fade:
            env = (n_wind - i) / fade
        wind_samples.append(int(avg * env * 0.15 * 32767))
        # Slide window
        old_idx = i
        new_idx = i + window
        if new_idx < n_wind:
            running_sum += raw_noise[new_idx] - raw_noise[old_idx]

    wind_bytes = struct.pack(f"<{len(wind_samples)}h", *wind_samples)
    wind_sound = pygame.mixer.Sound(buffer=wind_bytes)
    wind_sound.set_volume(0.08)

    return pad_sound, chirp_sound, wind_sound


_music_started = False


def start_music():
    global _music_started
    if _music_started:
        return
    _music_started = True
    pad, chirps, wind = generate_ambient_music()
    # Play on separate channels, looping forever
    ch1 = pygame.mixer.Channel(1)
    ch2 = pygame.mixer.Channel(2)
    ch3 = pygame.mixer.Channel(3)
    ch1.play(pad, loops=-1)
    ch2.play(chirps, loops=-1)
    ch3.play(wind, loops=-1)


def draw_text_2d(text, x, y, font, color=(255, 255, 0)):
    """Render text as a 2D overlay on top of the OpenGL scene."""
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

    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# --- Cloud class ---

class Cloud:
    def __init__(self, quad):
        self.x = random.uniform(-12, 12)
        self.y = random.uniform(4.0, 6.0)
        self.z = random.uniform(-12, -10)
        self.speed = random.uniform(0.003, 0.008)
        self.quad = quad
        # Generate 3-5 blobs with offsets
        n_blobs = random.randint(3, 5)
        self.blobs = []
        for _ in range(n_blobs):
            dx = random.uniform(-0.5, 0.5)
            dy = random.uniform(-0.1, 0.15)
            dz = random.uniform(-0.15, 0.15)
            sx = random.uniform(0.3, 0.6)
            sy = random.uniform(0.15, 0.3)
            sz = random.uniform(0.2, 0.4)
            self.blobs.append((dx, dy, dz, sx, sy, sz))

    def update(self):
        self.x += self.speed
        if self.x > 14:
            self.x = -14

    def draw(self):
        for dx, dy, dz, sx, sy, sz in self.blobs:
            glPushMatrix()
            glTranslatef(self.x + dx, self.y + dy, self.z + dz)
            glScalef(sx, sy, sz)
            glColor3f(0.95, 0.95, 0.98)
            gluSphere(self.quad, 1.0, 10, 10)
            glPopMatrix()


class Duck:
    def __init__(self):
        self.reset()
        self.quad = gluNewQuadric()

    def reset(self):
        self.x = random.uniform(-3, 3)
        self.y = random.uniform(0.5, 2.5)
        self.z = random.uniform(-8, -3)
        self.vx = random.choice([-1, 1]) * random.uniform(0.02, 0.06)
        self.vy = random.uniform(-0.01, 0.01)
        self.alive = True
        self.hit_flash = 0  # frames to flash red when hit
        self.wing_angle = random.uniform(0, math.pi * 2)

    def update(self):
        if not self.alive:
            return
        self.x += self.vx
        self.y += self.vy

        # Bounce off edges
        if self.x > 4.5 or self.x < -4.5:
            self.vx *= -1
        if self.y > 3.0 or self.y < 0.2:
            self.vy *= -1

        if self.hit_flash > 0:
            self.hit_flash -= 1

        # Animate wings
        self.wing_angle += 0.15

    def draw(self):
        if not self.alive:
            return
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)

        # Face direction of movement
        if self.vx < 0:
            glScalef(-1, 1, 1)

        # --- Body ---
        if self.hit_flash > 0:
            glColor3f(1.0, 0.2, 0.2)
        else:
            glColor3f(1.0, 0.85, 0.0)
        gluSphere(self.quad, 0.25, 20, 20)

        # --- Head ---
        glPushMatrix()
        glTranslatef(0.2, 0.28, 0.0)
        if self.hit_flash > 0:
            glColor3f(1.0, 0.2, 0.2)
        else:
            glColor3f(0.0, 0.55, 0.15)  # Green head like a mallard
        gluSphere(self.quad, 0.14, 16, 16)

        # --- Beak ---
        glPushMatrix()
        glTranslatef(0.13, 0.0, 0.0)
        glRotatef(90, 0, 1, 0)
        glColor3f(1.0, 0.5, 0.0)
        gluCylinder(self.quad, 0.04, 0.02, 0.12, 8, 4)
        glPopMatrix()

        # --- Eye ---
        glPushMatrix()
        glTranslatef(0.08, 0.06, 0.1)
        glColor3f(0.0, 0.0, 0.0)
        gluSphere(self.quad, 0.03, 8, 8)
        glPopMatrix()

        # White eye ring
        glPushMatrix()
        glTranslatef(0.075, 0.06, 0.098)
        glColor3f(1.0, 1.0, 1.0)
        gluSphere(self.quad, 0.04, 8, 8)
        glPopMatrix()

        glPopMatrix()  # end head

        # --- Wings (animated) ---
        wing_flap = math.sin(self.wing_angle) * 0.15
        # Left wing
        glPushMatrix()
        glTranslatef(-0.05, 0.05 + wing_flap, 0.22)
        glScalef(0.5, 0.25, 0.08)
        if self.hit_flash > 0:
            glColor3f(0.9, 0.2, 0.2)
        else:
            glColor3f(0.55, 0.35, 0.15)  # Brown wing
        gluSphere(self.quad, 0.3, 10, 10)
        glPopMatrix()
        # Right wing
        glPushMatrix()
        glTranslatef(-0.05, 0.05 + wing_flap, -0.22)
        glScalef(0.5, 0.25, 0.08)
        if self.hit_flash > 0:
            glColor3f(0.9, 0.2, 0.2)
        else:
            glColor3f(0.55, 0.35, 0.15)
        gluSphere(self.quad, 0.3, 10, 10)
        glPopMatrix()

        # --- Tail ---
        glPushMatrix()
        glTranslatef(-0.28, 0.1, 0.0)
        glRotatef(-20, 0, 0, 1)
        glScalef(0.3, 0.12, 0.12)
        glColor3f(0.4, 0.25, 0.1)
        gluSphere(self.quad, 0.3, 8, 8)
        glPopMatrix()

        glPopMatrix()  # end duck

    def get_screen_pos(self, viewport, modelview, projection):
        """Project duck 3D position to 2D screen coords."""
        win = gluProject(self.x, self.y, self.z, modelview, projection, viewport)
        return win[0], display[1] - win[1]  # flip Y

    def is_hit(self, mouse_x, mouse_y, viewport, modelview, projection):
        """Check if mouse click hits this duck using projected screen radius."""
        if not self.alive:
            return False
        sx, sy = self.get_screen_pos(viewport, modelview, projection)
        # Approximate screen radius based on z depth
        # Project a point offset by the duck radius
        edge = gluProject(self.x + 0.25, self.y, self.z, modelview, projection, viewport)
        screen_radius = abs(edge[0] - sx) * 2.5  # a bit generous
        dist = math.sqrt((mouse_x - sx) ** 2 + (mouse_y - sy) ** 2)
        return dist < max(screen_radius, 20)


class Particle:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.vx = random.uniform(-0.05, 0.05)
        self.vy = random.uniform(0.02, 0.08)
        self.vz = random.uniform(-0.02, 0.02)
        self.life = 1.0
        self.quad = gluNewQuadric()
        # Random feather color
        self.color = random.choice([
            (1.0, 0.85, 0.0),   # yellow
            (0.55, 0.35, 0.15), # brown
            (0.0, 0.55, 0.15),  # green
            (1.0, 0.5, 0.0),    # orange
        ])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy -= 0.003  # gravity
        self.life -= 0.04

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        r, g, b = self.color
        glColor3f(r * self.life, g * self.life, b * self.life)
        gluSphere(self.quad, 0.04 * self.life, 6, 6)
        glPopMatrix()


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

        # Shared quadric for scenery
        self.scenery_quad = gluNewQuadric()

        # Generate mountain profiles (two layers)
        rng = random.Random(12345)
        self.mountains_back = []
        x = -12
        while x <= 12:
            y = rng.uniform(2.5, 5.5)
            self.mountains_back.append((x, y))
            x += rng.uniform(0.8, 2.0)
        self.mountains_back.append((12, rng.uniform(2.5, 4.0)))

        rng2 = random.Random(67890)
        self.mountains_front = []
        x = -12
        while x <= 12:
            y = rng2.uniform(1.5, 3.5)
            self.mountains_front.append((x, y))
            x += rng2.uniform(1.0, 2.5)
        self.mountains_front.append((12, rng2.uniform(1.5, 3.0)))

        # Generate trees
        rng3 = random.Random(11111)
        self.trees = []
        for _ in range(8):
            tx = rng3.uniform(-8, 8)
            tz = rng3.uniform(-11, -9)
            height = rng3.uniform(0.8, 1.5)
            canopy_r = rng3.uniform(0.3, 0.5)
            self.trees.append((tx, tz, height, canopy_r))

        # Generate bushes
        self.bushes = []
        for _ in range(6):
            bx = rng3.uniform(-7, 7)
            bz = rng3.uniform(-10, -8.5)
            br = rng3.uniform(0.15, 0.3)
            self.bushes.append((bx, bz, br))

        # Generate patchy ground colors (12x12 grid)
        rng4 = random.Random(22222)
        self.ground_colors = []
        for i in range(12):
            row = []
            for j in range(12):
                g = 0.35 + rng4.uniform(-0.08, 0.08)
                r = 0.12 + rng4.uniform(-0.03, 0.03)
                b = 0.08 + rng4.uniform(-0.03, 0.03)
                row.append((r, g, b))
            self.ground_colors.append(row)

        # Generate clouds
        self.clouds = [Cloud(self.scenery_quad) for _ in range(7)]

        # Start music
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

        self.shoot_cooldown = 5  # short cooldown to prevent spam

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
                # Spawn particles (feathers)
                for _ in range(15):
                    self.particles.append(Particle(duck.x, duck.y, duck.z))
                break  # only hit one duck per shot

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

        # Respawn dead ducks
        for i, duck in enumerate(self.ducks):
            if not duck.alive and duck.hit_flash == 0:
                self.ducks[i] = Duck()

        # Update particles
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

        # Update clouds
        for cloud in self.clouds:
            cloud.update()

    def draw_sky(self):
        """Draw gradient sky background."""
        glBegin(GL_QUADS)
        # Bottom of sky: warm light blue
        glColor3f(0.55, 0.75, 0.95)
        glVertex3f(-20, -1.0, -15)
        glVertex3f(20, -1.0, -15)
        # Top of sky: deeper blue
        glColor3f(0.1, 0.25, 0.65)
        glVertex3f(20, 8.0, -15)
        glVertex3f(-20, 8.0, -15)
        glEnd()

    def draw_sun(self):
        """Draw the sun with rays."""
        sun_x, sun_y, sun_z = -4.5, 5.5, -14.8

        # Sun disc
        glBegin(GL_TRIANGLE_FAN)
        glColor3f(1.0, 0.95, 0.6)
        glVertex3f(sun_x, sun_y, sun_z)
        n_segments = 20
        radius = 0.8
        for i in range(n_segments + 1):
            angle = 2 * math.pi * i / n_segments
            glColor3f(1.0, 0.85, 0.4)
            glVertex3f(sun_x + radius * math.cos(angle),
                       sun_y + radius * math.sin(angle), sun_z)
        glEnd()

        # Sun rays
        n_rays = 10
        ray_inner = 0.85
        ray_outer = 1.4
        t = self.frame * 0.01  # slow rotation
        glBegin(GL_TRIANGLES)
        for i in range(n_rays):
            angle = 2 * math.pi * i / n_rays + t
            a1 = angle - 0.08
            a2 = angle + 0.08
            glColor4f(1.0, 0.9, 0.3, 0.6)
            glVertex3f(sun_x + ray_inner * math.cos(a1),
                       sun_y + ray_inner * math.sin(a1), sun_z)
            glVertex3f(sun_x + ray_inner * math.cos(a2),
                       sun_y + ray_inner * math.sin(a2), sun_z)
            glColor4f(1.0, 0.95, 0.5, 0.0)
            glVertex3f(sun_x + ray_outer * math.cos(angle),
                       sun_y + ray_outer * math.sin(angle), sun_z)
        glEnd()

    def draw_mountains(self):
        """Draw two layers of mountain silhouettes."""
        # Back layer - blue-gray, taller
        glBegin(GL_TRIANGLE_STRIP)
        for x, y in self.mountains_back:
            glColor3f(0.3, 0.33, 0.45)
            glVertex3f(x, y, -14.5)
            glColor3f(0.2, 0.25, 0.35)
            glVertex3f(x, -1.0, -14.5)
        glEnd()

        # Front layer - green-gray, shorter
        glBegin(GL_TRIANGLE_STRIP)
        for x, y in self.mountains_front:
            glColor3f(0.2, 0.38, 0.22)
            glVertex3f(x, y, -13.5)
            glColor3f(0.15, 0.3, 0.15)
            glVertex3f(x, -1.0, -13.5)
        glEnd()

    def draw_clouds(self):
        """Draw drifting clouds."""
        for cloud in self.clouds:
            cloud.draw()

    def draw_trees(self):
        """Draw trees and bushes in the background."""
        for tx, tz, height, canopy_r in self.trees:
            # Trunk
            glPushMatrix()
            glTranslatef(tx, -1.0, tz)
            glRotatef(-90, 1, 0, 0)
            glColor3f(0.35, 0.2, 0.08)
            gluCylinder(self.scenery_quad, 0.06, 0.04, height, 8, 2)
            glPopMatrix()

            # Canopy - 2-3 stacked spheres
            for i in range(3):
                glPushMatrix()
                glTranslatef(tx, -1.0 + height + i * canopy_r * 0.5,  tz)
                glScalef(1.0, 0.75, 1.0)
                g = 0.25 + i * 0.08
                glColor3f(0.1, g, 0.08)
                gluSphere(self.scenery_quad, canopy_r * (1.0 - i * 0.15), 10, 10)
                glPopMatrix()

        # Bushes
        for bx, bz, br in self.bushes:
            glPushMatrix()
            glTranslatef(bx, -1.0 + br * 0.5, bz)
            glScalef(1.2, 0.7, 1.0)
            glColor3f(0.12, 0.35, 0.1)
            gluSphere(self.scenery_quad, br, 8, 8)
            glPopMatrix()

    def draw_ground(self):
        """Draw patchy grass ground."""
        grid = 12
        x_start, x_end = -10, 10
        z_start, z_end = -15, 0
        dx = (x_end - x_start) / grid
        dz = (z_end - z_start) / grid

        glBegin(GL_QUADS)
        for i in range(grid):
            for j in range(grid):
                r, g, b = self.ground_colors[i][j]
                glColor3f(r, g, b)
                x0 = x_start + j * dx
                z0 = z_start + i * dz
                glVertex3f(x0, -1.0, z0)
                glVertex3f(x0 + dx, -1.0, z0)
                glVertex3f(x0 + dx, -1.0, z0 + dz)
                glVertex3f(x0, -1.0, z0 + dz)
        glEnd()

    def draw_pond(self):
        """Draw a small reflective pond on the ground."""
        pond_x, pond_z = 2.5, -6.0
        n_seg = 20
        # Animated subtle color shift
        t = self.frame * 0.02
        blue_shift = 0.55 + 0.05 * math.sin(t)

        glBegin(GL_TRIANGLE_FAN)
        glColor3f(0.15, 0.3, blue_shift)
        glVertex3f(pond_x, -0.99, pond_z)
        for i in range(n_seg + 1):
            angle = 2 * math.pi * i / n_seg
            glColor3f(0.1, 0.25, blue_shift - 0.05)
            glVertex3f(pond_x + 0.8 * math.cos(angle),
                       -0.99,
                       pond_z + 0.5 * math.sin(angle))
        glEnd()

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Camera: slightly above ground looking forward
        gluLookAt(0, 1, 2,   # eye
                  0, 1, -5,  # center
                  0, 1, 0)   # up

        # Background (back to front)
        self.draw_sky()
        self.draw_sun()
        self.draw_mountains()
        self.draw_clouds()
        self.draw_trees()
        self.draw_ground()
        self.draw_pond()

        # Game objects
        for duck in self.ducks:
            duck.draw()

        for p in self.particles:
            p.draw()

        # --- HUD ---
        draw_text_2d(f"Score: {self.score}", 20, 20, font_large, (255, 230, 0))
        misses_left = self.max_misses - self.misses
        color = (255, 80, 80) if misses_left <= 3 else (200, 200, 200)
        draw_text_2d(f"Misses left: {misses_left}", 20, 80, font_small, color)
        draw_text_2d("Click to shoot | M: mute", display[0] - 310, 20, font_small, (180, 220, 255))

        if self.game_over:
            draw_text_2d("GAME OVER", display[0] // 2 - 160, display[1] // 2 - 60, font_large, (255, 60, 60))
            draw_text_2d(f"Final Score: {self.score}", display[0] // 2 - 110, display[1] // 2 + 10, font_small, (255, 230, 0))
            draw_text_2d("Press R to restart", display[0] // 2 - 120, display[1] // 2 + 50, font_small, (200, 200, 200))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_input()
            self.update()
            self.render()
            self.clock.tick(60)
        pygame.quit()


game = Game()
game.run()

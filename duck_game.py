import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random

# Initialize Pygame
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

    def draw(self):
        if not self.alive:
            return
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)

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
            glColor3f(1.0, 0.85, 0.0)
        gluSphere(self.quad, 0.14, 16, 16)

        # --- Beak ---
        glPushMatrix()
        glTranslatef(0.13, 0.0, 0.0)
        glRotatef(90, 0, 1, 0)
        glColor3f(1.0, 0.5, 0.0)
        gluCylinder(self.quad, 0.04, 0.02, 0.1, 8, 4)
        glPopMatrix()

        # --- Eye ---
        glPushMatrix()
        glTranslatef(0.08, 0.06, 0.1)
        glColor3f(0.0, 0.0, 0.0)
        gluSphere(self.quad, 0.03, 8, 8)
        glPopMatrix()

        glPopMatrix()  # end head

        # --- Wing ---
        glPushMatrix()
        glTranslatef(0.0, 0.05, 0.22)
        glScalef(0.5, 0.25, 0.08)
        glColor3f(0.9, 0.7, 0.0)
        gluSphere(self.quad, 0.3, 10, 10)
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

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy -= 0.003  # gravity
        self.life -= 0.05

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glColor3f(1.0, self.life * 0.8, 0.0)
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

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self.__init__()
                if event.key == pygame.K_ESCAPE:
                    return False
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
                # Spawn particles
                for _ in range(12):
                    self.particles.append(Particle(duck.x, duck.y, duck.z))
                break  # only hit one duck per shot

        if not hit_any:
            self.misses += 1
            if self.misses >= self.max_misses:
                self.game_over = True

    def update(self):
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

    def draw_ground(self):
        glBegin(GL_QUADS)
        glColor3f(0.15, 0.45, 0.15)
        glVertex3f(-10, -1.0, -15)
        glVertex3f(10, -1.0, -15)
        glVertex3f(10, -1.0, 0)
        glVertex3f(-10, -1.0, 0)
        glEnd()

    def draw_sky(self):
        glBegin(GL_QUADS)
        glColor3f(0.2, 0.5, 0.9)
        glVertex3f(-20, -1.0, -15)
        glVertex3f(20, -1.0, -15)
        glColor3f(0.05, 0.15, 0.55)
        glVertex3f(20, 8.0, -15)
        glVertex3f(-20, 8.0, -15)
        glEnd()

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Camera: slightly above ground looking forward
        gluLookAt(0, 1, 2,   # eye
                  0, 1, -5,  # center
                  0, 1, 0)   # up

        self.draw_sky()
        self.draw_ground()

        for duck in self.ducks:
            duck.draw()

        for p in self.particles:
            p.draw()

        # --- HUD ---
        draw_text_2d(f"Score: {self.score}", 20, 20, font_large, (255, 230, 0))
        misses_left = self.max_misses - self.misses
        color = (255, 80, 80) if misses_left <= 3 else (200, 200, 200)
        draw_text_2d(f"Misses left: {misses_left}", 20, 80, font_small, color)
        draw_text_2d("Click to shoot!", display[0] - 220, 20, font_small, (180, 220, 255))

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
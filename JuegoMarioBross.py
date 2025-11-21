import pygame
import threading
import time
import random
import queue

# -----------------------
# Inicialización básica
# -----------------------
pygame.init()

# Pantalla
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mario Bros con Hilos - Mejorado")
clock = pygame.time.Clock()

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 30, 30)
GREEN = (30, 200, 30)
BROWN = (139, 69, 19)
GOLD = (255, 215, 0)
YELLOW = (255, 204, 0)
POWER_COLOR = (255, 100, 0)
BLUE = (50, 120, 255)

# -----------------------
# Mundo / Cámara
# -----------------------
camera_x = 0
CAMERA_SPEED = 4
WORLD_WIDTH = 3000  # ancho del mundo (puedes aumentarlo)

# -----------------------
# Hilos y sincronización
# -----------------------
player_mutex = threading.Lock()
enemy_mutex = threading.Lock()
coin_mutex = threading.Lock()
block_mutex = threading.Lock()
powerup_mutex = threading.Lock()

enemy_semaphore = threading.Semaphore(3)
event_queue = queue.Queue()

# -----------------------
# Variables compartidas
# Usamos coordenadas del mundo (no de pantalla)
# -----------------------
shared_player_position = [50, 500]  # [x_world, y_world]
shared_player_velocity = [0, 0]
shared_player_score = 0
shared_player_lives = 3

shared_enemies = []
shared_coins = []
shared_platforms = []
shared_blocks = []
shared_powerups = []

game_running = True
sentiment_analysis_active = True

# -----------------------
# CLASES DEL JUEGO
# -----------------------
class Platform:
    def __init__(self, x, y, width):
        self.x = x
        self.y = y
        self.width = width
        self.height = 20
        self.color = BROWN

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x - camera_x, self.y, self.width, self.height))


class Block:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 40
        self.color = YELLOW
        self.used = False
        self.bump_offset = 0
        self.bump_direction = 1

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x - camera_x, self.y + self.bump_offset, self.size, self.size))

    def update(self):
        if self.bump_offset != 0:
            self.bump_offset += self.bump_direction * 2
            if self.bump_offset > 8:
                self.bump_direction = -1
            if self.bump_offset <= 0:
                self.bump_offset = 0
                self.bump_direction = 1

    def hit(self):
        if not self.used:
            self.used = True
            self.bump_offset = 1
            return True
        return False


class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.radius = self.width // 2
        self.color = GOLD
        self.collected = False

    def draw(self):
        if not self.collected:
            pygame.draw.circle(screen, self.color, (int(self.x - camera_x + self.radius), int(self.y + self.radius)), self.radius)

    def check_collision(self):
        if self.collected:
            return False
        with player_mutex:
            player_rect = pygame.Rect(shared_player_position[0], shared_player_position[1], 40, 60)
        coin_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if player_rect.colliderect(coin_rect):
            self.collected = True
            return True
        return False


class PowerUp:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.color = POWER_COLOR
        self.speed = 2
        self.collected = False

    def draw(self):
        if not self.collected:
            pygame.draw.rect(screen, self.color, (self.x - camera_x, self.y, self.width, self.height))

    def update(self):
        if not self.collected:
            self.x += self.speed
            if self.x <= 0 or self.x >= WORLD_WIDTH - self.width:
                self.speed *= -1

    def check_collision(self):
        if self.collected:
            return False
        with player_mutex:
            player_rect = pygame.Rect(shared_player_position[0], shared_player_position[1], 40, 60)
        power_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if player_rect.colliderect(power_rect):
            self.collected = True
            return True
        return False


class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.color = GREEN
        self.speed = random.randint(1, 2)
        self.direction = random.choice([-1, 1])
        self.active = True

    def draw(self):
        if self.active:
            pygame.draw.rect(screen, self.color, (self.x - camera_x, self.y, self.width, self.height))

    def update(self):
        if not self.active:
            return

        self.x += self.speed * self.direction

        # Cambiar dirección en bordes del mundo
        if self.x <= 0 or self.x >= WORLD_WIDTH - self.width:
            self.direction *= -1

        # Verificar colisión con jugador
        with player_mutex:
            player_rect = pygame.Rect(shared_player_position[0], shared_player_position[1], 40, 60)
        enemy_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        if player_rect.colliderect(enemy_rect):
            event_queue.put(("ENEMY_COLLISION", self))

    def deactivate(self):
        self.active = False


class Player:
    def __init__(self):
        self.width = 40
        self.height = 60
        self.color = RED
        self.velocity_y = 0.0
        self.gravity = 0.7
        self.on_ground = False

    def draw(self):
        # Dibujar en coords de pantalla (world_x - camera_x)
        screen_x = int(shared_player_position[0] - camera_x)
        screen_y = int(shared_player_position[1])
        pygame.draw.rect(screen, self.color, (screen_x, screen_y, self.width, self.height))

    def update(self):
        global camera_x

        with player_mutex:
            # Aplicar gravedad
            self.velocity_y += self.gravity
            shared_player_position[1] += self.velocity_y

            # Rectángulo del jugador (coordenadas del mundo)
            player_rect = pygame.Rect(shared_player_position[0], shared_player_position[1], self.width, self.height)

            # Colisión con plataformas (usar coordenadas del mundo)
            self.on_ground = False
            for platform in shared_platforms:
                platform_rect = pygame.Rect(platform.x, platform.y, platform.width, platform.height)
                if player_rect.colliderect(platform_rect):
                    # Si cae sobre la plataforma
                    if self.velocity_y > 0 and player_rect.bottom >= platform_rect.top:
                        shared_player_position[1] = platform.y - self.height
                        self.velocity_y = 0
                        self.on_ground = True
                        player_rect = pygame.Rect(shared_player_position[0], shared_player_position[1], self.width, self.height)
                    # Si choca por abajo (golpe a bloque desde abajo posible)
                    elif self.velocity_y < 0 and player_rect.top <= platform_rect.bottom:
                        shared_player_position[1] = platform.y + platform.height
                        self.velocity_y = 0
                        player_rect = pygame.Rect(shared_player_position[0], shared_player_position[1], self.width, self.height)

            # Colisión con bloques (golpe por abajo)
            for block in shared_blocks:
                block_rect = pygame.Rect(block.x, block.y, block.size, block.size)
                if player_rect.colliderect(block_rect):
                    # Si viene subiendo y toca la parte inferior del bloque
                    if self.velocity_y < 0 and player_rect.top <= block_rect.bottom:
                        shared_player_position[1] = block.y + block.size
                        self.velocity_y = 0
                        # Si el bloque se activa, empujar evento para generar power-up/moneda
                        if block.hit():
                            event_queue.put(("BLOCK_HIT", block))
                        player_rect = pygame.Rect(shared_player_position[0], shared_player_position[1], self.width, self.height)

            # Límites verticales del mundo
            if shared_player_position[1] > SCREEN_HEIGHT - self.height:
                shared_player_position[1] = SCREEN_HEIGHT - self.height
                self.velocity_y = 0
                self.on_ground = True

            # Limites horizontales en world coords
            if shared_player_position[0] < 0:
                shared_player_position[0] = 0
            if shared_player_position[0] > WORLD_WIDTH - self.width:
                shared_player_position[0] = WORLD_WIDTH - self.width

            # Scroll lateral: ajustar camera_x basado en posición del jugador en pantalla
            screen_player_x = shared_player_position[0] - camera_x
            left_border = SCREEN_WIDTH * 0.4
            right_border = SCREEN_WIDTH * 0.6

            if screen_player_x > right_border:
                # mover camara a la derecha
                camera_x += screen_player_x - right_border
            elif screen_player_x < left_border:
                camera_x -= left_border - screen_player_x

            # Clamp camera dentro de mundo
            if camera_x < 0:
                camera_x = 0
            if camera_x > WORLD_WIDTH - SCREEN_WIDTH:
                camera_x = WORLD_WIDTH - SCREEN_WIDTH

    def jump(self):
        if self.on_ground:
            self.velocity_y = -12
            self.on_ground = False

# -----------------------
# HILOS DEL SISTEMA (mejorados)
# -----------------------
def enemy_manager():
    global shared_enemies
    while game_running:
        try:
            if enemy_semaphore.acquire(blocking=False):
                with enemy_mutex:
                    active_count = len([e for e in shared_enemies if e.active])
                    if active_count < 3:
                        new_enemy = Enemy(random.randint(int(camera_x)+50, int(camera_x)+SCREEN_WIDTH-50),
                                          random.randint(100, SCREEN_HEIGHT-100))
                        # asegurar en rango world
                        new_enemy.x = max(0, min(new_enemy.x, WORLD_WIDTH - new_enemy.width))
                        shared_enemies.append(new_enemy)
                    else:
                        enemy_semaphore.release()

            # Actualizar enemigos
            with enemy_mutex:
                for enemy in shared_enemies[:]:
                    enemy.update()
                    if not enemy.active:
                        shared_enemies.remove(enemy)
                        enemy_semaphore.release()

            time.sleep(0.12)
        except Exception as e:
            print(f"Error en enemy_manager: {e}")

def coin_manager():
    global shared_coins, shared_player_score
    while game_running:
        try:
            with coin_mutex:
                # Generar monedas si hay menos de 10 en el mundo
                if len([c for c in shared_coins if not c.collected]) < 8:
                    new_coin = Coin(random.randint(50, WORLD_WIDTH-50),
                                    random.randint(50, SCREEN_HEIGHT-100))
                    shared_coins.append(new_coin)

                for coin in shared_coins:
                    if coin.check_collision():
                        with player_mutex:
                            shared_player_score += 10
                        event_queue.put(("COIN_COLLECTED", coin))
            time.sleep(0.06)
        except Exception as e:
            print(f"Error en coin_manager: {e}")

def sentiment_analyzer():
    sentiment_words = {
        "positive": ["¡Genial!", "¡Excelente!"],
        "negative": ["¡Cuidado!", "¡Atención!"],
        "neutral": ["Jugando...", "Continuando..."]
    }
    while sentiment_analysis_active and game_running:
        try:
            with player_mutex:
                score = shared_player_score
                lives = shared_player_lives
            if score > 0 and score % 50 == 0:
                sentiment = random.choice(sentiment_words["positive"])
            elif lives < 2:
                sentiment = random.choice(sentiment_words["negative"])
            else:
                sentiment = random.choice(sentiment_words["neutral"])
            event_queue.put(("SENTIMENT_UPDATE", sentiment))
            time.sleep(3)
        except Exception as e:
            print(f"Error en sentiment_analyzer: {e}")

def event_processor():
    global shared_player_lives, shared_player_score, shared_powerups
    while game_running:
        try:
            if not event_queue.empty():
                event_type, data = event_queue.get()

                if event_type == "ENEMY_COLLISION":
                    with player_mutex:
                        shared_player_lives -= 1
                    data.deactivate()
                    print(f"¡Colisión con enemigo! Vidas: {shared_player_lives}")

                elif event_type == "COIN_COLLECTED":
                    print(f"¡Moneda recolectada! Pts: {shared_player_score}")

                elif event_type == "SENTIMENT_UPDATE":
                    print(f"Análisis de sentimiento: {data}")

                elif event_type == "BLOCK_HIT":
                    block = data
                    # Generar power-up encima del bloque (coordenadas del mundo)
                    new_power = PowerUp(block.x, block.y - 40)
                    with powerup_mutex:
                        shared_powerups.append(new_power)
                    print("Power-up generado por golpe a bloque!")

            time.sleep(0.01)
        except Exception as e:
            print(f"Error en event_processor: {e}")

# -----------------------
# Inicializar elementos del mundo
# -----------------------
def initialize_game():
    global shared_platforms, shared_blocks, shared_coins, shared_powerups

    # Plataformas (distribuidas en el mundo)
    shared_platforms = [
        Platform(0, 550, 800),
        Platform(900, 500, 300),
        Platform(1400, 450, 200),
        Platform(1800, 400, 300),
        Platform(2300, 450, 400)
    ]

    # Bloques tipo Mario distribuidos por el mundo
    shared_blocks = [
        Block(300, 300),
        Block(340, 300),
        Block(380, 300),
        Block(1200, 300),
        Block(1600, 320)
    ]

    # Listas iniciales
    shared_coins = []
    shared_enemies = []
    shared_powerups = []

    # Hilos (daemon para que terminen al cerrar)
    threading.Thread(target=enemy_manager, daemon=True).start()
    threading.Thread(target=coin_manager, daemon=True).start()
    threading.Thread(target=sentiment_analyzer, daemon=True).start()
    threading.Thread(target=event_processor, daemon=True).start()

# -----------------------
# BUCLE PRINCIPAL
# -----------------------
def main():
    global game_running, sentiment_analysis_active, shared_player_lives

    player = Player()
    initialize_game()

    font = pygame.font.SysFont('Arial', 24)

    # Variables para power-up temporal (por ejemplo efecto de tamaño)
    powerup_active = False
    powerup_timer = 0
    powerup_duration = 10.0  # segundos

    while game_running:
        # Manejar eventos pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.jump()

        # Movimiento horizontal (entrada)
        keys = pygame.key.get_pressed()
        with player_mutex:
            if keys[pygame.K_LEFT]:
                shared_player_position[0] -= 5
                if shared_player_position[0] < 0:
                    shared_player_position[0] = 0
            if keys[pygame.K_RIGHT]:
                shared_player_position[0] += 5
                if shared_player_position[0] > WORLD_WIDTH - player.width:
                    shared_player_position[0] = WORLD_WIDTH - player.width

        # Actualizar jugador (incluye cámara)
        player.update()

        # Actualizar bloques
        with block_mutex:
            for b in shared_blocks:
                b.update()

        # Actualizar enemigos y monedas (dibujado y actualizaciones en bucle principal para sincronía visual)
        with enemy_mutex:
            for e in shared_enemies:
                e.update()

        with coin_mutex:
            for c in shared_coins:
                # no hace 'update' visual, solo chequeo de colisión en hilo coin_manager
                pass

        # Actualizar power-ups y chequear colisiones
        with powerup_mutex:
            for p in shared_powerups[:]:
                p.update()
                if p.check_collision():
                    # aplicar efecto power-up: +1 vida y tamaño temporal
                    with player_mutex:
                        shared_player_lives += 1
                    powerup_active = True
                    powerup_timer = time.time()
                    # marcar eliminado visualmente (PowerUp.check_collision lo marca)
                    print("Power-up recogido! Vidas:", shared_player_lives)

        # Manejar expiración del power-up (si aplica)
        if powerup_active and (time.time() - powerup_timer) > powerup_duration:
            powerup_active = False
            print("Power-up expirado")

        # Comprobar fin del juego por vidas
        with player_mutex:
            if shared_player_lives <= 0:
                game_running = False

        # ----------------- DIBUJO -----------------
        screen.fill(BLACK)

        # Dibujar plataformas
        for platform in shared_platforms:
            platform.draw()

        # Dibujar bloques
        with block_mutex:
            for block in shared_blocks:
                block.draw()

        # Dibujar monedas
        with coin_mutex:
            for coin in shared_coins:
                coin.draw()

        # Dibujar power-ups
        with powerup_mutex:
            for p in shared_powerups:
                p.draw()

        # Dibujar enemigos
        with enemy_mutex:
            for enemy in shared_enemies:
                enemy.draw()

        # Dibujar jugador (en pantalla; el player.draw usa camera_x internamente)
        player.draw()

        # HUD (puntaje, vidas, hilos activos, cámara)
        with player_mutex:
            score_text = font.render(f"Puntuación: {shared_player_score}", True, WHITE)
            lives_text = font.render(f"Vidas: {shared_player_lives}", True, WHITE)

        thread_info = font.render(f"Hilos activos: {threading.active_count()}", True, WHITE)
        camera_info = font.render(f"Cámara X: {int(camera_x)}", True, WHITE)

        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (10, 40))
        screen.blit(thread_info, (10, 70))
        screen.blit(camera_info, (10, 100))

        pygame.display.flip()
        clock.tick(FPS)

    sentiment_analysis_active = False
    pygame.quit()

if __name__ == "__main__":
    main()

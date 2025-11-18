import pygame
import random
import sys
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple

# Initialisation de Pygame
pygame.init()

# Configuration de la fenêtre
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulation d'Intersection avec Feux Tricolores et Dépassements")
clock = pygame.time.Clock()
FPS = 60

# Couleurs
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
DARK_RED = (150, 0, 0)
DARK_YELLOW = (150, 150, 0)
DARK_GREEN = (0, 150, 0)
BLUE = (0, 0, 255)
COLORS = [
    (0, 0, 255),  # blue
    (255, 0, 0),  # red
    (0, 255, 0),  # green
    (128, 0, 128),  # purple
    (255, 165, 0),  # orange
    (165, 42, 42),  # brown
    (255, 192, 203)  # pink
]


class TrafficLightState(Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


@dataclass
class Car:
    def __init__(self, x, y, direction, speed, color, lane=0):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.color = color
        self.lane = lane
        self.stopped = False
        self.overtaking = False
        self.overtaking_timer = 0
        self.changing_lane = False
        # Ajout des dimensions de la voiture
        self.width = 20  # Largeur de la voiture
        self.length = 40  # Longueur de la voiture

    def move(self):
        if not self.stopped:
            speed = self.speed * (0.8 if self.overtaking else 1.0)  # Ralentit légèrement en dépassement

            if self.direction == Direction.NORTH:
                self.y -= speed
            elif self.direction == Direction.SOUTH:
                self.y += speed
            elif self.direction == Direction.EAST:
                self.x += speed
            elif self.direction == Direction.WEST:
                self.x -= speed

        if self.overtaking:
            self.overtaking_timer += 1
            if self.overtaking_timer > 120:  # 2 secondes de dépassement
                self.overtaking = False
                self.lane = 0
                self.overtaking_timer = 0

    def draw(self, screen):
        # Décalage selon la voie
        offset = 15 if self.lane == 1 else 0

        if self.direction in [Direction.NORTH, Direction.SOUTH]:
            # Voiture verticale
            rect = pygame.Rect(self.x - self.width / 2 + offset, self.y - self.length / 2, self.width, self.length)
            # Distance de sécurité arrière
            safety_rect = pygame.Rect(
                self.x - self.width / 2 + offset,
                self.y + self.length / 2,  # Position juste après la voiture
                self.width,
                5  # 5px de distance de sécurité
            )
        else:
            # Voiture horizontale
            rect = pygame.Rect(self.x - self.length / 2, self.y - self.width / 2 + offset, self.length, self.width)
            # Distance de sécurité arrière
            safety_rect = pygame.Rect(
                self.x - self.length / 2 - 5,  # Position juste avant la voiture
                self.y - self.width / 2 + offset,
                5,  # 5px de distance de sécurité
                self.width
            )

        # Dessiner la voiture
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, BLACK, rect, 1)  # Bordure noire

        # Dessiner la zone de sécurité arrière
        pygame.draw.rect(screen, (255, 0, 0, 128), safety_rect)  # Rouge semi-transparent

        # Dessiner un indicateur si la voiture est en train de dépasser
        if self.overtaking:
            pygame.draw.circle(screen, YELLOW, (int(rect.centerx), int(rect.centery)), 3)


class TrafficLight:
    def __init__(self, x: float, y: float, direction: Direction):
        self.x = x
        self.y = y
        self.direction = direction
        self.state = TrafficLightState.RED
        self.timer = 0
        self.red_duration = 180  # 3 secondes à 60 FPS
        self.yellow_duration = 60  # 1 seconde à 60 FPS
        self.green_duration = 240  # 4 secondes à 60 FPS
        self.next_state = None
        
        # Configuration initiale selon l'axe
        if direction in [Direction.EAST, Direction.WEST]:
            self.state = TrafficLightState.GREEN
            self.timer = 0
        else:  # NORTH, SOUTH
            self.state = TrafficLightState.RED
            self.timer = 0

    def update(self):
        self.timer += 1

        # Gestion des transitions avec synchronisation des axes
        if self.state == TrafficLightState.GREEN and self.timer >= self.green_duration:
            self.next_state = TrafficLightState.RED
            self.state = TrafficLightState.YELLOW
            self.timer = 0
        elif self.state == TrafficLightState.YELLOW and self.next_state == TrafficLightState.RED and self.timer >= self.yellow_duration:
            self.state = TrafficLightState.RED
            self.next_state = None
            self.timer = 0

    def force_red(self):
        """Force le feu au rouge pour la synchronisation"""
        if self.state != TrafficLightState.RED:
            self.state = TrafficLightState.RED
            self.timer = 0
            self.next_state = None

    def switch_to_green(self):
        """Change le feu au vert"""
        if self.state == TrafficLightState.RED:
            self.state = TrafficLightState.GREEN
            self.timer = 0
            self.next_state = None

    def draw(self, screen):
        pole_length = 30
        if self.direction == Direction.NORTH:
            pygame.draw.line(screen, BLACK, (self.x, self.y), (self.x, self.y + pole_length), 5)
        elif self.direction == Direction.SOUTH:
            pygame.draw.line(screen, BLACK, (self.x, self.y), (self.x, self.y - pole_length), 5)
        elif self.direction == Direction.EAST:
            pygame.draw.line(screen, BLACK, (self.x, self.y), (self.x - pole_length, self.y), 5)
        elif self.direction == Direction.WEST:
            pygame.draw.line(screen, BLACK, (self.x, self.y), (self.x + pole_length, self.y), 5)

        pygame.draw.rect(screen, BLACK, (self.x - 15, self.y - 30, 30, 60))

        # Rouge
        color = RED if self.state == TrafficLightState.RED else DARK_RED
        pygame.draw.circle(screen, color, (int(self.x), int(self.y - 20)), 8)

        # Jaune
        color = YELLOW if self.state == TrafficLightState.YELLOW else DARK_YELLOW
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 8)

        # Vert
        color = GREEN if self.state == TrafficLightState.GREEN else DARK_GREEN
        pygame.draw.circle(screen, color, (int(self.x), int(self.y + 20)), 8)


class TrafficSimulation:
    def __init__(self):
        self.safety_distance = 5
        self.cars: List[Car] = []
        self.traffic_lights = {
            Direction.NORTH: TrafficLight(WIDTH // 2 - 30, HEIGHT // 2 + 100, Direction.NORTH),
            Direction.SOUTH: TrafficLight(WIDTH // 2 + 30, HEIGHT // 2 - 100, Direction.SOUTH),
            Direction.EAST: TrafficLight(WIDTH // 2 - 100, HEIGHT // 2 - 30, Direction.EAST),
            Direction.WEST: TrafficLight(WIDTH // 2 + 100, HEIGHT // 2 + 30, Direction.WEST)
        }

        self.phase_timer = 0
        self.phase_duration = 300  # 5 secondes pour chaque phase (à 60 FPS)
        self.current_phase = "EW"  # Commence par la phase Est-Ouest
        
        self.spawn_timer = 0
        self.spawn_rate = 90
        self.font = pygame.font.SysFont('Arial', 18)
        self.big_font = pygame.font.SysFont('Arial', 24, bold=True)
        self.debug_mode = False  # Ajout de l'initialisation de debug_mode

    def update_traffic_lights(self):
        self.phase_timer += 1

        # Changement de phase
        if self.phase_timer >= self.phase_duration:
            self.phase_timer = 0
            
            if self.current_phase == "EW":
                # Passage à la phase Nord-Sud
                self.current_phase = "NS"
                # Mettre les feux Est-Ouest au rouge
                self.traffic_lights[Direction.EAST].force_red()
                self.traffic_lights[Direction.WEST].force_red()
                # Après un court délai, mettre les feux Nord-Sud au vert
                self.traffic_lights[Direction.NORTH].switch_to_green()
                self.traffic_lights[Direction.SOUTH].switch_to_green()
            else:
                # Passage à la phase Est-Ouest
                self.current_phase = "EW"
                # Mettre les feux Nord-Sud au rouge
                self.traffic_lights[Direction.NORTH].force_red()
                self.traffic_lights[Direction.SOUTH].force_red()
                # Après un court délai, mettre les feux Est-Ouest au vert
                self.traffic_lights[Direction.EAST].switch_to_green()
                self.traffic_lights[Direction.WEST].switch_to_green()

        # Mise à jour normale des feux
        for light in self.traffic_lights.values():
            light.update()

    def draw_roads(self):
        screen.fill((50, 150, 50))

        road_width = 300  # Largeur totale des routes (2 voies)
        # Route horizontale
        pygame.draw.rect(screen, GRAY, (0, HEIGHT // 2 - road_width // 2, WIDTH, road_width))
        # Route verticale
        pygame.draw.rect(screen, GRAY, (WIDTH // 2 - road_width // 2, 0, road_width, HEIGHT))

        # Lignes de séparation des voies
        line_length = 50
        gap = 20
        # Lignes horizontales
        for x in range(line_length // 2, WIDTH - line_length // 2, line_length + gap):
            pygame.draw.line(screen, WHITE, (x, HEIGHT // 2 - road_width // 4),
                             (x + line_length, HEIGHT // 2 - road_width // 4), 2)
            pygame.draw.line(screen, WHITE, (x, HEIGHT // 2 + road_width // 4),
                             (x + line_length, HEIGHT // 2 + road_width // 4), 2)
        # Lignes verticales
        for y in range(line_length // 2, HEIGHT - line_length // 2, line_length + gap):
            pygame.draw.line(screen, WHITE, (WIDTH // 2 - road_width // 4, y),
                             (WIDTH // 2 - road_width // 4, y + line_length), 2)
            pygame.draw.line(screen, WHITE, (WIDTH // 2 + road_width // 4, y),
                             (WIDTH // 2 + road_width // 4, y + line_length), 2)

        # Ligne centrale jaune
        pygame.draw.line(screen, YELLOW, (0, HEIGHT // 2), (WIDTH, HEIGHT // 2), 3)
        pygame.draw.line(screen, YELLOW, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 3)

        # Bordures des routes
        border_width = 5
        pygame.draw.line(screen, WHITE, (0, HEIGHT // 2 - road_width // 2), (WIDTH, HEIGHT // 2 - road_width // 2),
                         border_width)
        pygame.draw.line(screen, WHITE, (0, HEIGHT // 2 + road_width // 2), (WIDTH, HEIGHT // 2 + road_width // 2),
                         border_width)
        pygame.draw.line(screen, WHITE, (WIDTH // 2 - road_width // 2, 0), (WIDTH // 2 - road_width // 2, HEIGHT),
                         border_width)
        pygame.draw.line(screen, WHITE, (WIDTH // 2 + road_width // 2, 0), (WIDTH // 2 + road_width // 2, HEIGHT),
                         border_width)

    def spawn_car(self):
        direction = random.choice(list(Direction))
        speed = random.uniform(2, 4)
        color = random.choice(COLORS)
        lane = random.choice([0, 1])  # Choisir une voie aléatoirement

        if direction == Direction.NORTH:
            x_pos = WIDTH // 2 - 50 if lane == 0 else WIDTH // 2 - 20
            car = Car(x_pos, HEIGHT + 50, direction, speed, color, lane=lane)
        elif direction == Direction.SOUTH:
            x_pos = WIDTH // 2 + 50 if lane == 0 else WIDTH // 2 + 20
            car = Car(x_pos, -50, direction, speed, color, lane=lane)
        elif direction == Direction.EAST:
            y_pos = HEIGHT // 2 - 50 if lane == 0 else HEIGHT // 2 - 20
            car = Car(-50, y_pos, direction, speed, color, lane=lane)
        elif direction == Direction.WEST:
            y_pos = HEIGHT // 2 + 50 if lane == 0 else HEIGHT // 2 + 20
            car = Car(WIDTH + 50, y_pos, direction, speed, color, lane=lane)

        if not self.check_collision(car):
            self.cars.append(car)

    def check_collision(self, new_car: Car) -> bool:
        for car in self.cars:
            if car.direction != new_car.direction:
                continue

            # Distance entre les voitures (selon l'axe de déplacement)
            if new_car.direction in [Direction.NORTH, Direction.SOUTH]:
                dist = abs(new_car.y - car.y)
            else:
                dist = abs(new_car.x - car.x)

            if dist < self.safety_distance:
                return True
        return False

    def check_overtaking(self, car: Car):
        if car.overtaking or car.lane == 1:  # Déjà en dépassement ou sur la voie de dépassement
            return

        light = self.traffic_lights[car.direction]
        if light.state != TrafficLightState.GREEN:  # Dépassement seulement à feu vert
            return

        # Vérifier les voitures devant
        for other in self.cars:
            if other == car or other.direction != car.direction or other.lane != 0:
                continue

            # Calculer la distance avec la voiture devant
            if car.direction in [Direction.NORTH, Direction.SOUTH]:
                dist = car.y - other.y if car.direction == Direction.NORTH else other.y - car.y
            else:
                dist = other.x - car.x if car.direction == Direction.EAST else car.x - other.x

            if 0 < dist < self.safety_distance * 1.5:  # Voiture trop proche devant
                car.overtaking = True
                car.lane = 1
                car.overtaking_timer = 0
                break

    def should_car_stop(self, car: Car) -> bool:
        light = self.traffic_lights[car.direction]
        stop_distance = 50

        if car.direction == Direction.NORTH:
            approaching = car.y < light.y + stop_distance and car.y > light.y - 20
            return approaching and light.state in [TrafficLightState.RED, TrafficLightState.YELLOW]
        elif car.direction == Direction.SOUTH:
            approaching = car.y > light.y - stop_distance and car.y < light.y + 20
            return approaching and light.state in [TrafficLightState.RED, TrafficLightState.YELLOW]
        elif car.direction == Direction.EAST:
            approaching = car.x < light.x + stop_distance and car.x > light.x - 20
            return approaching and light.state in [TrafficLightState.RED, TrafficLightState.YELLOW]
        elif car.direction == Direction.WEST:
            approaching = car.x > light.x - stop_distance and car.x < light.x + 20
            return approaching and light.state in [TrafficLightState.RED, TrafficLightState.YELLOW]

        return False

    def update(self):
        # Mise à jour des feux de circulation
        self.update_traffic_lights()

        # Le reste du code update reste inchangé
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_rate:
            self.spawn_car()
            self.spawn_timer = 0

        # Mettre à jour les voitures
        for car in self.cars[:]:
            car.stopped = self.should_car_stop(car)

            if not car.stopped and not car.changing_lane:
                self.handle_overtaking(car)

            if not car.stopped:
                car.move()

            if (car.x < -100 or car.x > WIDTH + 100 or 
                car.y < -100 or car.y > HEIGHT + 100):
                self.cars.remove(car)

    def draw_stats(self):
        stats = [
            f"Voitures: {len(self.cars)}",
            f"Distance sécurité: {self.safety_distance}px",
            "",
            "États des feux:"
        ]

        for direction, light in self.traffic_lights.items():
            state_str = light.state.value.upper()
            if light.state == TrafficLightState.YELLOW:
                if light.next_state == TrafficLightState.GREEN:
                    state_str = "JAUNE (→ VERT)"
                else:
                    state_str = "JAUNE (→ ROUGE)"
            stats.append(f"{direction.name}: {state_str}")

        # Dessiner le fond des statistiques
        pygame.draw.rect(screen, (200, 200, 200, 200), (10, 10, 250, 40 + len(stats) * 25))
        pygame.draw.rect(screen, (100, 100, 100), (10, 10, 250, 40 + len(stats) * 25), 2)

        # Dessiner le texte des statistiques
        for i, stat in enumerate(stats):
            if i == 3:  # Titre "États des feux"
                text = self.big_font.render(stat, True, BLACK)
            else:
                text = self.font.render(stat, True, BLACK)
            screen.blit(text, (20, 20 + i * 25))

    def handle_overtaking(self, car: Car):
        if not car.overtaking:
            self.check_overtaking(car)
        else:
            car.overtaking_timer += 1
            if car.overtaking_timer > 60:  # 1 seconde à 60 FPS
                car.overtaking = False
                car.lane = 0  # Retour sur la voie normale
                car.overtaking_timer = 0

    def run(self):
        running = True
        print("🚦 Simulation d'intersection avec dépassements démarrée!")
        print("📊 Statistiques affichées en temps réel")
        print("🚗 Les voitures apparaissent automatiquement")
        print("🛑 Appuyez sur ESC ou fermez la fenêtre pour arrêter")
        print("🔧 Touche D pour activer/désactiver le mode debug")

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_d:
                        self.debug_mode = not self.debug_mode

            self.update()
            self.draw_roads()

            for car in self.cars:
                car.draw(screen)

            for light in self.traffic_lights.values():
                light.draw(screen)

            self.draw_stats()

            # Afficher les distances de sécurité en mode debug
            if self.debug_mode:
                for car in self.cars:
                    if car.direction in [Direction.NORTH, Direction.SOUTH]:
                        pygame.draw.line(screen, (255, 0, 0, 100),
                                         (car.x - 30, car.y - self.safety_distance / 2),
                                         (car.x + 30, car.y - self.safety_distance / 2), 1)
                        pygame.draw.line(screen, (255, 0, 0, 100),
                                         (car.x - 30, car.y + self.safety_distance / 2),
                                         (car.x + 30, car.y + self.safety_distance / 2), 1)
                    else:
                        pygame.draw.line(screen, (255, 0, 0, 100),
                                         (car.x - self.safety_distance / 2, car.y - 30),
                                         (car.x - self.safety_distance / 2, car.y + 30), 1)
                        pygame.draw.line(screen, (255, 0, 0, 100),
                                         (car.x + self.safety_distance / 2, car.y - 30),
                                         (car.x + self.safety_distance / 2, car.y + 30), 1)

            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    simulation = TrafficSimulation()
    simulation.run()
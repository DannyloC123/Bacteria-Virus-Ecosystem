#!/usr/bin/env python3

import sys
import random
import pygame
import math



### Functions

# Collision function
def is_collision(e1, e2):
    dx = e1.x - e2.x
    dy = e1.y - e2.y
    distance = math.sqrt(dx**2 + dy**2)
    
    return distance < (e1.size + e2.size) / 2

# Vision Function
def get_nearest(entity, targets):
    closest = None
    min_dist = float("inf")
    for t in targets:
        dx = entity.x - t.x
        dy = entity.y - t.y
        dist = dx*dx + dy*dy  # no sqrt

        if dist < min_dist:
            min_dist = dist
            closest = t

    return closest

# Normalize function
def normalize(dx, dy, speed=1):
    mag = math.sqrt(dx*dx + dy*dy)
    if mag == 0:
        return 0, 0

    return (dx / mag) * speed, (dy / mag) * speed



# Class for every entity
class Entity:
    def __init__(self, x, y, size, health=1000, speed=1):
        self.x = x
        self.y = y
        self.size = size
        self.health = health
        self.max_health = health
        self.distance_traveled = 0
        self.speed = speed
        self.reproduction_cooldown = random.randint(60, 180)

    def move(self, dx, dy):
        dx *= self.speed
        dy *= self.speed

        self.x += dx
        self.y += dy

        self.x = max(0, min(self.x, 1000))
        self.y = max(0, min(self.y, 800))

        # distance (no sqrt needed)
        self.distance_traveled += dx*dx + dy*dy

        if self.distance_traveled >= 9:
            self.health -= 5
            self.distance_traveled = 0

        # cooldown tick
        if self.reproduction_cooldown > 0:
            self.reproduction_cooldown -= 1


# Class for the agents
class Agent:
    def decide(self, organism, env):
        if isinstance(organism, Bacteria):
            return self.bacteria_behavior(organism, env)
        else:
            return self.virus_behavior(organism, env)

    def bacteria_behavior(self, organism, env):
        nearest_pellet = get_nearest(organism, env["pellets"])
        nearest_virus = get_nearest(organism, env["viruses"])

        # run away from virus
        if nearest_virus:
            dx = organism.x - nearest_virus.x
            dy = organism.y - nearest_virus.y

            if abs(dx) < organism.vision_radius:
                return normalize(dx, dy, 2)

        # go to food
        if nearest_pellet:
            dx = nearest_pellet.x - organism.x
            dy = nearest_pellet.y - organism.y
            return normalize(dx, dy, 1)

        return random.choice([-1,0,1]), random.choice([-1,0,1])

    def virus_behavior(self, organism, env):
        nearest_bacteria = get_nearest(organism, env["bacteria"])

        if nearest_bacteria:
            dx = nearest_bacteria.x - organism.x
            dy = nearest_bacteria.y - organism.y
            return normalize(dx, dy, 1.5)

        return random.choice([-1,0,1]), random.choice([-1,0,1])

# Class for the bacteria (prey)
class Bacteria(Entity):
    def __init__(self, x, y, vision_radius):
        super().__init__(x, y, size=20)
        self.vision_radius = vision_radius
        self.agent = Agent()

    def update(self, env):
        dx, dy = self.agent.decide(self, env)
        self.move(dx, dy)

# Class for the virus (preditor)
class Virus(Entity):
    def __init__(self, x, y, vision_radius):
        super().__init__(x, y, size=40)
        self.vision_radius = vision_radius
        self.agent = Agent()

    def update(self, env):
        dx, dy = self.agent.decide(self, env)
        self.move(dx, dy)

# Class for the food pellet
class Pellet(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, size=6)



def main():
    pygame.init()

    WIDTH, HEIGHT = 1000, 800
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Bacteria vs Virus")

    clock = pygame.time.Clock()

    # images
    virus_img = pygame.image.load("virus.png").convert_alpha()
    virus_img = pygame.transform.scale(virus_img, (40, 40))

    bacteria_img = pygame.image.load("bacteria.png").convert_alpha()
    bacteria_img = pygame.transform.scale(bacteria_img, (20, 20))

    # entities
    bacteria_list = [Bacteria(random.randint(0, WIDTH), random.randint(0, HEIGHT), 100) for _ in range(20)]
    virus_list = [Virus(random.randint(0, WIDTH), random.randint(0, HEIGHT), 100) for _ in range(5)]
    pellet_list = [Pellet(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(30)]

    running = True

    while running:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        env = {
            "bacteria": bacteria_list,
            "viruses": virus_list,
            "pellets": pellet_list
        }

        # update
        for b in bacteria_list:
            b.update(env)

        for v in virus_list:
            v.update(env)

        # bacteria eat pellets
        new_pellets = []
        for p in pellet_list:
            eaten = False
            for b in bacteria_list:
                if is_collision(b, p):
                    b.health += b.max_health / 5
                    b.health = min(b.health, b.max_health)
                    eaten = True
                    break
            if not eaten:
                new_pellets.append(p)
        pellet_list = new_pellets

        # bacteria evolution
        if len(bacteria_list) < 300:
            new_bacteria = []
            for b in bacteria_list:
                if b.health >= b.max_health and b.reproduction_cooldown == 0:
                    b.health = b.max_health / 2
                    b.reproduction_cooldown = 100

                    mutant = Bacteria(b.x, b.y, b.vision_radius)
                    mutant.speed = max(0.5, b.speed + random.uniform(-0.2, 0.2))

                    new_bacteria.append(mutant)

            bacteria_list.extend(new_bacteria)

        # virus evolution
        if len(virus_list) < 150:
            new_viruses = []
            for v in virus_list:
                if v.health >= v.max_health and v.reproduction_cooldown == 0:
                    v.health = v.max_health / 2
                    v.reproduction_cooldown = 100

                    mutant = Virus(v.x, v.y, v.vision_radius)
                    mutant.speed = max(0.5, v.speed + random.uniform(-0.2, 0.2))

                    new_viruses.append(mutant)

            virus_list.extend(new_viruses)

        # remove dead
        bacteria_list = [b for b in bacteria_list if b.health > 0]
        virus_list = [v for v in virus_list if v.health > 0]

        # spawn pellets
        if len(pellet_list) < 100 and random.random() < 0.05:
            pellet_list.append(Pellet(random.randint(0, WIDTH), random.randint(0, HEIGHT)))

        # draw
        screen.fill((0, 102, 102))

        for p in pellet_list:
            pygame.draw.circle(screen, (255, 255, 0), (int(p.x), int(p.y)), p.size)

        for b in bacteria_list:
            screen.blit(bacteria_img, (int(b.x - b.size//2), int(b.y - b.size//2)))

        for v in virus_list:
            screen.blit(virus_img, (int(v.x - v.size//2), int(v.y - v.size//2)))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
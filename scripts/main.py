import pygame
import sys
import random
import math
from visual import SpectrumVisualizer
from AudioAnalyzer import AudioAnalyzer

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # Initialize mixer for sound

# Define constants
WIDTH, HEIGHT = 480, 640
FPS = 60
font_arcade = pygame.font.Font('./fonts/arcade.TTF', 44)

# Create game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TATAKAE")

# Initialize spectrum visualizer
visualizer = SpectrumVisualizer("./music/mywar.wav")

# Initialize audio analyzer
freq_groups = [[30], [70], [100]]  # Define frequency groups (Hz)
audio_analyzer = AudioAnalyzer()
audio_analyzer.load("./music/mywar.wav")
audio_analyzer.precompute(freq_groups, output_file="./precomputed/precomputed_data.npy")

# Add rhythm-based bullet generation
bass_trigger = -30  # Decibel level threshold
last_bass_shot_time = 0
bullet_cooldown = 400  # Minimum time (ms) between bullet bursts

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)


# Load background images
home_bg = pygame.image.load("./images/home_bg.png")
drip_bg = pygame.image.load("./images/mywar_bg.png")

# Load bullet images
player_bullet_img = pygame.image.load("./images/bullet_blue.png")
boss_bullet_img = pygame.image.load("./images/bullet_orange.png")

# Load heart images
heart_filled = pygame.image.load("./images/heart2.png")
heart_empty = pygame.image.load("./images/heart1.png")
heart_size = (40, 40)  # Resize heart images
heart_filled = pygame.transform.scale(heart_filled, heart_size)
heart_empty = pygame.transform.scale(heart_empty, heart_size)


# Load background music for home and game
home_bg_music = "./music/home_bg.wav"
game_bg_music = "./music/mywar.wav"

# Define player
player_size = 20
player_pos = [WIDTH // 2, HEIGHT - player_size * 2]
player_speed = 6
player_velocity = [0, 0]  # Velocity vector

# Define boss animation frames
boss_size = 150
boss_frames = [
    pygame.transform.scale(pygame.image.load(f"./images/boss_frame_{i}.png"), (boss_size, boss_size))
    for i in range(4)  # Assuming 4 frames: boss_frame_0.png to boss_frame_3.png
]
boss_frame_index = 0
boss_frame_timer = 0  # Timer to control frame switching
boss_frame_interval = 200  # Milliseconds between frame switches

boss_pos = [WIDTH // 2 - boss_size // 2, HEIGHT // 4 - boss_size // 2]  # Stationary boss in the middle top
boss_health = 50  # Boss health

# Define bullets
bullet_size = 32
bullet_speed = 10
bullets = []

# Define boss bullets
enemy_bullet_size = 32
enemy_bullet_speed = 5
enemy_bullets = []  # Format: [x, y, dx, dy, start_time]

# Resize bullet images if necessary
player_bullet_img = pygame.transform.scale(player_bullet_img, (bullet_size, bullet_size))
boss_bullet_img = pygame.transform.scale(boss_bullet_img, (enemy_bullet_size, enemy_bullet_size))

# Game score and lives
score = 0
lives = 5  # Initial lives

# Game loop
clock = pygame.time.Clock()

Drop = True


def draw_end_page(message):
    """Draw the end page with a return to home button."""
    screen.fill(BLACK)

    message_text = font_arcade.render(message, True, WHITE)
    button_text = font_arcade.render("Return", True, WHITE)

    # Position text
    message_rect = message_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    button_rect = pygame.Rect(WIDTH // 2 - 125, HEIGHT // 2 - 25, 250, 50)

    # Draw elements
    screen.blit(message_text, message_rect)
    pygame.draw.rect(screen, BLUE, button_rect)
    screen.blit(button_text, button_text.get_rect(center=button_rect.center))

    return button_rect


def draw_start_page():
    """Draw the start page with Start and Quit buttons."""
    home_bg_size = (WIDTH, HEIGHT)
    home_bg_t = pygame.transform.scale(home_bg, home_bg_size)
    screen.blit(home_bg_t, (0, 0))


    title_text = font_arcade.render("TATAKAE!!", True, WHITE)
    start_text = font_arcade.render("Start", True, WHITE)
    quit_text = font_arcade.render("Quit", True, WHITE)

    # Position text
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    start_rect = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2 - 25, 150, 50)
    quit_rect = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2 + 50, 150, 50)

    # Draw elements
    screen.blit(title_text, title_rect)
    pygame.draw.rect(screen, BLUE, start_rect)
    pygame.draw.rect(screen, RED, quit_rect)
    screen.blit(start_text, start_text.get_rect(center=start_rect.center))
    screen.blit(quit_text, quit_text.get_rect(center=quit_rect.center))

    return start_rect, quit_rect


def show_quit_confirmation():
    """Show a confirmation pop-up to ask if the player really wants to quit."""
    popup_width, popup_height = 400, 200
    popup_rect = pygame.Rect((WIDTH - popup_width) // 2, (HEIGHT - popup_height) // 2, popup_width, popup_height)

    yes_rect = pygame.Rect(popup_rect.centerx - 80, popup_rect.bottom - 60, 60, 40)
    no_rect = pygame.Rect(popup_rect.centerx + 20, popup_rect.bottom - 60, 60, 40)

    while True:
        pygame.draw.rect(screen, BLACK, popup_rect)
        pygame.draw.rect(screen, WHITE, popup_rect, 5)  # Border

        message_text = font_arcade.render("Sure ma", True, WHITE)
        yes_text = font_arcade.render("Yes", True, WHITE)
        no_text = font_arcade.render("No", True, WHITE)

        screen.blit(message_text, message_text.get_rect(center=(popup_rect.centerx, popup_rect.centery - 20)))
        pygame.draw.rect(screen, GREEN, yes_rect)
        pygame.draw.rect(screen, RED, no_rect)
        screen.blit(yes_text, yes_text.get_rect(center=yes_rect.center))
        screen.blit(no_text, no_text.get_rect(center=no_rect.center))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if yes_rect.collidepoint(event.pos):  # Quit the game
                    pygame.quit()
                    sys.exit()
                elif no_rect.collidepoint(event.pos):  # Return to start page
                    return


def start_menu():
    """Display the start menu with Start and Quit buttons."""
    pygame.mixer.music.load(home_bg_music)  # Load home background music
    pygame.mixer.music.play(-1)  # Play in a loop

    while True:
        start_button_rect, quit_button_rect = draw_start_page()
        pygame.display.flip()  # Update the display

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button_rect.collidepoint(event.pos):  # If Start button clicked
                    pygame.mixer.music.stop()  # Stop home music
                    pygame.mixer.music.load(game_bg_music)
                    pygame.mixer.music.play(-1)  # Play indefinitely

                    return  # Exit the start menu
                elif quit_button_rect.collidepoint(event.pos):  # If Quit button clicked
                    show_quit_confirmation()  # Show confirmation dialog


# Function to reset the game state
def reset_game():
    global boss_health, lives, score, bullets, enemy_bullets, player_pos, player_velocity
    boss_health = 50
    lives = 5
    score = 0
    bullets = []
    enemy_bullets = []
    player_pos = [WIDTH // 2, HEIGHT - player_size * 2]
    player_velocity = [0, 0]


# Updated end_game() function to ensure return to the home page
def end_game(message):
    """Display the end screen with a Return to Home button."""
    while True:
        return_button_rect = draw_end_page(message)
        pygame.display.flip()  # Update the display

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if return_button_rect.collidepoint(event.pos):  # If Return to Home button clicked
                    start_menu()  # Go back to the home page
                    reset_game()  # Reset the game state for a fresh start
                    return  # Exit the end screen


# Game-related functions
def draw_player():
    pygame.draw.rect(screen, WHITE, (player_pos[0], player_pos[1], player_size, player_size))


def draw_boss():
    global boss_frame_index, boss_frame_timer
    current_time = pygame.time.get_ticks()
    # Update animation frame
    if current_time - boss_frame_timer >= boss_frame_interval:
        boss_frame_index = (boss_frame_index + 1) % len(boss_frames)
        boss_frame_timer = current_time
    # Draw the current frame
    screen.blit(boss_frames[boss_frame_index], (boss_pos[0], boss_pos[1]))

def generate_rhythm_based_bullets():
    global last_bass_shot_time, Drop
    current_time = pygame.time.get_ticks()
    if current_time - last_bass_shot_time > bullet_cooldown:
        bass_drop = audio_analyzer.get_interpolated_decibel(pygame.mixer.music.get_pos() / 1000.0, 0)  # Get bass (75 Hz)
        bass_decibel = audio_analyzer.get_interpolated_decibel(pygame.mixer.music.get_pos() / 1000.0, 1)  # Get bass (75 Hz)
        if bass_drop > bass_trigger:
            Drop = True
            last_bass_shot_time = current_time
            boss_center_x = boss_pos[0] + boss_size // 2
            boss_center_y = boss_pos[1] + boss_size // 2

            # Generate four random unique angles
            # bullet_angle_gap = random.choice([40,30])
            #angles = random.sample(range(0, 360, 30), 6)
            angles = range(0, 360, 12)
            for angle in angles:  # Circular bullet pattern
                radian = math.radians(angle)
                dx = enemy_bullet_speed * math.cos(radian)
                dy = enemy_bullet_speed * math.sin(radian)
                #ax = random.uniform(-0.03, 0.03)  # Random horizontal acceleration (left or right curve)
                #ax = 0.1
                enemy_bullets.append([boss_center_x, boss_center_y, dx, dy, 0, current_time])

        elif bass_decibel > bass_trigger:
            Drop = False
            last_bass_shot_time = current_time
            boss_center_x = boss_pos[0] + boss_size // 2
            boss_center_y = boss_pos[1] + boss_size // 2

            # Generate four random unique angles
            # bullet_angle_gap = random.choice([40,30])
            angles = random.sample(range(0, 360, 30), 6)
            #angles = range(0, 360, 30)
            for angle in angles:  # Circular bullet pattern
                radian = math.radians(angle)
                dx = enemy_bullet_speed * math.cos(radian)
                dy = enemy_bullet_speed * math.sin(radian)
                ax = random.uniform(-0.03, 0.03)  # Random horizontal acceleration (left or right curve)
                #ax = 0.1
                enemy_bullets.append([boss_center_x, boss_center_y, dx, dy, ax, current_time])


def draw_bullets():
    for bullet in bullets:
        screen.blit(player_bullet_img, (bullet[0], bullet[1]))


def draw_enemy_bullets():
    global Drop
    boss_center_x = boss_pos[0] + boss_size / 2
    boss_center_y = boss_pos[1] + boss_size / 2
    for enemy_bullet in enemy_bullets:
        # Calculate the distance from the bullet to the center of the boss
        distance_to_boss = math.sqrt(
            (enemy_bullet[0] - boss_center_x) ** 2 + (enemy_bullet[1] - boss_center_y) ** 2
        )

        # Skip bullets within 20 pixels of the boss's center
        if distance_to_boss <= 100:
            continue

        # Calculate the angle of rotation in degrees
        angle = math.degrees(math.atan2(-enemy_bullet[3], enemy_bullet[2]))  # atan2(y, x)
        # Rotate the bullet image
        '''if Drop:
            rotated_bullet = pygame.transform.rotate(player_bullet_img, angle)
            # Adjust the position to account for rotation offset
            bullet_rect = rotated_bullet.get_rect(center=(enemy_bullet[0], enemy_bullet[1]))
            # Draw the rotated bullet
            screen.blit(rotated_bullet, bullet_rect.topleft)
        else:'''
        rotated_bullet = pygame.transform.rotate(boss_bullet_img, angle)
        # Adjust the position to account for rotation offset
        bullet_rect = rotated_bullet.get_rect(center=(enemy_bullet[0], enemy_bullet[1]))
        # Draw the rotated bullet
        screen.blit(rotated_bullet, bullet_rect.topleft)


def move_bullets():
    for bullet in bullets:
        bullet[1] -= bullet_speed


def move_enemy_bullets():
    current_time = pygame.time.get_ticks()
    for enemy_bullet in enemy_bullets:
        # Check if this bullet should start moving
        if current_time >= enemy_bullet[4]:  # Check start_time
            enemy_bullet[0] += enemy_bullet[2]  # dx
            enemy_bullet[1] += enemy_bullet[3]  # dy

            # Apply horizontal acceleration (ax) to dx
            enemy_bullet[2] += enemy_bullet[4]

            # Apply "gravity-like" effect to dy (optional for more dramatic curve)
            enemy_bullet[3] += 0.05  # Simulate downward acceleration


def check_collision():
    global score, boss_health
    for bullet in bullets:
        if (
            bullet[1] <= boss_pos[1] + boss_size
            and bullet[1] + bullet_size >= boss_pos[1]
            and bullet[0] <= boss_pos[0] + boss_size
            and bullet[0] + bullet_size >= boss_pos[0]
        ):
            bullets.remove(bullet)
            boss_health -= 1
            score += 1


def check_enemy_bullet_collision():
    global lives
    # Define a smaller hit radius for the enemy bullet
    bullet_hit_radius = enemy_bullet_size // 4  # Reduce the hitbox to 1/4th the size

    for enemy_bullet in enemy_bullets:
        # Calculate the distance between the player and the bullet
        dist_x = player_pos[0] + player_size // 2 - enemy_bullet[0]
        dist_y = player_pos[1] + player_size // 2 - enemy_bullet[1]
        distance = math.sqrt(dist_x ** 2 + dist_y ** 2)

        # Check if the player is within the hit radius of the bullet
        if distance <= bullet_hit_radius:
            enemy_bullets.remove(enemy_bullet)
            lives -= 1
            if lives == 0:
                end_game("Game Over!")  # Show the Game Over screen



def draw_lives():
    for i in range(5):
        x_pos = WIDTH - (i + 1) * (heart_size[0] + 5)  # Calculate x-position for hearts
        y_pos = 10  # Fixed y-position
        if i < (5 - lives):  # Empty hearts appear from the rightmost
            screen.blit(heart_empty, (x_pos, y_pos))  # Draw empty hearts
        else:
            screen.blit(heart_filled, (x_pos, y_pos))  # Draw filled hearts


def main():
    # Run the start menu
    start_menu()

    # Main Game Loop
    while True:
        delta_time = clock.tick(FPS) / 1000.0  # Delta time in seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    player_velocity[0] = -player_speed
                elif event.key == pygame.K_RIGHT:
                    player_velocity[0] = player_speed
                elif event.key == pygame.K_UP:
                    player_velocity[1] = -player_speed
                elif event.key == pygame.K_DOWN:
                    player_velocity[1] = player_speed
                elif event.key == pygame.K_SPACE:
                    bullets.append([player_pos[0] + player_size // 2 - bullet_size // 2, player_pos[1]])
            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                    player_velocity[0] = 0
                if event.key in [pygame.K_UP, pygame.K_DOWN]:
                    player_velocity[1] = 0

        

        # Move player
        player_pos[0] += player_velocity[0]
        player_pos[1] += player_velocity[1]

        # Boundary checks for player
        if player_pos[0] < 0:
            player_pos[0] = 0
        elif player_pos[0] + player_size > WIDTH:
            player_pos[0] = WIDTH - player_size
        if player_pos[1] < 0:
            player_pos[1] = 0
        elif player_pos[1] + player_size > HEIGHT:
            player_pos[1] = HEIGHT - player_size

        
        # Rhythm-based bullet generation
        generate_rhythm_based_bullets() 

        
        drip_bg_size = (WIDTH, HEIGHT)
        drip_bg_t = pygame.transform.scale(drip_bg, drip_bg_size)
        screen.blit(drip_bg_t, (0, 0))

        # Render spectrum in the background
        visualizer.update(delta_time)
        visualizer.render(screen)
        # Move bullets
        move_bullets()
        move_enemy_bullets()
        # Check collisions
        check_collision()
        check_enemy_bullet_collision()
        # Draw elements
        draw_player()
        draw_boss()
        draw_bullets()
        draw_enemy_bullets()

        # Show score and lives
        score_text = font_arcade.render(f"HP   {boss_health}", True, BLACK)
        screen.blit(score_text, (10, 10))
        draw_lives()

        # Check boss health
        if boss_health <= 0:
            end_game("You Win!")
        if lives <= 0:
            end_game("Game Over!")

        # Update display
        pygame.display.flip()

        # Control frame rate
        clock.tick(FPS)


if __name__ == "__main__":
    main()


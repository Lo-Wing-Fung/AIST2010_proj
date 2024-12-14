import tkinter
import tkinter.filedialog
import pygame
import sys
import random
import math
import time
import os
import shutil
from natsort import natsorted
from visual import SpectrumVisualizer
from AudioAnalyzer import AudioAnalyzer


# avoid collision (in mac)
top = tkinter.Tk()
top.withdraw()  # hide window

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # Initialize mixer for sound

# Define constants
WIDTH, HEIGHT = 480, 640
FPS = 100
font_arcade = pygame.font.Font('./fonts/arcade_new.TTF', 30)
font_arcade_mid = pygame.font.Font('./fonts/arcade_new.TTF', 20)
font_arcade_small = pygame.font.Font('./fonts/arcade_new.TTF', 10)


# Create game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TATAKAE")

freq_groups = [[30], [70], [100]]  # Define frequency groups (Hz)


visualizer, audio_analyzer, game_bg_music, difficulty = None, None, None, None

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

COLOR_INACTIVE = (100, 80, 255)
COLOR_ACTIVE = (100, 200, 255)
COLOR_LIST_INACTIVE = (143, 238, 255)
COLOR_LIST_ACTIVE = (194, 246, 255)


# Load bullet images
player_bullet_img = pygame.image.load("./images/bullet_blue.png")
boss_bullet_img = pygame.image.load("./images/bullet_orange.png")

# Load heart images
heart_filled = pygame.image.load("./images/heart2.png")
heart_empty = pygame.image.load("./images/heart1.png")
heart_size = (40, 40)  # Resize heart images
heart_filled = pygame.transform.scale(heart_filled, heart_size)
heart_empty = pygame.transform.scale(heart_empty, heart_size)


# Define player
player_size = 40
player_pos = [WIDTH // 2, HEIGHT - player_size * 2]
player_speed = 6
player_velocity = [0, 0]  # Velocity vector

# Define boss animation frames
boss_size = 180


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

boss_frames, player_image, home_bg, drip_bg = None, None, None, None
theme_selected = "touhou"
home_bg_music = f"./background/{theme_selected}_bg.wav"


class DropDown:
    def __init__(self, color_menu, color_option, x, y, w, h, font, main, options):
        self.color_menu = color_menu
        self.color_option = color_option
        self.rect = pygame.Rect(x, y, w, h)  # Main dropdown rectangle
        self.font = font
        self.main = main  # Main button text
        self.options = options  # Dropdown options
        self.draw_menu = False  # Flag to determine if the menu is open
        self.menu_active = False  # Highlight state for the main dropdown button
        self.active_option = -1  # Highlighted option in the dropdown menu

    def draw(self, surf):
        # Draw the main dropdown button
        pygame.draw.rect(surf, self.color_menu[self.menu_active], self.rect, 0)
        msg = self.font.render(self.main, True, (0, 0, 0))
        surf.blit(msg, msg.get_rect(center=self.rect.center))

        # Draw the dropdown menu if open
        if self.draw_menu:
            for i, text in enumerate(self.options):
                rect = self.rect.copy()
                rect.y += (i + 1) * self.rect.height
                pygame.draw.rect(surf, self.color_option[1 if i == self.active_option else 0], rect, 0)
                msg = self.font.render(text, True, (0, 0, 0))
                surf.blit(msg, msg.get_rect(center=rect.center))

    def update(self, event_list):
        mpos = pygame.mouse.get_pos()  # Get mouse position
        self.menu_active = self.rect.collidepoint(mpos)  # Check if mouse is over the main dropdown button

        # Highlight the active option in the dropdown menu
        self.active_option = -1
        for i in range(len(self.options)):
            rect = self.rect.copy()
            rect.y += (i + 1) * self.rect.height
            if rect.collidepoint(mpos):
                self.active_option = i
                break

        # Close the dropdown menu if the mouse is not over the button or menu
        if not self.menu_active and self.active_option == -1:
            self.draw_menu = False
            

        # Handle events
        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button click
                if self.menu_active:  # Toggle menu if main button is clicked
                    self.draw_menu = not self.draw_menu
                elif self.draw_menu and self.active_option >= 0:  # Select an option
                    self.draw_menu = False
                    return self.active_option  # Return the selected option
        return -1


def song_preprocess(default="mywar.wav", diff="Easy"):
    global visualizer, audio_analyzer, game_bg_music, difficulty
    visualizer, audio_analyzer, game_bg_music, difficulty = None, None, None, None

    global FPS, lives, boss_health
    FPS, lives, boss_health = None, None, None

    if diff == "Easy":
        FPS = 60
        lives = 5
        boss_health = 50

    elif diff == "Medium":
        FPS = 100
        lives = 3
        boss_health = 100

    elif diff == "Hard":
        FPS = 200
        lives = 1
        boss_health = 200

    # Initialize spectrum visualizer
    visualizer = SpectrumVisualizer(f"./music/{default}")

    # Initialize audio analyzer
    audio_analyzer = AudioAnalyzer()

    precomputed_file = f"./precomputed/{default.replace('.wav', '.npy')}"

    # Check if precomputed data exists
    if os.path.exists(precomputed_file):
        start_time = time.time()
        audio_analyzer.load_precomputed(precomputed_file)  # Load precomputed data
        print("--- %s seconds ---" % (time.time() - start_time))
    else:
        print(f"Precomputed file not found. Computing data...")
        start_time = time.time()
        audio_analyzer.load(f"./music/{default}")  # Load the audio file
        audio_analyzer.precompute(freq_groups, precomputed_file)  # Precompute and save
        print("--- %s seconds ---" % (time.time() - start_time))

    game_bg_music = f"./music/{default}"
    difficulty = diff


def draw_end_page(message):
    """Draw the end page with a return to home button."""
    screen.fill(BLACK)

    message_text = font_arcade.render(message, True, WHITE)
    button_text = font_arcade_mid.render("Return Home", True, WHITE)

    # Position text
    message_rect = message_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    button_rect = pygame.Rect(WIDTH // 2 - 125, HEIGHT // 2 - 25, 250, 50)

    # Draw elements
    screen.blit(message_text, message_rect)
    pygame.draw.rect(screen, BLUE, button_rect)
    screen.blit(button_text, button_text.get_rect(center=button_rect.center))

    return button_rect


def change_theme():
    global boss_frames, player_image, home_bg, drip_bg, home_bg_music

    boss_frames = [
        pygame.transform.scale(pygame.image.load(f"./themes/{theme_selected}/{theme_selected}_boss_frame_{i}.png"), (boss_size, boss_size))
        for i in range(4)  # Assuming 4 frames: boss_frame_0.png to boss_frame_3.png
    ]
    player_image = pygame.image.load(f"./themes/{theme_selected}/{theme_selected}_player.png")  # Replace with your player image path
    player_image = pygame.transform.scale(player_image, (player_size, player_size))  # Scale the image to match player size

    home_bg = pygame.image.load(f"./themes/{theme_selected}/{theme_selected}_home_bg.png")
    drip_bg = pygame.image.load(f"./themes/{theme_selected}/{theme_selected}_bg.png")


    if home_bg_music != f"./background/{theme_selected}_bg.wav":
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        
        home_bg_music = f"./background/{theme_selected}_bg.wav"
        pygame.mixer.music.load(home_bg_music)  # Load home background music
        pygame.mixer.music.play(-1)  # Play in a loop


def show_theme_selection():
    """Display a confirmation window to select a theme."""
    global theme_selected
    popup_width, popup_height = 400, 300
    popup_rect = pygame.Rect((WIDTH - popup_width) // 2, (HEIGHT - popup_height) // 2, popup_width, popup_height)

    # Define theme images and their positions
    themes = ["mario", "touhou", "pixel", "pacman"]
    theme_images = [f"./themes/{theme}/{theme}.png" for theme in themes]  # Replace with your image paths
    theme_buttons = []
    past_theme = theme_selected
    theme_selected = None

    # Load theme images
    for i, theme_image_path in enumerate(theme_images):
        image = pygame.image.load(theme_image_path)
        scaled_image = pygame.transform.scale(image, (50, 50))  # Resize images
        x = popup_rect.x + 40 + i * 90                             
        y = popup_rect.y + 100
        rect = pygame.Rect(x, y, 50, 50)
        theme_buttons.append((scaled_image, rect, themes[i]))

    # Confirm and Return buttons
    confirm_rect = pygame.Rect(popup_rect.centerx - 170, popup_rect.bottom - 60, 150, 40)
    return_rect = pygame.Rect(popup_rect.centerx + 20, popup_rect.bottom - 60, 150, 40)

    while True:
        event_list = pygame.event.get()
        for event in event_list:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check if any theme button is clicked
                for _, rect, theme in theme_buttons:
                    if rect.collidepoint(event.pos):
                        theme_selected = theme  # Highlight selected theme
                if confirm_rect.collidepoint(event.pos) and theme_selected:
                    print(f"Theme confirmed: {theme_selected}")
                    # Apply theme logic here, e.g., change images or colors
                    change_theme()
                    return theme_selected
                elif return_rect.collidepoint(event.pos):
                    theme_selected = past_theme
                    return past_theme  # Return without making changes

        # Draw popup
        pygame.draw.rect(screen, BLACK, popup_rect)
        pygame.draw.rect(screen, WHITE, popup_rect, 5)  # Border

        title_text = font_arcade.render("Theme", True, WHITE)
        screen.blit(title_text, title_text.get_rect(center=(popup_rect.centerx, popup_rect.y + 30)))

        # Draw theme buttons and highlight selected theme
        for image, rect, theme in theme_buttons:
            screen.blit(image, rect)
            if theme_selected == theme:
                pygame.draw.rect(screen, GREEN, rect, 3)  # Highlight selected theme

        # If a theme is selected, display its name below all icons
        if theme_selected:
            theme_name_text = font_arcade_mid.render(theme_selected.capitalize(), True, WHITE)
            screen.blit(theme_name_text, theme_name_text.get_rect(center=(popup_rect.centerx, popup_rect.y + 200)))

        # Draw Confirm and Return buttons
        pygame.draw.rect(screen, GREEN, confirm_rect)
        pygame.draw.rect(screen, RED, return_rect)
        confirm_text = font_arcade_mid.render("Confirm", True, WHITE)
        return_text = font_arcade_mid.render("Return", True, WHITE)
        screen.blit(confirm_text, confirm_text.get_rect(center=confirm_rect.center))
        screen.blit(return_text, return_text.get_rect(center=return_rect.center))

        pygame.display.flip()


def draw_start_page():
    """Draw the start page with Start, Upload, Quit, and Theme buttons."""
    global boss_frames
    home_bg_size = (WIDTH, HEIGHT)
    home_bg_t = pygame.transform.scale(home_bg, home_bg_size)
    screen.blit(home_bg_t, (0, 0))

    title_text = font_arcade.render("TATAKAE!!", True, WHITE)
    start_text = font_arcade_mid.render("Start", True, WHITE)
    upload_text = font_arcade_mid.render("Upload", True, WHITE)
    quit_text = font_arcade_mid.render("Quit", True, WHITE)

    # Theme button
    # theme_button_rect = pygame.Rect(WIDTH - 60, 20, 40, 40)  # Square button at the top-right corner

    # Position text
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    start_rect = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2 - 25, 150, 50)
    upload_rect = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2 + 50, 150, 50)
    quit_rect = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2 + 125, 150, 50)

    # Draw elements
    screen.blit(title_text, title_rect)
    pygame.draw.rect(screen, BLUE, start_rect)
    pygame.draw.rect(screen, GREEN, upload_rect)
    pygame.draw.rect(screen, RED, quit_rect)
    # pygame.draw.rect(screen, (255, 255, 0), theme_button_rect)  # Yellow square for theme button
    screen.blit(start_text, start_text.get_rect(center=start_rect.center))
    screen.blit(upload_text, upload_text.get_rect(center=upload_rect.center))
    screen.blit(quit_text, quit_text.get_rect(center=quit_rect.center))

    # Draw theme icon (optional, replace with a theme icon if needed)
    
    
    image = pygame.image.load(f"./themes/{theme_selected}/{theme_selected}.png")
    scaled_image = pygame.transform.scale(image, (40, 40))  # Resize images
    theme_button_rect = pygame.Rect(WIDTH - 60, 20, 40, 40)

    screen.blit(scaled_image, theme_button_rect)
    

    return start_rect, upload_rect, quit_rect, theme_button_rect


def show_start_confirmation():
    """Show a confirmation pop-up with two dropdowns to select the game mode and difficulty."""
    popup_width, popup_height = 400, HEIGHT
    popup_rect = pygame.Rect((WIDTH - popup_width) // 2, (HEIGHT - popup_height) // 2, popup_width, popup_height)

    yes_rect = pygame.Rect(popup_rect.centerx - 170, popup_rect.bottom - 60, 150, 40)
    no_rect = pygame.Rect(popup_rect.centerx + 20, popup_rect.bottom - 60, 150, 40)

    songs = natsorted(os.listdir("./music"))

    # Create two dropdowns: one for game mode and one for difficulty
    dropdown_mode = DropDown(
        [COLOR_INACTIVE, COLOR_ACTIVE],
        [COLOR_LIST_INACTIVE, COLOR_LIST_ACTIVE],
        popup_rect.x + 50, popup_rect.y + 100, 300, 40,
        font_arcade_mid, "Select Song", songs
    )

    dropdown_difficulty = DropDown(
        [COLOR_INACTIVE, COLOR_ACTIVE],
        [COLOR_LIST_INACTIVE, COLOR_LIST_ACTIVE],
        popup_rect.x + 50, popup_rect.y + 160, 300, 40,
        font_arcade_mid, "Select Mode", ["Easy", "Medium", "Hard"]
    )

    selected_mode = None
    selected_difficulty = None

    while True:
        event_list = pygame.event.get()

        # Update both dropdowns and capture their selections
        mode_option = dropdown_mode.update(event_list)
        if mode_option >= 0:
            dropdown_mode.main = dropdown_mode.options[mode_option]
            selected_mode = dropdown_mode.main
            print(f"Selected mode: {selected_mode}")

        difficulty_option = dropdown_difficulty.update(event_list)
        if difficulty_option >= 0:
            dropdown_difficulty.main = dropdown_difficulty.options[difficulty_option]
            selected_difficulty = dropdown_difficulty.main
            print(f"Selected difficulty: {selected_difficulty}")

        for event in event_list:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if yes_rect.collidepoint(event.pos):  # Confirm selections
                    print(f"Game started with mode: {selected_mode}, difficulty: {selected_difficulty}")
                    return selected_mode, selected_difficulty
                elif no_rect.collidepoint(event.pos):  # Return to start page
                    return None, None

        # Draw the popup
        pygame.draw.rect(screen, BLACK, popup_rect)
        pygame.draw.rect(screen, WHITE, popup_rect, 5)  # Border

        title_text = font_arcade_mid.render("Game Settings", True, WHITE)
        screen.blit(title_text, title_text.get_rect(center=(popup_rect.centerx, popup_rect.y + 50)))

        pygame.draw.rect(screen, GREEN, yes_rect)
        pygame.draw.rect(screen, RED, no_rect)

        yes_text = font_arcade_mid.render("Start", True, WHITE)
        no_text = font_arcade_mid.render("Return", True, WHITE)

        screen.blit(yes_text, yes_text.get_rect(center=yes_rect.center))
        screen.blit(no_text, no_text.get_rect(center=no_rect.center))

        # Check which dropdown is open and draw its menu last
        if dropdown_mode.draw_menu:
            dropdown_difficulty.draw(screen)  # Draw the lower dropdown first
            dropdown_mode.draw(screen)  # Draw the upper dropdown on top
        else:
            dropdown_mode.draw(screen)  # Draw the upper dropdown first
            dropdown_difficulty.draw(screen)  # Draw the lower dropdown on top

        pygame.display.flip()


def upload_preprocessing(file_name):
    global visualizer, audio_analyzer
    visualizer, audio_analyzer = None, None

    base = os.path.basename(file_name)
    shutil.copyfile(file_name, f"./music/{base}")
    print("uploaded.")

    # Initialize spectrum visualizer
    visualizer = SpectrumVisualizer(f"./music/{base}")

    # Initialize audio analyzer
    audio_analyzer = AudioAnalyzer()
    precomputed_file = f"./precomputed/{base.replace('.wav', '.npy')}"

    # Check if precomputed data exists
    if os.path.exists(precomputed_file):
        start_time = time.time()
        audio_analyzer.load_precomputed(precomputed_file)  # Load precomputed data
        print("--- %s seconds ---" % (time.time() - start_time))
    else:
        print(f"Precomputed file not found. Computing data...")
        start_time = time.time()
        audio_analyzer.load(f"./music/{base}")  # Load the audio file
        audio_analyzer.precompute(freq_groups, precomputed_file)  # Precompute and save
        print("--- %s seconds ---" % (time.time() - start_time))

    print("preprocessed.")


def show_upload_confirmation():
    """Show a confirmation pop-up to ask if the player wants to upload."""
    popup_width, popup_height = 400, 150
    popup_rect = pygame.Rect((WIDTH - popup_width) // 2, (HEIGHT - popup_height) // 2, popup_width, popup_height)

    yes_rect = pygame.Rect(popup_rect.centerx - 170, popup_rect.bottom - 60, 150, 40)
    no_rect = pygame.Rect(popup_rect.centerx + 20, popup_rect.bottom - 60, 150, 40)

    file_name = None

    while True:
        pygame.draw.rect(screen, BLACK, popup_rect)
        pygame.draw.rect(screen, WHITE, popup_rect, 5)  # Border

        yes_text = font_arcade_mid.render("Upload", True, WHITE)
        no_text = font_arcade_mid.render("Return", True, WHITE)
            
        if file_name:
            base = os.path.basename(file_name)
            message_text = font_arcade_small.render(f"File uploaded: {base}", True, WHITE)
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
                if yes_rect.collidepoint(event.pos):  
                    file_name = tkinter.filedialog.askopenfilename()
                    top.withdraw()
                    upload_preprocessing(file_name)    # move to music folder and precompute

                elif no_rect.collidepoint(event.pos):  # Return to start page
                    return


def show_quit_confirmation():
    """Show a confirmation pop-up to ask if the player really wants to quit."""
    popup_width, popup_height = 400, 200
    popup_rect = pygame.Rect((WIDTH - popup_width) // 2, (HEIGHT - popup_height) // 2, popup_width, popup_height)

    yes_rect = pygame.Rect(popup_rect.centerx - 80, popup_rect.bottom - 60, 60, 40)
    no_rect = pygame.Rect(popup_rect.centerx + 20, popup_rect.bottom - 60, 60, 40)

    while True:
        pygame.draw.rect(screen, BLACK, popup_rect)
        pygame.draw.rect(screen, WHITE, popup_rect, 5)  # Border

        message_text = font_arcade.render("Sure?", True, WHITE)
        yes_text = font_arcade_mid.render("Yes", True, WHITE)
        no_text = font_arcade_mid.render("No", True, WHITE)

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
    """Display the start menu with Start, Upload, Quit, and Theme buttons."""
    pygame.mixer.music.load(home_bg_music)  # Load home background music
    pygame.mixer.music.play(-1)  # Play in a loop

    while True:
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)  # Play home music if stopped

        start_button_rect, upload_button_rect, quit_button_rect, theme_button_rect = draw_start_page()
        pygame.display.flip()  # Update the display

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_button_rect.collidepoint(event.pos):  # If Start button clicked
                    selected_song, selected_difficulty = show_start_confirmation()
                    if selected_song and selected_difficulty:
                        song_preprocess(selected_song, selected_difficulty)
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(game_bg_music)
                        pygame.mixer.music.play(-1)
                        return  # Exit the start menu
                elif upload_button_rect.collidepoint(event.pos):  # If Upload button clicked
                    show_upload_confirmation()
                elif quit_button_rect.collidepoint(event.pos):  # If Quit button clicked
                    show_quit_confirmation()
                elif theme_button_rect.collidepoint(event.pos):  # If Theme button clicked
                    selected_theme = show_theme_selection()
                    if selected_theme:
                        print(f"Theme changed to: {selected_theme}")


# Function to reset the game state
def reset_game():
    global score, bullets, enemy_bullets, player_pos, player_velocity
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
    screen.blit(player_image, (player_pos[0], player_pos[1]))


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
    l = {"Easy": 5, "Medium": 3, "Hard": 1}

    for i in range(l[difficulty]):
        x_pos = WIDTH - (i + 1) * (heart_size[0] + l[difficulty])  # Calculate x-position for hearts
        y_pos = 10  # Fixed y-position
        if i < (l[difficulty] - lives):  # Empty hearts appear from the rightmost
            screen.blit(heart_empty, (x_pos, y_pos))  # Draw empty hearts
        else:
            screen.blit(heart_filled, (x_pos, y_pos))  # Draw filled hearts


def main():
    change_theme()

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
        if theme_selected == "pacman" or theme_selected == "pixel":
            score_text = font_arcade.render(f"HP {boss_health}", True, WHITE)
        else:
            score_text = font_arcade.render(f"HP {boss_health}", True, BLACK)
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


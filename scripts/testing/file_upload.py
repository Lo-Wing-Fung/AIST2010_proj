import tkinter
import tkinter.filedialog
import pygame

WIDTH = 640
HEIGHT = 480
FPS = 30

def prompt_file():
    """Create a Tk file dialog and cleanup when finished"""
    file_name = tkinter.filedialog.askopenfilename()
    top.withdraw()
    return file_name



top = tkinter.Tk()
top.withdraw()  # hide window


pygame.init()
window = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

f = "<No File Selected>"
frames = 0
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                f = prompt_file()

    # draw surface - fill background
    window.fill(pygame.color.Color("grey"))
    ## update title to show filename
    pygame.display.set_caption(f"Frames: {frames:10}, File: {f}")
    # show surface
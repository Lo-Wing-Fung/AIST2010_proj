

# Customizable Rhythm Game with Unique Visuals 🎮

We have developed a rhythm-based bullet hell game as part of the AIST2010 course project. It combines rhythm synchronization with fast-paced action and customization options, including themes and uploaded songs.


## 🚀 Features
- **Dynamic Gameplay**: Dodge bullets and shoot your way to victory.
- **Rhythm Integration**: Bullet patterns are influenced by the song's bass and rhythm.
- **Custom Themes**: Change the game theme (background, music, characters) to your liking.
- **Song Upload**: Add your own music for a personalized experience.
- **Difficulty Levels**: Choose from Easy, Medium, and Hard to challenge yourself.

## 📋 Prerequisites

### Libraries and Dependencies
Ensure you have Python installed. Install the required libraries with the following:

```bash
pip install -r requirements.txt
```

### Setup
Clone the repository and pull the code:

```bash
git init
git remote add origin https://github.com/Lo-Wing-Fung/AIST2010_proj.git
git pull
```


## 🕹️ How to Play
1. **Run the Game**: Start the game with the following command:
   ```bash
   python scripts/main.py
   ```
2. **Homepage**: 
   - Background music plays automatically.
   - Click `Start` to select a song and difficulty level.
   - Choose a theme by clicking the theme button at the top-right corner.
3. **Upload Your Song**: 
   - Click `Upload` to add a new song.
   - The game will preprocess the song and generate rhythm-based gameplay.
4. **In-Game**: 
   - Dodge enemy bullets.
   - Shoot the boss to reduce its health.
   - Avoid losing lives (shown as heart icons).
5. **Win or Lose**:
   - Win by depleting the boss's HP.
   - Lose when all your lives are gone.

## 🎨 Themes
You can select themes like `Mario`, `Touhou`, `Pixel`, and `Pacman`. Each theme changes:
- Background images
- Character sprites
- Background music

To select a theme:
- Click the **theme button** (top-right corner) on the homepage.
- Choose a theme from the pop-up.
- Click `Confirm` to apply it.

## 🎵 Custom Song Integration
- Upload new songs through the `Upload` button on the homepage.
- The game will preprocess the song, generating data for rhythm-based bullet patterns.
- Supported formats: `.wav`

## 🎮 Game Controls
| Action         | Key            |
|----------------|----------------|
| Move Left      | `Left Arrow`   |
| Move Right     | `Right Arrow`  |
| Move Up        | `Up Arrow`     |
| Move Down      | `Down Arrow`   |
| Shoot          | `Space`        |

## 📂 File Structure
```
AIST2010_proj
├── scripts
│   ├── main.py            # Main game logic
│   ├── visual.py          # Spectrum visualizer logic
│   ├── AudioAnalyzer.py   # Audio analysis and rhythm generation
├── themes                 # Theme-specific assets
│   ├── mario
│   ├── touhou
│   ├── pixel
│   ├── pacman
├── music                  # Music files for gameplay
├── precomputed            # Precomputed rhythm data for songs
├── fonts                  # Fonts used in the game
├── images                 # General images for UI and gameplay
├── background             # Background music files
└── requirements.txt       # Dependencies
```

## 📖 Key Components

### `main.py`
- Handles the core game loop, rendering, and user interactions.
- Implements the dropdown menus, theme selection, and gameplay logic.

### `visual.py`
- Implements the visualizer for the spectrum, synchronized with the audio.

### `AudioAnalyzer.py`
- Performs audio analysis to generate rhythm-based patterns for gameplay.
- Precomputes data for efficient runtime performance.



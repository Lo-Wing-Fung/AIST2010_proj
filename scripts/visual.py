from AudioAnalyzer import *
import pygame
import math
import numpy as np

class SpectrumVisualizer:
    def __init__(self, filename="./music/mywar.wav", screen_width=480, screen_height=640):
        self.filename = filename
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.analyzer = AudioAnalyzer()
        self.analyzer.load(filename)

        self.circle_x = self.screen_width // 2
        self.circle_y = self.screen_height // 4

        self.min_radius = 30
        self.max_radius = 50
        self.radius = self.max_radius
        self.radius_vel = 0
        self.bass_trigger = -30

        self.bars = self._initialize_bars()
        self.polygon_default_color = [237, 190, 235]
        self.poly_color = self.polygon_default_color.copy()
        self.polygon_color_vel = [0, 0, 0]
        self.last_time = pygame.time.get_ticks()
        self.avg_bass = 0

    def _initialize_bars(self):
        freq_groups = [
            {"start": 50, "stop": 100, "count": 8},
            {"start": 120, "stop": 250, "count": 20},
            {"start": 251, "stop": 2000, "count": 25},
            {"start": 2001, "stop": 6000, "count": 7},
        ]
        bars = []
        angle = 0
        bar_spacing = 5
        angle_dt = 1

        for group in freq_groups:
            group_bars = []
            size = group["stop"] - group["start"]
            step = size // group["count"]
            for i in range(group["count"]):
                freq_range = np.arange(group["start"] + i * step, group["start"] + (i + 1) * step)
                group_bars.append(
                    RotatedAverageAudioBar(
                        self.circle_x,
                        self.circle_y,
                        freq_range,
                        (255, 0, 255),
                        angle=angle,
                        width=2,
                        max_height=100,
                    )
                )
                angle += angle_dt + bar_spacing
            bars.append(group_bars)
        return bars

    def update(self, delta_time):
        t = pygame.time.get_ticks()
        delta_time = (t - self.last_time) / 1000.0
        self.last_time = t

        self.avg_bass = 0
        for group in self.bars:
            for bar in group:
                bar.update_all(delta_time, pygame.mixer.music.get_pos() / 1000.0, self.analyzer)
            self.avg_bass += sum(bar.avg for bar in group) / len(group)

        # Pulsating effect on bass trigger
        if self.avg_bass > self.bass_trigger:
            new_radius = self.min_radius + int(self.avg_bass * (self.max_radius - self.min_radius) / 50)
            self.radius_vel = (new_radius - self.radius) / 0.1
        self.radius += self.radius_vel * delta_time

    def render(self, screen):
        for group in self.bars:
            for bar in group:
                bar.x = self.circle_x + self.radius * math.cos(math.radians(bar.angle - 90))
                bar.y = self.circle_y + self.radius * math.sin(math.radians(bar.angle - 90))
                bar.update_rect()
                bar.render(screen)

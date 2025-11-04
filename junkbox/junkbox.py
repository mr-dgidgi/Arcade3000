#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
/!\ Script generated with IA

Junkbox - Fullscreen Jukebox with Cyberpunk Aesthetic
Usage: python3 juknkbox.py [music_root_folder] [optional_font_path]

Features added:
 - Scanline overlay (subtle horizontal lines)
 - Glitch effects on title / selected track (color shifts, jitter, brief duplicates)
 - Tries to load terminal-like fonts (DejaVuSansMono, VT323, or use provided TTF path)
 - Keeps same controls: ← → genres, ↑ ↓ tracks, Enter play (1 credit), Space +1 credit, s stop, q/Esc quit

Notes:
 - Depends on pygame (pip install pygame)
 - You can pass a TTF path as the 2nd argument to use a specific font.

"""

import sys
import os
import time
import threading
import importlib
import random

import pygame

AUDIO_EXTS = ('.mp3', '.wav', '.ogg', '.flac')

# ---------- Scan music ----------

def scan_music(root):
    genres = []
    if not os.path.isdir(root):
        return genres
    for entry in sorted(os.listdir(root)):
        p = os.path.join(root, entry)
        if os.path.isdir(p):
            tracks = []
            for fname in sorted(os.listdir(p)):
                if fname.lower().endswith(AUDIO_EXTS):
                    tracks.append(os.path.join(p, fname))
            if tracks:
                genres.append((entry, tracks))
    return genres

# ---------- Audio player with fallback ----------
class Player:
    DEFAULT_SIM_LENGTH = 30.0  # secondes si durée inconnue en mode dummy

    def __init__(self):
        self.lock = threading.Lock()
        self.current = None
        self.length = 0.0
        self.playing = False
        self._stop_flag = False
        self.available = True
        self._sim_start = None
        # init mixer with fallback to dummy if necessary
        try:
            pygame.mixer.init()
        except Exception as e1:
            try:
                os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
                try:
                    importlib.reload(pygame)
                except Exception:
                    pass
                pygame.mixer.init()
            except Exception as e2:
                self.available = False
                self._init_error = (e1, e2)

    def load_length(self, filepath):
        if self.available:
            try:
                snd = pygame.mixer.Sound(filepath)
                return snd.get_length()
            except Exception:
                return 0.0
        else:
            return 0.0

    def play(self, filepath):
        with self.lock:
            self.stop()
            if not self.available:
                # simulate playback
                self.current = filepath
                # try to get a length, else use default
                length = self.load_length(filepath) or 0.0
                if length <= 0.0:
                    length = self.DEFAULT_SIM_LENGTH
                self.length = length
                self.playing = True
                self._stop_flag = False
                self._sim_start = time.time()

                def _sim():
                    start = self._sim_start
                    while not self._stop_flag and (time.time() - start) < self.length:
                        time.sleep(0.1)
                    # mark finished
                    with self.lock:
                        self.playing = False
                        self.current = None
                        self._sim_start = None
                        self._stop_flag = False

                threading.Thread(target=_sim, daemon=True).start()
                return

            # real audio path
            try:
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play()
                self.current = filepath
                self.length = self.load_length(filepath)
                self.playing = True
                self._stop_flag = False
                self._sim_start = time.time()
            except Exception as e:
                self.current = None
                self.playing = False
                self._sim_start = None
                raise

    def stop(self):
        with self.lock:
            self._stop_flag = True
            if self.available:
                try:
                    pygame.mixer.music.stop()
                except Exception:
                    pass
            # reset simulation state
            self.playing = False
            self.current = None
            self._sim_start = None
            # small delay to allow sim thread to exit if running
            time.sleep(0.01)

    def get_pos(self):
        """Return position in seconds. Works for both real and simulated playback."""
        if not self.available:
            if self._sim_start is None:
                return None
            return time.time() - self._sim_start
        pos_ms = pygame.mixer.music.get_pos()
        if pos_ms < 0:
            # no position info
            # If we started playback just now, we can return elapsed since _sim_start if set
            if self._sim_start:
                return time.time() - self._sim_start
            return None
        return pos_ms / 1000.0

    def is_playing(self):
        if not self.available:
            return self.playing
        try:
            return pygame.mixer.music.get_busy()
        except Exception:
            return False

# ---------- Visual effects helpers ----------

def draw_text(surface, text, font, pos, color, align="topleft"):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    setattr(rect, align, pos)
    surface.blit(surf, rect)
    return surf, rect


def draw_glitch_text(surface, text, font, pos, base_color, time_seed, max_jitter=6, glitch_prob=0.015):
    """Draw text normally then sometimes add glitch layers (offset colored duplicates).
    - glitch_prob: per-frame chance to trigger an intense glitch for this text
    - time_seed: used to have different random states per text element
    Returns whether a glitch was drawn (bool).
    """
    # Draw base
    surf = font.render(text, True, base_color)
    rect = surf.get_rect()
    rect.topleft = pos
    surface.blit(surf, rect)

    rng = random.Random((time_seed, int(time.time() * 1000)))
    drew_glitch = False

    # Small subtle shimmer (always small chance per frame)
    if rng.random() < 0.07:
        offset_x = rng.randint(-1, 1)
        offset_y = rng.randint(-1, 1)
        shimmer = font.render(text, True, (180, 255, 255))
        srect = shimmer.get_rect()
        srect.topleft = (pos[0] + offset_x, pos[1] + offset_y)
        shimmer.set_alpha(120)
        surface.blit(shimmer, srect)

    # Occasional heavier glitch
    if rng.random() < glitch_prob:
        drew_glitch = True
        layers = 3
        for i in range(layers):
            ox = rng.randint(-max_jitter, max_jitter)
            oy = rng.randint(-max_jitter // 2, max_jitter // 2)
            color = (rng.randint(150, 255), rng.randint(80, 255), rng.randint(80, 255))
            layer = font.render(text, True, color)
            lrect = layer.get_rect()
            lrect.topleft = (pos[0] + ox, pos[1] + oy)
            layer.set_alpha(160 - i * 40)
            surface.blit(layer, lrect)

        # also draw a horizontal slice shifted
        try:
            slice_y = rng.randint(0, surf.get_height() - 1)
            slice_h = max(1, rng.randint(1, surf.get_height() // 4))
            clip_rect = pygame.Rect(0, slice_y, surf.get_width(), slice_h)
            fragment = surf.subsurface(clip_rect).copy()
            frag_rect = fragment.get_rect()
            frag_rect.topleft = (
                pos[0] + rng.randint(-20, 20),
                pos[1] + slice_y + rng.randint(-4, 4)
            )
            fragment.set_alpha(200)
            surface.blit(fragment, frag_rect)
        except Exception:
            pass

    return drew_glitch



def draw_scanlines(surface, line_spacing=4, alpha=18, animate=False, t=0.0, speed=60, band_height=80, band_alpha=110):
    """Overlay horizontal scanlines across the whole surface.

    If animate is True, a brighter band will slowly move vertically to simulate
    a CRT refresh/rolling scanline effect. Parameters:
    - line_spacing: pixels between drawn lines
    - alpha: base line alpha (0-255)
    - animate: enable moving bright band
    - t: current time (seconds) used to compute animation position
    - speed: vertical speed in pixels/second for the bright band
    - band_height: height in pixels of the bright band
    - band_alpha: alpha value for lines inside the bright band
    """
    w, h = surface.get_size()
    # Base scanlines
    line_surf = pygame.Surface((w, h), flags=pygame.SRCALPHA)
    line_color = (0, 0, 0, alpha)
    for y in range(0, h, line_spacing):
        line_surf.fill(line_color, rect=pygame.Rect(0, y, w, 1))

    # Animated brighter band (optional)
    if animate:
        # compute top of band so it moves from -band_height .. h
        # using time as source so animation is smooth and deterministic
        total_span = h + band_height
        pos = (t * speed) % total_span
        top = int(pos - band_height)
        band_surf = pygame.Surface((w, h), flags=pygame.SRCALPHA)
        band_color = (0, 0, 0, band_alpha)
        # draw brighter scanlines only inside the band area
        start_y = max(0, top)
        end_y = min(h, top + band_height)
        for y in range(start_y - (start_y % line_spacing), end_y, line_spacing):
            # ensure we only draw inside band
            if y < 0 or y >= h:
                continue
            band_surf.fill(band_color, rect=pygame.Rect(0, y, w, 1))
        # composite: draw base then band over it
        line_surf.blit(band_surf, (0, 0))

    surface.blit(line_surf, (0, 0))

# ---------- Utilities ----------

def format_time(t):
    try:
        ti = int(t)
    except Exception:
        return "0:00"
    m = ti // 60
    s = ti % 60
    return f"{m}:{s:02d}"

# ---------- Main app ----------

def pick_mono_font(ttf_path=None, size=20):
    """Pick a monospace/terminal-like font.

    Priority:
    1. If `ttf_path` is provided and valid, use it.
    2. Look for the first .ttf/.otf file under `assets/fonts/` relative to this file.
    3. Try a list of common monospace font names via pygame.font.match_font.
    4. Fallback to pygame's default font.
    """
    # 1) explicit path
    if ttf_path:
        if os.path.isfile(ttf_path):
            try:
                return pygame.font.Font(ttf_path, size)
            except Exception:
                pass

    # 2) project assets/fonts/ (relative to this module)
    try:
        base_dir = os.path.dirname(__file__)
        fonts_dir = os.path.join(base_dir, 'assets', 'fonts')
        if os.path.isdir(fonts_dir):
            for fname in sorted(os.listdir(fonts_dir)):
                if fname.lower().endswith(('.ttf', '.otf')):
                    fpath = os.path.join(fonts_dir, fname)
                    try:
                        return pygame.font.Font(fpath, size)
                    except Exception:
                        # try next file
                        continue
    except Exception:
        # if anything goes wrong, continue to other fallbacks
        pass

    # 3) Common monospace/terminal-like fonts via system match
    names = [
        'vt323',            # pixel/terminal webfont
        'dejavusansmono',
        'inconsolata',
        'anonymouspro',
        'couriernew',
        'liberationmono',
        'sourcecodepro',
        'consolas',
    ]
    for n in names:
        f = pygame.font.match_font(n)
        if f:
            try:
                return pygame.font.Font(f, size)
            except Exception:
                continue

    # 4) fallback to pygame default
    return pygame.font.Font(pygame.font.get_default_font(), size)


def main(music_root, font_path=None):
    pygame.init()
    # initialize joystick subsystem and try to open first gamepad (if any)
    pygame.joystick.init()
    joystick = None
    joystick_name = None
    joystick_buttons = 0
    joystick_hats = 0
    if pygame.joystick.get_count() > 0:
        try:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            joystick_name = joystick.get_name()
            joystick_buttons = joystick.get_numbuttons()
            joystick_hats = joystick.get_numhats()
            msg = f"Manette détectée: {joystick_name}"
            last_msg_time = time.time()
        except Exception:
            joystick = None
    info = pygame.display.Info()
    screen_w, screen_h = info.current_w, info.current_h

    # Fullscreen window
    screen = pygame.display.set_mode((screen_w, screen_h), pygame.FULLSCREEN | pygame.DOUBLEBUF)
    pygame.display.set_caption("CyberJuke")

    # Colors (cyberpunk neon)
    BG = (6, 6, 12)
    NEON_PINK = (255, 85, 255)
    NEON_CYAN = (0, 255, 255)
    NEON_YELLOW = (255, 220, 90)
    TEXT = (200, 200, 220)
    DIM = (120, 120, 130)

    # Fonts (sizes chosen relative to screen)
    title_size = max(28, screen_w // 40)
    large_size = max(20, screen_w // 60)
    med_size = max(16, screen_w // 90)
    small_size = max(12, screen_w // 120)

    font_title = pick_mono_font(font_path, title_size)
    font_large = pick_mono_font(font_path, large_size)
    font_med = pick_mono_font(font_path, med_size)
    font_small = pick_mono_font(font_path, small_size)

    # scan
    genres = scan_music(music_root)
    if not genres:
        print(f"Aucun fichier audio trouvé sous '{music_root}'.")
        pygame.quit()
        return

    gi = 0
    ti = 0
    credits = 0
    player = Player()
    msg = "Bienvenue dans CyberJuke - Presse Espace pour credit."

    clock = pygame.time.Clock()
    running = True

    PROGRESS_BAR_W = int(screen_w * 0.5)
    PROGRESS_BAR_H = max(12, screen_h // 80)
    PROGRESS_X = (screen_w - PROGRESS_BAR_W) // 2
    PROGRESS_Y = int(screen_h * 0.90)

    last_msg_time = 0

    # glitch controller
    glitch_enabled = True
    last_glitch_time = 0
    glitch_cooldown = 0.12

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            # joystick hat (dpad)
            elif ev.type == pygame.JOYHATMOTION:
                try:
                    hx, hy = ev.value
                except Exception:
                    hx, hy = 0, 0
                # vertical (track selection)
                if hy == 1:
                    ti = (ti - 1) % len(genres[gi][1])
                elif hy == -1:
                    ti = (ti + 1) % len(genres[gi][1])
                # horizontal (genre selection)
                if hx == -1:
                    gi = (gi - 1) % len(genres)
                    ti = min(ti, len(genres[gi][1]) - 1)
                    msg = f"Genre -> {genres[gi][0]}"
                    last_msg_time = time.time()
                elif hx == 1:
                    gi = (gi + 1) % len(genres)
                    ti = min(ti, len(genres[gi][1]) - 1)
                    msg = f"Genre -> {genres[gi][0]}"
                    last_msg_time = time.time()
            # joystick buttons
            elif ev.type == pygame.JOYBUTTONDOWN:
                b = getattr(ev, 'button', None)
                if b is not None:
                    # A -> play (common mapping button 0)
                    if b == 0:
                        selected = genres[gi][1][ti]
                        if credits <= 0:
                            msg = "Pas assez de credits. Appuie sur Select/back pour ajouter 1 credit."
                            last_msg_time = time.time()
                        else:
                            try:
                                player.play(selected)
                                credits -= 1
                                msg = f"Lecture: {os.path.basename(selected)}  (credits: {credits})"
                                last_msg_time = time.time()
                            except Exception as e:
                                msg = f"Erreur lecture: {e}"
                                last_msg_time = time.time()
                    # B -> stop (common mapping button 1)
                    elif b == 1:
                        player.stop()
                        msg = "Arrêt de la lecture."
                        last_msg_time = time.time()
                    # Select / Back -> add credit (button 6 or 8 on some controllers)
                    elif b in (6, 8):
                        credits += 1
                        msg = f"credit ajouté. Total: {credits}"
                        last_msg_time = time.time()
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif ev.key == pygame.K_LEFT:
                    gi = (gi - 1) % len(genres)
                    ti = min(ti, len(genres[gi][1]) - 1)
                    msg = f"Genre -> {genres[gi][0]}"
                    last_msg_time = time.time()
                elif ev.key == pygame.K_RIGHT:
                    gi = (gi + 1) % len(genres)
                    ti = min(ti, len(genres[gi][1]) - 1)
                    msg = f"Genre -> {genres[gi][0]}"
                    last_msg_time = time.time()
                elif ev.key == pygame.K_UP:
                    ti = (ti - 1) % len(genres[gi][1])
                elif ev.key == pygame.K_DOWN:
                    ti = (ti + 1) % len(genres[gi][1])
                elif ev.key == pygame.K_SPACE:
                    credits += 1
                    msg = f"credit ajouté. Total: {credits}"
                    last_msg_time = time.time()
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    selected = genres[gi][1][ti]
                    if credits <= 0:
                        msg = "Pas assez de credits. Appuie sur espace pour ajouter 1 credit."
                        last_msg_time = time.time()
                    else:
                        try:
                            player.play(selected)
                            credits -= 1
                            msg = f"Lecture: {os.path.basename(selected)}  (credits: {credits})"
                            last_msg_time = time.time()
                        except Exception as e:
                            msg = f"Erreur lecture: {e}"
                            last_msg_time = time.time()
                elif ev.key == pygame.K_s:
                    player.stop()
                    msg = "Arrêt de la lecture."
                    last_msg_time = time.time()

        # Clear
        screen.fill(BG)

        # Header / Title (with occasional glitch)
        title_text = "== Junkbox - Arcade 3000 ========================="
        title_pos = (30, 20)
        if glitch_enabled and random.random() < 0.02:
            # instant glitch triggered
            draw_glitch_text(screen, title_text, font_title, title_pos, NEON_CYAN, time_seed=1, max_jitter=12, glitch_prob=0.5)
            last_glitch_time = time.time()
        else:
            # small shimmer or normal
            draw_glitch_text(screen, title_text, font_title, title_pos, NEON_CYAN, time_seed=1, max_jitter=4, glitch_prob=0.006)

        # --- DUMMY MODE INDICATOR ---
        # Affiche un message visible si on est en fallback dummy (aucune sortie audio)
        if not player.available:
            # flicker the red/orange color slightly for cyberpunk alarm
            flicker = random.randint(120, 255)
            dummy_color = (255, flicker // 2, flicker // 2)
            dummy_text = "[MODE DUMMY ACTIVÉ – aucune sortie audio]"
            # placed top-left with small margin
            draw_text(screen, dummy_text, font_small, (20, 18), dummy_color, align="topleft")

        # Genre strip (center top)
        genre_names = [g for g, t in genres]
        genre_line = "   ".join([f"[{n}]" if i == gi else n for i, n in enumerate(genre_names)])
        draw_text(screen, genre_line, font_large, (screen_w//2, 90), NEON_PINK, align="midtop")

        # Selected track info (left) - glitchable
        genre_name, tracks = genres[gi]
        sel_name = os.path.basename(tracks[ti])
        draw_text(screen, f"Genre: {genre_name}", font_med, (60, 160), NEON_YELLOW, align="topleft")

        # draw the selectable track with strong glitch probability so it "flickers"
        sel_pos = (60, 200)
        draw_glitch_text(screen, f"Track: {sel_name}", font_large, sel_pos, TEXT, time_seed=2+ti, max_jitter=8, glitch_prob=0.03)

        # Credits and controls (right)
        controls = [
            f"credits: {credits}  (Espace = +1 credit)",
            "← → : genres    ↑ ↓ : pistes",
            "Entrée : jouer (1 credit)    s : stop    q/Esc : quitter"
        ]
        y = 160
        for c in controls:
            draw_text(screen, c, font_med, (screen_w - 60, y), DIM, align="topright")
            y += 32

        # Playlist (center-left)
        list_x = 60
        list_y = 300
        max_lines = 20
        start = max(0, ti - max_lines//2)
        for idx in range(start, min(len(tracks), start + max_lines)):
            fname = os.path.basename(tracks[idx])
            prefix = "▶ " if (player.current and os.path.basename(player.current) == fname and player.is_playing()) else "  "
            text = prefix + fname
            color = NEON_CYAN if idx == ti else DIM
            font_use = font_med if idx == ti else font_small
            # selected line jitters a bit to sell the glitch effect
            if idx == ti and random.random() < 0.02:
                jitter = (random.randint(-3,3), random.randint(-2,2))
            else:
                jitter = (0,0)
            draw_text(screen, text, font_use, (list_x + jitter[0], list_y + (idx - start) * 28 + jitter[1]), color, align="topleft")

        # Progress bar
        if player.current and player.is_playing():
            pos = player.get_pos() or 0.0
            length = player.length or 0.0
            pct = 0.0
            if length > 0:
                pct = min(1.0, max(0.0, pos / length))
            filled_w = int(PROGRESS_BAR_W * pct)
            # background bar
            pygame.draw.rect(screen, (30, 30, 40), (PROGRESS_X - 4, PROGRESS_Y - 4, PROGRESS_BAR_W + 8, PROGRESS_BAR_H + 8), border_radius=6)
            # empty
            pygame.draw.rect(screen, (40, 40, 50), (PROGRESS_X, PROGRESS_Y, PROGRESS_BAR_W, PROGRESS_BAR_H), border_radius=6)
            # filled neon
            if filled_w > 0:
                pygame.draw.rect(screen, NEON_PINK, (PROGRESS_X, PROGRESS_Y, filled_w, PROGRESS_BAR_H), border_radius=6)
            # elapsed text
            time_text = f"{format_time(pos)} / {format_time(length)}"
            draw_text(screen, time_text, font_small, (screen_w//2, PROGRESS_Y - 30), NEON_CYAN, align="midtop")
        else:
            # empty bar
            pygame.draw.rect(screen, (30, 30, 40), (PROGRESS_X - 4, PROGRESS_Y - 4, PROGRESS_BAR_W + 8, PROGRESS_BAR_H + 8), border_radius=6)
            pygame.draw.rect(screen, (40, 40, 50), (PROGRESS_X, PROGRESS_Y, PROGRESS_BAR_W, PROGRESS_BAR_H), border_radius=6)
            draw_text(screen, "Aucune lecture en cours.", font_small, (screen_w//2, PROGRESS_Y - 30), DIM, align="midtop")

        # Scanlines overlay (animated bright band)
        draw_scanlines(screen, line_spacing=3, alpha=30, animate=True, t=time.time(), speed=90, band_height=max(40, screen_h // 12), band_alpha=120)

        # subtle vignette / noise - a faint overlay of dots
        if random.random() < 0.08:
            noise = pygame.Surface((screen_w, screen_h), flags=pygame.SRCALPHA)
            for _ in range(200):
                x = random.randint(0, screen_w-1)
                y = random.randint(0, screen_h-1)
                noise.fill((random.randint(0,30), random.randint(0,30), random.randint(0,30), random.randint(6,18)), rect=pygame.Rect(x,y,1,1))
            screen.blit(noise, (0,0))

        # Footer message (brief)
        if msg and time.time() - last_msg_time < 6:
            draw_text(screen, msg, font_small, (screen_w//2, screen_h - 50), NEON_YELLOW, align="midtop")

        pygame.display.flip()

        # detect end of track (if pygame reports not busy but we thought playing)
        if player.current and not player.is_playing() and player.playing:
            player.playing = False
            player.current = None
            msg = "Lecture terminée."
            last_msg_time = time.time()

        clock.tick(30)

    # cleanup
    try:
        player.stop()
    except Exception:
        pass
    pygame.quit()


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.getcwd(), "music")
    font_arg = sys.argv[2] if len(sys.argv) > 2 else None
    main(root, font_arg)

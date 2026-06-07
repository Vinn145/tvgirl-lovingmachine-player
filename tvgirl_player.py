import pygame
import sys
import os
import re
import math
from tkinter import Tk, filedialog

# -------------------------------------------------------------
# INITIALIZATION
# -------------------------------------------------------------
pygame.init()
pygame.mixer.init()
Tk().withdraw()  # Sembunyikan window utama tkinter

# -------------------------------------------------------------
# PALET WARNA ALA TV GIRL (Lebih Clean & Muted)
# -------------------------------------------------------------
BG_COLOR = (18, 2, 8)          # #120208 (Sedikit lebih gelap, deep contrast)
PANEL_BG = (28, 4, 14)         # #1c040e (Background lirik aktif)
BORDER_COLOR = (54, 12, 30)    # #360c1e (Border dibuat lebih redup/thin)
TEXT_MUTED = (94, 34, 56)      # #5e2238 (Lirik masa depan, lebih samar)
TEXT_PAST = (51, 10, 26)       # #330a1a (Lirik masa lalu, sangat samar/clean)
TEXT_MAIN = (255, 186, 212)    # #ffbad4 (Pink pastel lembut untuk lirik aktif)
TEXT_ACTIVE = (255, 143, 185)  # #ff8fb9 (Pink terang untuk judul lagu)
NEON_PINK = (255, 46, 122)     # #ff2e7a (Aksen timeline & visualizer)

# Setup Window
WIDTH, HEIGHT = 1000, 570      
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MarlboroRed")
clock = pygame.time.Clock()

# Fonts (Menggunakan font monospace Consolas)
font_small = pygame.font.SysFont("Consolas", 11)
font_label = pygame.font.SysFont("Consolas", 10, bold=True)
font_title = pygame.font.SysFont("Consolas", 14, bold=True)
font_lyrics = pygame.font.SysFont("Consolas", 15)
font_lyrics_active = pygame.font.SysFont("Consolas", 17, bold=True)

# -------------------------------------------------------------
# HELPER FUNCTIONS (Logika parsing & formatting)
# -------------------------------------------------------------
def fmt_time(seconds):
    if seconds is None or seconds < 0:
        return "0:00"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m}:{s:02d}"

def parse_lrc(text_content):
    res = []
    lines = text_content.split('\n')
    re_time = re.compile(r'\[(\d{1,2}):(\d{2})\.(\d{2,3})\]')
    
    is_lrc = any(re_time.search(l) for l in lines)
    if is_lrc:
        for line in lines:
            text = re.sub(r'\[\d{1,2}:\d{2}\.\d{2,3}\]', '', line).strip()
            if not text:
                continue
            for match in re_time.finditer(line):
                m, s, ms = match.groups()
                t = int(m) * 60 + int(s) + int(ms.ljust(3, '0')) / 1000.0
                res.append({"time": t, "text": text})
        res.sort(key=lambda x: x["time"])
    else:
        for line in lines:
            if line.strip():
                res.append({"time": -1, "text": line.strip()})
    return res

def get_current_audio_time():
    if not playing:
        return paused_ticks / 1000.0
    elapsed = pygame.time.get_ticks() - audio_start_ticks
    return elapsed / 1000.0

def toggle_play():
    global playing, audio_start_ticks, paused_ticks
    if not audio_path:
        return
    if not playing:
        pygame.mixer.music.play(start=paused_ticks / 1000.0)
        audio_start_ticks = pygame.time.get_ticks() - paused_ticks
        playing = True
    else:
        paused_ticks = pygame.time.get_ticks() - audio_start_ticks
        pygame.mixer.music.stop()
        playing = False

# -------------------------------------------------------------
# STATE VARIABLES (Konfigurasi File Otomatis)
# -------------------------------------------------------------
audio_path = "Loving Machine.mp3"
track_name = "Loving Machine"
artist_name = "TV Girl"
lrc_path = "TV Girl - Loving Machine.lrc"
img_path = "AlbumCover.jpg"  

lyrics = []           
cur_idx = -1
playing = False
looping = False
volume = 0.8
audio_duration = 0.0  
audio_start_ticks = 0 
paused_ticks = 0      
cover_image = None

pygame.mixer.music.set_volume(volume)

# -------------------------------------------------------------
# AUTOMATIC LOAD SYSTEM (Startup)
# -------------------------------------------------------------
if os.path.exists(lrc_path):
    with open(lrc_path, 'r', encoding='utf-8', errors='ignore') as f:
        lyrics = parse_lrc(f.read())

if os.path.exists(img_path):
    try:
        img = pygame.image.load(img_path)
        cover_image = pygame.transform.scale(img, (169, 169))
    except Exception as e:
        print("Gagal memuat default cover:", e)

if os.path.exists(audio_path):
    pygame.mixer.music.load(audio_path)
    try:
        sound = pygame.mixer.Sound(audio_path)
        audio_duration = sound.get_length()
    except:
        audio_duration = 180.0

toggle_play()

# -------------------------------------------------------------
# MAIN RECT GEOMETRY (Geometri Interaksi)
# -------------------------------------------------------------
btn_play = pygame.Rect(45, 520, 40, 25)
slider_prog = pygame.Rect(45, 495, 910, 6)
slider_vol = pygame.Rect(890, 528, 65, 4)

# -------------------------------------------------------------
# GAME LOOP
# -------------------------------------------------------------
running = True
while running:
    mx, my = pygame.mouse.get_pos()
    click = False
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                click = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                toggle_play()

    cur_time = get_current_audio_time()
    if playing and cur_time >= audio_duration:
        playing = False
        paused_ticks = 0
        if looping:
            toggle_play()

    if click:
        if btn_play.collidepoint((mx, my)):
            toggle_play()
        elif slider_prog.collidepoint((mx, my)):
            if audio_duration > 0:
                pct = (mx - slider_prog.x) / slider_prog.width
                paused_ticks = int(pct * audio_duration * 1000)
                if playing:
                    pygame.mixer.music.play(start=paused_ticks / 1000.0)
                    audio_start_ticks = pygame.time.get_ticks() - paused_ticks
        elif pygame.Rect(820, 515, 140, 30).collidepoint((mx, my)):
            if slider_vol.x <= mx <= slider_vol.x + slider_vol.width:
                volume = (mx - slider_vol.x) / slider_vol.width
                volume = max(0.0, min(1.0, volume))
                pygame.mixer.music.set_volume(volume)

    # -------------------------------------------------------------
    # RENDERING GRAPHICS
    # -------------------------------------------------------------
    screen.fill(BG_COLOR)
    pygame.draw.rect(screen, BORDER_COLOR, (0, 0, WIDTH, HEIGHT), 1)

    # --- 1. MINIMALIST HEADER ---
    lbl_logo = font_title.render("MarlboroRed", True, TEXT_MAIN)
    screen.blit(lbl_logo, (15, 8))
    pygame.draw.line(screen, BORDER_COLOR, (0, 32), (WIDTH, 32), 1)

    # --- 2. LEFT PANEL (Polesan Elemen Baru Biar Nggak Kosong) ---
    pygame.draw.line(screen, BORDER_COLOR, (195, 32), (195, 460), 1)
    
    # Album Cover Area
    if cover_image:
        screen.blit(cover_image, (13, 45))
    else:
        pygame.draw.rect(screen, BORDER_COLOR, (13, 45, 169, 169), 1)
        lbl_art_placeholder = font_small.render("no art loaded", True, TEXT_MUTED)
        screen.blit(lbl_art_placeholder, (45, 120))

    # Informasi Track & Artist
    screen.blit(font_label.render("TRACK", True, TEXT_MUTED), (13, 235))
    txt_track = font_title.render(track_name[:20] + "..." if len(track_name) > 20 else track_name, True, TEXT_ACTIVE)
    screen.blit(txt_track, (13, 249))
    
    screen.blit(font_label.render("ARTIST", True, TEXT_MUTED), (13, 277))
    txt_artist = font_small.render(artist_name, True, TEXT_MAIN)
    screen.blit(txt_artist, (13, 291))

    # [BARU] Elemen Kosmetik: Spesifikasi Audio ala Tape Player jadul
    screen.blit(font_label.render("DECK INFO", True, TEXT_MUTED), (13, 325))
    screen.blit(font_small.render("TYPE : MPEG AUDIO (MP3)", True, TEXT_MUTED), (13, 339))
    screen.blit(font_small.render("RATE : 44100 HZ / 320KBPS", True, TEXT_MUTED), (13, 353))
    screen.blit(font_small.render("MODE : STEREO CH.", True, TEXT_MUTED), (13, 367))

    # [BARU] Indikator Putar Berkedip (Blinking Status)
    ticks = pygame.time.get_ticks()
    blink = (ticks // 500) % 2 == 0  # Berkedip setiap 500ms
    
    if playing:
        status_label = "● PLAYING" if blink else "  PLAYING"
        status_color = NEON_PINK
    elif paused_ticks > 0:
        status_label = "║ PAUSED"
        status_color = TEXT_MUTED
    else:
        status_label = "■ STOPPED"
        status_color = TEXT_MUTED

    screen.blit(font_label.render("STATUS", True, TEXT_MUTED), (13, 410))
    screen.blit(font_small.render(status_label, True, status_color), (13, 424))

    # --- 3. RIGHT PANEL (Lyrics Stream with Better Fade Out) ---
    screen.blit(font_label.render("› lyrics", True, TEXT_MUTED), (210, 45))
    
    if not lyrics:
        lbl_no_lyr = font_small.render("lirik belum dimuat", True, TEXT_MUTED)
        screen.blit(lbl_no_lyr, (350, 220))
    else:
        new_idx = -1
        if lyrics[0]["time"] >= 0:
            for i, line in enumerate(lyrics):
                if cur_time >= line["time"]:
                    new_idx = i
            cur_idx = new_idx

        lyric_center_y = 220
        line_height = 32 
        
        for i, line in enumerate(lyrics):
            rel_y = lyric_center_y + (i - cur_idx) * line_height
            if 65 < rel_y < 430:
                if i == cur_idx:
                    line_bg = pygame.Rect(210, rel_y - 6, 760, 28)
                    pygame.draw.rect(screen, PANEL_BG, line_bg, 0, 4) 
                    pygame.draw.rect(screen, NEON_PINK, (210, rel_y - 6, 3, 28)) 
                    txt_surf = font_lyrics_active.render(line["text"], True, TEXT_MAIN)
                elif i < cur_idx:
                    txt_surf = font_lyrics.render(line["text"], True, TEXT_PAST)
                else:
                    txt_surf = font_lyrics.render(line["text"], True, TEXT_MUTED)
                    
                screen.blit(txt_surf, (225, rel_y))

    # --- 4. BOTTOM PANEL (Visualizer & Smooth Controls) ---
    pygame.draw.line(screen, BORDER_COLOR, (0, 460), (WIDTH, 460), 1)
    
    # Visualizer Spektrum Muted Wave
    viz_ticks = pygame.time.get_ticks()
    for b in range(64):
        bar_w = WIDTH / 64
        amp = math.sin(viz_ticks * 0.008 + b * 0.25) * math.cos(viz_ticks * 0.004 + b * 0.12) if playing else 0.02
        amp_val = max(2, int(abs(amp) * 28))
        pygame.draw.rect(screen, (int(130 + amp_val * 3), 20, 80), (b * bar_w, 485 - amp_val, bar_w - 2, amp_val))

    # Timeline Bar
    pygame.draw.rect(screen, BORDER_COLOR, slider_prog, 0, 2)
    prog_pct = (cur_time / audio_duration) if audio_duration > 0 else 0.0
    prog_width = int(prog_pct * slider_prog.width)
    pygame.draw.rect(screen, NEON_PINK, (slider_prog.x, slider_prog.y, prog_width, slider_prog.height), 0, 2)
    pygame.draw.circle(screen, TEXT_MAIN, (slider_prog.x + prog_width, slider_prog.y + 3), 4)

    # Time Info
    screen.blit(font_small.render(fmt_time(cur_time), True, TEXT_MUTED), (13, 492))
    screen.blit(font_small.render(fmt_time(audio_duration), True, TEXT_MUTED), (WIDTH - 42, 492))

    # Play/Pause Icon
    is_play_hover = btn_play.collidepoint((mx, my))
    play_symbol = "  ▪" if playing else "  ▶"
    screen.blit(font_title.render(play_symbol, True, NEON_PINK if is_play_hover else TEXT_MAIN), (btn_play.x, btn_play.y + 2))

    # Volume Slider Clean
    screen.blit(font_small.render("VOL", True, TEXT_MUTED), (855, 523))
    pygame.draw.rect(screen, BORDER_COLOR, slider_vol, 0, 1)
    vol_width = int(volume * slider_vol.width)
    pygame.draw.rect(screen, NEON_PINK, (slider_vol.x, slider_vol.y, vol_width, slider_vol.height), 0, 1)
    pygame.draw.circle(screen, TEXT_MAIN, (slider_vol.x + vol_width, slider_vol.y + 2), 4)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
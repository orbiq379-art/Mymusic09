
# My Music — single-file Android-friendly Kivy music player
# Designed around the supplied clean white music-player reference.
#
# Recommended:
#   pip install kivy
#
# On Android/Pydroid, give the app/storage permission when prompted.
# This version uses only Kivy + Python standard library.

import os
import json
import random
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.graphics.vertex_instructions import Rectangle
from kivy.uix.image import Image


# ============================================================
# Theme
# ============================================================

BG = (0.965, 0.965, 0.955, 1)
WHITE = (1, 1, 1, 1)
BLACK = (0.035, 0.045, 0.055, 1)
TEXT = (0.08, 0.085, 0.095, 1)
MUTED = (0.48, 0.49, 0.50, 1)
LIGHT = (0.86, 0.865, 0.87, 1)
DARK_CARD = (0.055, 0.065, 0.08, 1)
ACCENT = (0.12, 0.13, 0.15, 1)

AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac"
}


# ============================================================
# Small UI helpers
# ============================================================

def clean_name(path):
    """Turn a filename into a nicer song title."""
    name = Path(path).stem
    name = name.replace("_", " ").replace("-", " ")
    return " ".join(name.split()).strip() or "Unknown Song"


def artist_from_path(path):
    """
    Lightweight metadata fallback without extra packages.
    Examples:
      Artist - Song.mp3 -> Artist
      Song.mp3          -> Local Music
    """
    name = Path(path).stem
    if " - " in name:
        return name.split(" - ", 1)[0].strip()
    return "Local Music"


class RoundedBox(BoxLayout):
    def __init__(self, bg=WHITE, radius=18, **kwargs):
        super().__init__(**kwargs)
        self.bg = bg
        self.radius = radius
        with self.canvas.before:
            Color(*bg)
            self.shape = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(radius)]
            )
        self.bind(pos=self._update, size=self._update)

    def _update(self, *_):
        self.shape.pos = self.pos
        self.shape.size = self.size


class RoundButton(Button):
    def __init__(self, bg=WHITE, fg=BLACK, radius=18, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = fg
        self.bg = bg
        self.radius = radius
        with self.canvas.before:
            Color(*bg)
            self.shape = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(radius)]
            )
        self.bind(pos=self._update, size=self._update)

    def _update(self, *_):
        self.shape.pos = self.pos
        self.shape.size = self.size


class IconButton(Button):
    """Clean vector icon button: no external icon package required."""
    def __init__(self, icon, size=42, **kwargs):
        super().__init__(**kwargs)
        self.text = icon
        self.font_size = 0
        self.size_hint = (None, None)
        self.size = (dp(size), dp(size))
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = TEXT
        self._icon = icon

        with self.canvas:
            Color(*TEXT)
            self._lines = []
            self._shapes = []
            self._build_icon()

        self.bind(pos=self._redraw, size=self._redraw, text=self._redraw)

    def _clear_icon(self):
        for obj in self._lines + self._shapes:
            try:
                self.canvas.remove(obj)
            except Exception:
                pass
        self._lines = []
        self._shapes = []

    def _line(self, points, width=1.8):
        obj = Line(points=points, width=dp(width),
                   cap='round', joint='round')
        self._lines.append(obj)
        return obj

    def _circle(self, x, y, r, width=1.8):
        obj = Line(circle=(x, y, r), width=dp(width))
        self._lines.append(obj)
        return obj

    def _filled_circle(self, x, y, r):
        obj = Ellipse(pos=(x-r, y-r), size=(2*r, 2*r))
        self._shapes.append(obj)
        return obj

    def _build_icon(self):
        self._clear_icon()
        icon = self.text
        x, y = self.pos
        w, h = self.size
        cx, cy = x + w/2, y + h/2
        c = self.color

        # All icons are deliberately simple, monochrome vector shapes.
        Color(*c)

        if icon == "⌂":  # home
            self._line([cx-10,cy-1, cx,cy+9, cx+10,cy-1])
            self._line([cx-7,cy-4, cx-7,cy-11, cx+7,cy-11, cx+7,cy-4])
            self._line([cx-2,cy-11,cx-2,cy-3,cx+2,cy-3,cx+2,cy-11])

        elif icon == "⌕":  # search
            self._circle(cx-2, cy+2, 7)
            self._line([cx+3,cy-3,cx+10,cy-10])

        elif icon == "▣":  # library
            self._line([cx-9,cy-9,cx-9,cy+9,cx+9,cy+9,cx+9,cy-9,cx-9,cy-9])
            self._line([cx-5,cy+4,cx+5,cy+4])
            self._line([cx-5,cy,cx+5,cy])
            self._line([cx-5,cy-4,cx+2,cy-4])

        elif icon == "◷":  # history
            self._circle(cx, cy, 9)
            self._line([cx,cy,cx,cy+5,cx+4,cy+7])
            self._line([cx-11,cy+2,cx-7,cy+2,cx-9,cy+6])

        elif icon == "⌄":  # down chevron
            self._line([cx-7,cy+3,cx,cy-4,cx+7,cy+3])

        elif icon == "☷":  # queue
            self._line([cx-8,cy+7,cx+8,cy+7])
            self._line([cx-8,cy,cx+8,cy])
            self._line([cx-8,cy-7,cx+8,cy-7])
            self._line([cx-8,cy+7,cx-8,cy+7])

        elif icon in ("♡", "♥"):  # heart
            # Smooth enough heart outline using connected line segments.
            pts = [
                cx,cy-9, cx-8,cy-3, cx-8,cy+3,
                cx,cy+10, cx+8,cy+3, cx+8,cy-3,
                cx,cy-9
            ]
            self._line(pts, 1.7)
            if icon == "♥":
                # Filled heart approximation.
                self._line([
                    cx,cy-7,cx-6,cy-2,cx-6,cy+2,
                    cx,cy+8,cx+6,cy+2,cx+6,cy-2,cx,cy-7
                ], 3.2)

        elif icon == "▶":  # play
            obj = Rectangle(
                pos=(cx-4,cy-8), size=(dp(11),dp(16))
            )
            # Replace rectangle with a triangle-like line.
            self.canvas.remove(obj)
            self._line([cx-5,cy-9,cx+8,cy,cx-5,cy+9,cx-5,cy-9], 2)

        elif icon == "⏸":  # pause
            self._line([cx-5,cy-8,cx-5,cy+8], 3)
            self._line([cx+5,cy-8,cx+5,cy+8], 3)

        elif icon in ("|◀", "⏮"):  # previous
            self._line([cx-8,cy-8,cx-8,cy+8], 2)
            self._line([cx-5,cy,cx+8,cy+8,cx+8,cy-8,cx-5,cy], 2)

        elif icon in ("▶|", "⏭"):  # next
            self._line([cx+8,cy-8,cx+8,cy+8], 2)
            self._line([cx+5,cy,cx-8,cy+8,cx-8,cy-8,cx+5,cy], 2)

        elif icon == "⤨":  # shuffle
            self._line([cx-9,cy+7,cx-3,cy+7,cx+7,cy-7,cx+10,cy-7])
            self._line([cx+6,cy-10,cx+10,cy-7,cx+6,cy-4])
            self._line([cx-9,cy-7,cx-3,cy-7,cx+1,cy-2])
            self._line([cx+5,cy+4,cx+10,cy+7])
            self._line([cx+6,cy+4,cx+10,cy+7,cx+6,cy+10])

        elif icon == "↻":  # repeat
            self._line([cx+7,cy-3,cx+7,cy+6,cx-7,cy+6,cx-7,cy+1])
            self._line([cx-10,cy+4,cx-7,cy+1,cx-4,cy+4])
            self._line([cx-7,cy+3,cx-7,cy-6,cx+7,cy-6,cx+7,cy-1])
            self._line([cx+10,cy-4,cx+7,cy-1,cx+4,cy-4])

        elif icon == "+":  # plus
            self._line([cx-8,cy,cx+8,cy], 2)
            self._line([cx,cy-8,cx,cy+8], 2)

        else:
            # Fallback: a small neutral dot, so missing icons never show
            # as tofu/square characters on Android.
            self._filled_circle(cx, cy, 3)

    def _redraw(self, *_):
        self._clear_icon()
        with self.canvas:
            Color(*self.color)
        self._build_icon()


class Artwork(FloatLayout):
    """
    Self-contained album artwork placeholder.
    A real artwork image can be added later without changing the player.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.055, 0.065, 0.08, 1)
            self.bg = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(24)]
            )
            Color(0.72, 0.73, 0.73, 1)
            self.leaf = Ellipse(
                pos=(0, 0), size=(0, 0)
            )
            Color(0.055, 0.065, 0.08, 1)
            self.vein = Line(points=[], width=dp(1.5))

        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        x, y = self.pos
        w, h = self.size
        self.bg.pos = self.pos
        self.bg.size = self.size

        s = min(w, h) * 0.42
        self.leaf.pos = (x + w * .50 - s/2, y + h * .51 - s/2)
        self.leaf.size = (s, s)

        # A few simple leaf veins create a monochrome album-art feel.
        cx, cy = x + w*.50, y + h*.51
        self.vein.points = [
            cx-s*.42, cy, cx+s*.42, cy,
            cx, cy-s*.42, cx, cy+s*.42,
            cx-s*.28, cy-s*.28, cx+s*.28, cy+s*.28,
            cx-s*.28, cy+s*.28, cx+s*.28, cy-s*.28
        ]


class Waveform(BoxLayout):
    """Lightweight animated-looking waveform made from canvas rectangles."""
    progress = NumericProperty(0.0)

    def __init__(self, bars=38, **kwargs):
        super().__init__(**kwargs)
        self.bars = bars
        self.values = [
            random.uniform(.15, .95) for _ in range(bars)
        ]
        self.bind(pos=self._draw, size=self._draw, progress=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        if self.width <= 1 or self.height <= 1:
            return

        gap = dp(3)
        bw = max(dp(2), (self.width - gap*(self.bars-1))/self.bars)
        for i, value in enumerate(self.values):
            x = self.x + i*(bw+gap)
            h = self.height * value
            y = self.y + (self.height-h)/2

            if i / max(1, self.bars-1) <= self.progress:
                Color(*BLACK)
            else:
                Color(0.82, 0.83, 0.84, 1)

            RoundedRectangle(
                pos=(x, y),
                size=(bw, h),
                radius=[dp(2)]
            )


# ============================================================
# Main application
# ============================================================

class MusicApp(App):
    title = "My Music"

    def build(self):
        Window.clearcolor = BG

        self.music = []
        self.favorites = set()
        self.history = []
        self.current_index = -1
        self.sound = None
        self.paused = False
        self.shuffle = False
        self.repeat = False
        self.duration = 0
        self.elapsed = 0
        self.volume = .9

        self.data_file = self._data_path()
        self.load_state()

        self.manager = ScreenManager()
        self.home = HomeScreen(name="home", app=self)
        self.library = LibraryScreen(name="library", app=self)
        self.search = SearchScreen(name="search", app=self)
        self.player_screen = NowPlayingScreen(name="player", app=self)

        self.manager.add_widget(self.home)
        self.manager.add_widget(self.library)
        self.manager.add_widget(self.search)
        self.manager.add_widget(self.player_screen)

        Clock.schedule_interval(self.update_player, .5)
        Clock.schedule_once(lambda *_: self.refresh_all(), .2)

        return self.manager

    def _data_path(self):
        try:
            base = Path(self.user_data_dir)
            base.mkdir(parents=True, exist_ok=True)
            return base / "library.json"
        except Exception:
            return Path("library.json")

    def load_state(self):
        try:
            if self.data_file.exists():
                data = json.loads(self.data_file.read_text(encoding="utf-8"))
                self.music = data.get("music", [])
                self.favorites = set(data.get("favorites", []))
                self.history = data.get("history", [])
                self.volume = float(data.get("volume", .9))
        except Exception:
            self.music = []
            self.favorites = set()
            self.history = []

    def save_state(self):
        try:
            data = {
                "music": self.music,
                "favorites": list(self.favorites),
                "history": self.history[:30],
                "volume": self.volume,
            }
            self.data_file.write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    # --------------------------
    # Library
    # --------------------------

    def add_files(self, files):
        changed = False
        for path in files:
            if not path:
                continue
            path = os.path.abspath(path)
            if Path(path).suffix.lower() in AUDIO_EXTENSIONS and path not in self.music:
                self.music.append(path)
                changed = True

        if changed:
            self.save_state()
            self.refresh_all()

    def remove_missing(self):
        before = len(self.music)
        self.music = [p for p in self.music if os.path.exists(p)]
        if len(self.music) != before:
            self.save_state()
            self.refresh_all()

    def refresh_all(self):
        self.remove_missing()
        self.home.refresh()
        self.library.refresh()
        self.search.refresh()
        self.player_screen.refresh()

    def open_file_picker(self, *_):
        music_root = "/storage/emulated/0/Music"
        if not os.path.exists(music_root):
            music_root = "/storage/emulated/0"
        if not os.path.exists(music_root):
            music_root = os.getcwd()

        chooser = FileChooserListView(
            path=music_root,
            filters=["*.mp3", "*.wav", "*.ogg", "*.m4a", "*.aac", "*.flac"],
            multiselect=True
        )

        root = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        root.add_widget(chooser)

        buttons = BoxLayout(
            size_hint_y=None, height=dp(54), spacing=dp(10)
        )
        cancel = RoundButton(text="Cancel", bg=LIGHT, size_hint_x=.4)
        add = RoundButton(text="Add Selected Songs", bg=BLACK, fg=WHITE)

        buttons.add_widget(cancel)
        buttons.add_widget(add)
        root.add_widget(buttons)

        popup = Popup(
            title="Choose music from your phone",
            content=root,
            size_hint=(.96, .92),
            separator_color=LIGHT
        )

        cancel.bind(on_release=popup.dismiss)

        def finish(_):
            self.add_files(chooser.selection)
            popup.dismiss()

        add.bind(on_release=finish)
        popup.open()

    # --------------------------
    # Playback
    # --------------------------

    def play(self, index):
        if not self.music:
            return

        if index < 0 or index >= len(self.music):
            return

        path = self.music[index]

        try:
            if self.sound:
                self.sound.stop()

            self.sound = SoundLoader.load(path)
            if not self.sound:
                self.home.show_message("This audio format could not be played.")
                return

            self.sound.volume = self.volume
            self.sound.play()

            self.current_index = index
            self.paused = False
            self.elapsed = 0
            self.duration = self.sound.length or 0

            if path in self.history:
                self.history.remove(path)
            self.history.insert(0, path)
            self.history = self.history[:30]

            self.save_state()
            self.refresh_all()

            self.manager.current = "player"

        except Exception as exc:
            self.home.show_message("Couldn't play this file.")

    def toggle_play(self, *_):
        if not self.sound:
            if self.music:
                self.play(0)
            return

        try:
            if self.paused:
                self.sound.play()
                self.paused = False
            else:
                self.sound.stop()
                self.paused = True
        except Exception:
            pass

        self.refresh_all()

    def next_song(self, *_):
        if not self.music:
            return

        if self.shuffle and len(self.music) > 1:
            choices = [i for i in range(len(self.music))
                       if i != self.current_index]
            index = random.choice(choices)
        else:
            index = (self.current_index + 1) % len(self.music)

        self.play(index)

    def previous_song(self, *_):
        if not self.music:
            return

        # If we're more than 3 seconds in, restart the song.
        if self.sound and self.elapsed > 3:
            self.seek(0)
            return

        index = self.current_index - 1
        if index < 0:
            index = len(self.music) - 1
        self.play(index)

    def toggle_shuffle(self, *_):
        self.shuffle = not self.shuffle
        self.refresh_all()

    def toggle_repeat(self, *_):
        self.repeat = not self.repeat
        self.refresh_all()

    def toggle_favorite(self, *_):
        if self.current_index < 0:
            return
        path = self.music[self.current_index]
        if path in self.favorites:
            self.favorites.remove(path)
        else:
            self.favorites.add(path)
        self.save_state()
        self.refresh_all()

    def seek(self, value):
        if not self.sound or not self.duration:
            return
        try:
            self.sound.seek(max(0, min(float(value), self.duration)))
        except Exception:
            pass

    def set_volume(self, value):
        self.volume = float(value)
        if self.sound:
            self.sound.volume = self.volume
        self.save_state()

    def update_player(self, _dt):
        if not self.sound or self.paused:
            return

        try:
            pos = self.sound.get_pos()
            if pos >= 0:
                self.elapsed = pos

            if self.duration <= 0:
                self.duration = self.sound.length or 0

            # Kivy's audio backends can return -1 at end.
            finished = (
                self.duration > 0 and
                self.elapsed >= self.duration - .15
            )

            if finished:
                if self.repeat:
                    self.play(self.current_index)
                else:
                    self.next_song()

            self.player_screen.update_progress()
            self.home.update_mini()
            self.library.update_mini()
            self.search.update_mini()

        except Exception:
            pass

    # --------------------------
    # Navigation
    # --------------------------

    def go(self, screen):
        self.manager.current = screen

    def current_title(self):
        if 0 <= self.current_index < len(self.music):
            return clean_name(self.music[self.current_index])
        return "Nothing playing"

    def current_artist(self):
        if 0 <= self.current_index < len(self.music):
            return artist_from_path(self.music[self.current_index])
        return "Your music"

    def is_favorite(self):
        if 0 <= self.current_index < len(self.music):
            return self.music[self.current_index] in self.favorites
        return False


# ============================================================
# Shared navigation / mini player
# ============================================================

class BaseScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

    def nav_bar(self):
        bar = BoxLayout(
            size_hint_y=None, height=dp(68),
            padding=(dp(12), dp(5)), spacing=dp(3)
        )

        items = [
            ("⌂", "Home", "home"),
            ("⌕", "Search", "search"),
            ("▣", "Library", "library"),
            ("◷", "History", None),
        ]

        for icon, text, target in items:
            b = Button(
                text=f"{icon}\n{text}",
                font_size=dp(11),
                background_normal="",
                background_color=(0,0,0,0),
                color=TEXT
            )
            if target:
                b.bind(on_release=lambda _, s=target: self.app.go(s))
            else:
                b.bind(on_release=self.show_history)
            bar.add_widget(b)

        return bar

    def show_history(self, *_):
        self.app.go("library")
        Clock.schedule_once(
            lambda __: self.app.library.show_history_only(), .05
        )

    def mini_player(self):
        root = RoundedBox(
            bg=DARK_CARD, radius=17,
            size_hint_y=None, height=dp(62),
            padding=(dp(12), dp(7))
        )

        art = Artwork(size_hint_x=None, width=dp(48))
        root.add_widget(art)

        info = BoxLayout(
            orientation="vertical",
            padding=(dp(10), 0)
        )

        self.mini_title = Label(
            text=self.app.current_title(),
            color=WHITE,
            font_size=dp(13),
            halign="left",
            valign="middle"
        )
        self.mini_artist = Label(
            text=self.app.current_artist(),
            color=(.67,.68,.70,1),
            font_size=dp(10),
            halign="left"
        )
        info.add_widget(self.mini_title)
        info.add_widget(self.mini_artist)
        root.add_widget(info)

        heart = IconButton("♡", size=42)
        heart.color = WHITE
        heart.bind(on_release=lambda *_: self.app.toggle_favorite())
        root.add_widget(heart)

        play = IconButton("⏸" if self.app.sound and not self.app.paused else "▶", size=42)
        play.color = WHITE
        play.bind(on_release=lambda *_: self.app.toggle_play())
        root.add_widget(play)

        root.bind(on_touch_up=self._mini_touch)
        self._mini_play = play
        return root

    def _mini_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.app.go("player")

    def update_mini(self):
        if hasattr(self, "mini_title"):
            self.mini_title.text = self.app.current_title()
            self.mini_artist.text = self.app.current_artist()
        if hasattr(self, "_mini_play"):
            self._mini_play.text = (
                "⏸" if self.app.sound and not self.app.paused else "▶"
            )


# ============================================================
# Home
# ============================================================

class HomeScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root = BoxLayout(
            orientation="vertical",
            padding=(dp(18), dp(10), dp(18), dp(4)),
            spacing=dp(10)
        )

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(54))
        logo = Label(
            text="[b]My Music[/b]",
            markup=True, font_size=dp(25),
            color=TEXT, halign="left"
        )
        header.add_widget(logo)
        search = IconButton("⌕", size=44)
        search.bind(on_release=lambda *_: self.app.go("search"))
        header.add_widget(search)
        self.root.add_widget(header)

        # Welcome card
        card = RoundedBox(
            bg=(.93,.93,.91,1), radius=22,
            size_hint_y=None, height=dp(122),
            padding=dp(17)
        )

        art = Artwork(size_hint_x=None, width=dp(88))
        card.add_widget(art)

        welcome = BoxLayout(orientation="vertical", padding=(dp(14), dp(5)))
        welcome.add_widget(Label(
            text="[b]Your music.[/b]",
            markup=True, color=TEXT,
            font_size=dp(21), halign="left"
        ))
        welcome.add_widget(Label(
            text="Offline • Private • Yours",
            color=MUTED, font_size=dp(12), halign="left"
        ))
        add = RoundButton(
            text="+ Add music",
            bg=BLACK, fg=WHITE, radius=13,
            size_hint=(None,None), size=(dp(125), dp(36))
        )
        add.bind(on_release=self.app.open_file_picker)
        welcome.add_widget(add)
        card.add_widget(welcome)
        self.root.add_widget(card)

        section = BoxLayout(size_hint_y=None, height=dp(40))
        section.add_widget(Label(
            text="[b]Recently Played[/b]",
            markup=True, color=TEXT, font_size=dp(18), halign="left"
        ))
        see = Button(
            text="See all", background_normal="",
            background_color=(0,0,0,0), color=MUTED,
            size_hint_x=None, width=dp(75)
        )
        see.bind(on_release=lambda *_: self.app.go("library"))
        section.add_widget(see)
        self.root.add_widget(section)

        self.scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(2)
        )
        self.recent_box = GridLayout(
            cols=1, spacing=dp(6),
            size_hint_y=None
        )
        self.recent_box.bind(
            minimum_height=self.recent_box.setter("height")
        )
        self.scroll.add_widget(self.recent_box)
        self.root.add_widget(self.scroll)

        self.mini = self.mini_player()
        self.root.add_widget(self.mini)
        self.root.add_widget(self.nav_bar())

        self.add_widget(self.root)

    def refresh(self):
        self.recent_box.clear_widgets()

        paths = []
        for p in self.app.history:
            if p in self.app.music and p not in paths:
                paths.append(p)

        if not paths:
            paths = self.app.music[:8]

        if not paths:
            self.recent_box.add_widget(Label(
                text="No songs yet.\nTap “Add music” to choose songs from your phone.",
                color=MUTED, font_size=dp(14),
                size_hint_y=None, height=dp(80),
                halign="center"
            ))
            return

        for path in paths[:10]:
            self.recent_box.add_widget(
                self.song_row(path, self.app.music.index(path))
            )

    def song_row(self, path, index):
        row = BoxLayout(
            size_hint_y=None, height=dp(62),
            spacing=dp(10)
        )

        art = Artwork(size_hint_x=None, width=dp(52))
        row.add_widget(art)

        info = BoxLayout(orientation="vertical")
        info.add_widget(Label(
            text=clean_name(path),
            color=TEXT, font_size=dp(14),
            halign="left", valign="middle"
        ))
        info.add_widget(Label(
            text=artist_from_path(path),
            color=MUTED, font_size=dp(11),
            halign="left"
        ))
        row.add_widget(info)

        play = IconButton("▶", size=42)
        play.bind(on_release=lambda *_: self.app.play(index))
        row.add_widget(play)

        return row

    def update_mini(self):
        super().update_mini()

    def show_message(self, text):
        Popup(
            title="My Music",
            content=Label(text=text, color=TEXT),
            size_hint=(.85, .3)
        ).open()


# ============================================================
# Library
# ============================================================

class LibraryScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history_only = False

        self.root = BoxLayout(
            orientation="vertical",
            padding=(dp(18), dp(10), dp(18), dp(4)),
            spacing=dp(8)
        )

        header = BoxLayout(size_hint_y=None, height=dp(54))
        header.add_widget(Label(
            text="[b]Library[/b]",
            markup=True, color=TEXT, font_size=dp(25),
            halign="left"
        ))
        add = IconButton("+", size=44)
        add.bind(on_release=self.app.open_file_picker)
        header.add_widget(add)
        self.root.add_widget(header)

        self.tabs = BoxLayout(
            size_hint_y=None, height=dp(42), spacing=dp(6)
        )

        for title, mode in [
            ("Songs", "songs"),
            ("Albums", "albums"),
            ("Favorites", "favorites"),
            ("History", "history")
        ]:
            b = RoundButton(
                text=title,
                bg=WHITE, fg=TEXT, radius=12
            )
            b.bind(
                on_release=lambda _, m=mode: self.set_mode(m)
            )
            self.tabs.add_widget(b)

        self.root.add_widget(self.tabs)

        self.scroll = ScrollView(do_scroll_x=False)
        self.list_box = GridLayout(
            cols=1, spacing=dp(5),
            size_hint_y=None
        )
        self.list_box.bind(
            minimum_height=self.list_box.setter("height")
        )
        self.scroll.add_widget(self.list_box)
        self.root.add_widget(self.scroll)

        self.mini = self.mini_player()
        self.root.add_widget(self.mini)
        self.root.add_widget(self.nav_bar())

        self.add_widget(self.root)

    def set_mode(self, mode):
        self.history_only = mode == "history"
        self.refresh(mode)

    def show_history_only(self):
        self.set_mode("history")

    def refresh(self, mode="songs"):
        self.list_box.clear_widgets()

        if mode == "history":
            paths = [p for p in self.app.history if p in self.app.music]
        elif mode == "favorites":
            paths = [p for p in self.app.music if p in self.app.favorites]
        else:
            paths = list(self.app.music)

        if mode == "albums":
            # Simple album grouping based on folder name.
            groups = {}
            for p in self.app.music:
                album = Path(p).parent.name or "Music"
                groups.setdefault(album, []).append(p)

            if not groups:
                self.empty()
                return

            for album, items in sorted(groups.items()):
                self.album_row(album, items)
            return

        if not paths:
            self.empty()
            return

        for p in paths:
            self.list_box.add_widget(
                self.song_row(p, self.app.music.index(p))
            )

    def empty(self):
        self.list_box.add_widget(Label(
            text="Nothing here yet.",
            color=MUTED, font_size=dp(15),
            size_hint_y=None, height=dp(90)
        ))

    def album_row(self, album, items):
        row = RoundedBox(
            bg=WHITE, radius=15,
            size_hint_y=None, height=dp(78),
            padding=dp(8)
        )
        art = Artwork(size_hint_x=None, width=dp(60))
        row.add_widget(art)

        info = BoxLayout(orientation="vertical", padding=(dp(10),0))
        info.add_widget(Label(
            text=album, color=TEXT, font_size=dp(15),
            halign="left"
        ))
        info.add_widget(Label(
            text=f"{len(items)} song" + ("s" if len(items) != 1 else ""),
            color=MUTED, font_size=dp(11), halign="left"
        ))
        row.add_widget(info)

        play = IconButton("▶", size=42)
        play.bind(
            on_release=lambda *_: self.app.play(
                self.app.music.index(items[0])
            )
        )
        row.add_widget(play)

        self.list_box.add_widget(row)

    def song_row(self, path, index):
        row = BoxLayout(
            size_hint_y=None, height=dp(64), spacing=dp(9)
        )

        art = Artwork(size_hint_x=None, width=dp(52))
        row.add_widget(art)

        info = BoxLayout(orientation="vertical")
        info.add_widget(Label(
            text=clean_name(path), color=TEXT,
            font_size=dp(14), halign="left"
        ))
        info.add_widget(Label(
            text=artist_from_path(path), color=MUTED,
            font_size=dp(11), halign="left"
        ))
        row.add_widget(info)

        heart = IconButton(
            "♥" if path in self.app.favorites else "♡", size=38
        )
        heart.bind(
            on_release=lambda *_,
            p=path: self.toggle_favorite_for(p)
        )
        row.add_widget(heart)

        play = IconButton("▶", size=38)
        play.bind(on_release=lambda *_: self.app.play(index))
        row.add_widget(play)

        return row

    def toggle_favorite_for(self, path):
        if path in self.app.favorites:
            self.app.favorites.remove(path)
        else:
            self.app.favorites.add(path)
        self.app.save_state()
        self.refresh("favorites" if self.history_only is False else "songs")

    def update_mini(self):
        super().update_mini()


# ============================================================
# Search
# ============================================================

class SearchScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root = BoxLayout(
            orientation="vertical",
            padding=(dp(18), dp(10), dp(18), dp(4)),
            spacing=dp(8)
        )

        header = BoxLayout(size_hint_y=None, height=dp(54))
        header.add_widget(Label(
            text="[b]Search[/b]", markup=True,
            color=TEXT, font_size=dp(25), halign="left"
        ))
        self.root.add_widget(header)

        from kivy.uix.textinput import TextInput

        self.input = TextInput(
            hint_text="Songs, artists, albums...",
            multiline=False,
            size_hint_y=None,
            height=dp(48),
            padding=(dp(15), dp(12)),
            foreground_color=TEXT,
            background_color=WHITE,
            cursor_color=TEXT
        )
        self.input.bind(text=lambda *_: self.refresh())
        self.root.add_widget(self.input)

        self.scroll = ScrollView(do_scroll_x=False)
        self.results = GridLayout(
            cols=1, spacing=dp(5), size_hint_y=None
        )
        self.results.bind(
            minimum_height=self.results.setter("height")
        )
        self.scroll.add_widget(self.results)
        self.root.add_widget(self.scroll)

        self.mini = self.mini_player()
        self.root.add_widget(self.mini)
        self.root.add_widget(self.nav_bar())

        self.add_widget(self.root)

    def refresh(self):
        if not hasattr(self, "results"):
            return

        self.results.clear_widgets()
        q = self.input.text.strip().lower() if hasattr(self, "input") else ""

        matches = []
        for p in self.app.music:
            searchable = (
                clean_name(p) + " " +
                artist_from_path(p) + " " +
                str(Path(p).parent.name)
            ).lower()
            if not q or q in searchable:
                matches.append(p)

        if not matches:
            self.results.add_widget(Label(
                text="No matching songs.",
                color=MUTED, size_hint_y=None, height=dp(80)
            ))
            return

        for p in matches:
            index = self.app.music.index(p)
            row = BoxLayout(
                size_hint_y=None, height=dp(64), spacing=dp(9)
            )
            row.add_widget(Artwork(size_hint_x=None, width=dp(52)))

            info = BoxLayout(orientation="vertical")
            info.add_widget(Label(
                text=clean_name(p), color=TEXT,
                font_size=dp(14), halign="left"
            ))
            info.add_widget(Label(
                text=artist_from_path(p), color=MUTED,
                font_size=dp(11), halign="left"
            ))
            row.add_widget(info)

            b = IconButton("▶", size=42)
            b.bind(on_release=lambda _, i=index: self.app.play(i))
            row.add_widget(b)

            self.results.add_widget(row)

    def update_mini(self):
        super().update_mini()


# ============================================================
# Now Playing
# ============================================================

class NowPlayingScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root = BoxLayout(
            orientation="vertical",
            padding=(dp(18), dp(8), dp(18), dp(18)),
            spacing=dp(10)
        )

        header = BoxLayout(size_hint_y=None, height=dp(50))
        back = IconButton("⌄", size=44)
        back.bind(on_release=lambda *_: self.app.go("home"))
        header.add_widget(back)

        header.add_widget(Label(
            text="[b]Now Playing[/b]", markup=True,
            color=TEXT, font_size=dp(17), halign="center"
        ))

        queue = IconButton("☷", size=44)
        header.add_widget(queue)
        self.root.add_widget(header)

        self.art = Artwork(size_hint_y=None, height=dp(315))
        self.root.add_widget(self.art)

        title_box = BoxLayout(
            size_hint_y=None, height=dp(70)
        )
        names = BoxLayout(orientation="vertical")
        self.title_label = Label(
            text="Nothing playing",
            color=TEXT, font_size=dp(28),
            halign="left", valign="middle"
        )
        self.artist_label = Label(
            text="Your music",
            color=MUTED, font_size=dp(15),
            halign="left"
        )
        names.add_widget(self.title_label)
        names.add_widget(self.artist_label)
        title_box.add_widget(names)

        self.heart = IconButton("♡", size=50)
        self.heart.bind(on_release=lambda *_: self.app.toggle_favorite())
        title_box.add_widget(self.heart)
        self.root.add_widget(title_box)

        self.wave = Waveform(
            size_hint_y=None, height=dp(58)
        )
        self.root.add_widget(self.wave)

        times = BoxLayout(
            size_hint_y=None, height=dp(22)
        )
        self.current_time = Label(
            text="0:00", color=MUTED,
            font_size=dp(10), halign="left"
        )
        self.total_time = Label(
            text="0:00", color=MUTED,
            font_size=dp(10), halign="right"
        )
        times.add_widget(self.current_time)
        times.add_widget(self.total_time)
        self.root.add_widget(times)

        # Actual seek slider, visually kept subtle.
        self.seek_slider = Slider(
            min=0, max=1, value=0,
            size_hint_y=None, height=dp(8)
        )
        self.seek_slider.bind(
            on_touch_up=self.on_seek_touch
        )
        self.root.add_widget(self.seek_slider)

        controls = BoxLayout(
            size_hint_y=None, height=dp(78),
            spacing=dp(8)
        )

        self.shuffle_btn = IconButton("⤨", size=48)
        self.shuffle_btn.bind(on_release=lambda *_: self.app.toggle_shuffle())

        prev = IconButton("|◀", size=50)
        prev.bind(on_release=lambda *_: self.app.previous_song())

        self.play_btn = RoundButton(
            text="▶",
            bg=BLACK, fg=WHITE, radius=50,
            size_hint=(None,None), size=(dp(70), dp(70)),
            font_size=dp(27)
        )
        self.play_btn.bind(on_release=lambda *_: self.app.toggle_play())

        nxt = IconButton("▶|", size=50)
        nxt.bind(on_release=lambda *_: self.app.next_song())

        self.repeat_btn = IconButton("↻", size=48)
        self.repeat_btn.bind(on_release=lambda *_: self.app.toggle_repeat())

        controls.add_widget(self.shuffle_btn)
        controls.add_widget(prev)
        controls.add_widget(self.play_btn)
        controls.add_widget(nxt)
        controls.add_widget(self.repeat_btn)

        self.root.add_widget(controls)

        self.volume = Slider(
            min=0, max=1, value=.9,
            size_hint_y=None, height=dp(25)
        )
        self.volume.bind(value=lambda _, v: self.app.set_volume(v))
        self.root.add_widget(self.volume)

        self.add_widget(self.root)

    def on_seek_touch(self, slider, touch):
        if slider.collide_point(*touch.pos):
            self.app.seek(slider.value)

    def update_progress(self):
        if not self.app.sound:
            return

        duration = self.app.duration or 0
        elapsed = max(0, self.app.elapsed)

        self.title_label.text = self.app.current_title()
        self.artist_label.text = self.app.current_artist()
        self.heart.text = "♥" if self.app.is_favorite() else "♡"

        self.play_btn.text = (
            "⏸" if not self.app.paused else "▶"
        )

        self.shuffle_btn.color = TEXT if not self.app.shuffle else MUTED
        self.repeat_btn.color = TEXT if not self.app.repeat else MUTED

        self.current_time.text = format_time(elapsed)
        self.total_time.text = format_time(duration)

        if duration > 0:
            self.seek_slider.value = min(1, elapsed/duration)
            self.wave.progress = min(1, elapsed/duration)

        self.volume.value = self.app.volume

    def refresh(self):
        self.update_progress()


def format_time(seconds):
    try:
        seconds = int(max(0, seconds))
    except Exception:
        return "0:00"
    return f"{seconds//60}:{seconds%60:02d}"


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    MusicApp().run()

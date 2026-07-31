import os
import json
import uuid
import random
import pygame
import time
import math
from dataclasses import dataclass, field
from enum import Enum, auto

from play_logger import PlayLogger

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# このスクリプトファイル自身があるフォルダを基準にする。
# (相対パスのままだと、実行時のカレントディレクトリによって
#  音声ファイルが見つからず無音になることがあるための対策)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------------
# 基本設定
# ----------------------------
# 音声バッファを小さくして、再生の遅延(反応の遅さ)を減らす。
# pre_init は pygame.init() より前に呼ぶ必要がある。
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=256)
pygame.init()
try:
    pygame.mixer.init()
    HAS_AUDIO = True
except pygame.error as e:
    HAS_AUDIO = False
    print(f"[audio] mixerの初期化に失敗しました: {e}")

WIDTH = 1000
HEIGHT = 600
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("English Rhythm Game")

clock = pygame.time.Clock()


def load_font(size: int) -> pygame.font.Font:
    """環境にarialがなくても落ちないようにフォールバックする。"""
    try:
        return pygame.font.SysFont("arial", size)
    except Exception:
        return pygame.font.Font(None, size)


font = load_font(42)
small_font = load_font(30)
large_font = load_font(64)


# 色
BACKGROUND = (25, 28, 40)
NORMAL_COLOR = (220, 220, 220)
ACTIVE_COLOR = (255, 215, 80)
HIT_COLOR = (80, 220, 140)
GOOD_COLOR = (255, 215, 80)
MISS_COLOR = (230, 80, 80)
LANE_COLOR = (60, 64, 82)
HIT_LINE_COLOR = (140, 145, 170)

# 判定・見た目のタイミング設定
TRAVEL_TIME = 1.4          # ノーツが降ってくるのにかかる秒数
PERFECT_WINDOW = 0.15
GOOD_WINDOW = 0.30
MISS_GRACE = 0.35          # このタイミングを過ぎたら自動でMISS扱い

LANE_X = WIDTH // 2
LANE_TOP_Y = 60
HIT_LINE_Y = HEIGHT - 160
NOTE_RADIUS = 22

STAGES_PER_CHECKPOINT = 10  # この数ごとに「続ける/ここで終わる」を選べる

# ----------------------------
# 難易度設定
#   highlight_window : 単語がハイライトされる、正解タイミング前後の許容秒数
#   show_highlight   : Falseなら一切ハイライトしない(音声だけが頼り)
# ----------------------------
DIFFICULTIES = {
    "EASY":   {"label": "Easy",   "highlight_window": 0.4,  "show_highlight": True,  "show_notes": True},
    "NORMAL": {"label": "Normal", "highlight_window": 0.12, "show_highlight": True,  "show_notes": True},
    "HARD":   {"label": "Hard",   "highlight_window": 0.0,  "show_highlight": False, "show_notes": False},
}
DIFFICULTY_ORDER = ["EASY", "NORMAL", "HARD"]


# ----------------------------
# 背景グラフィック(単色塗りつぶしの代わりに、グラデーション+星を1枚のSurfaceに事前描画しておく)
# ----------------------------
def make_background_surface(width: int, height: int, top_color, bottom_color) -> pygame.Surface:
    surf = pygame.Surface((width, height))
    for y in range(height):
        ratio = y / height
        color = tuple(
            int(top_color[i] + (bottom_color[i] - top_color[i]) * ratio) for i in range(3)
        )
        pygame.draw.line(surf, color, (0, y), (width, y))

    rng = random.Random(42)  # 毎回同じ星の配置になるように固定シード
    for _ in range(90):
        x = rng.randint(0, width - 1)
        y = rng.randint(0, height - 1)
        shade = rng.randint(50, 90)
        size = rng.choice([1, 1, 1, 2])
        pygame.draw.circle(surf, (shade, shade, shade + 15), (x, y), size)

    return surf


BACKGROUND_SURFACE = make_background_surface(WIDTH, HEIGHT, (16, 18, 30), (34, 38, 58))


# ----------------------------
# 効果音(numpyで簡易生成、無ければ無音)
# ----------------------------
def make_beep(freq: float, duration: float = 0.12, volume: float = 0.4):
    if not (HAS_AUDIO and HAS_NUMPY):
        return None
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, False)
    wave = np.sin(freq * t * 2 * math.pi)
    # フェードアウトしてプチノイズを防ぐ
    fade = np.linspace(1, 0, n_samples)
    wave = wave * fade * volume
    stereo = np.column_stack((wave, wave))
    audio = (stereo * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(audio)


SOUND_PERFECT = make_beep(880)
SOUND_GOOD = make_beep(660)
SOUND_MISS = make_beep(220, duration=0.18)


# ----------------------------
# BGM(numpyでシンプルなループ音楽を生成する。外部の音楽ファイルは不要)
# ----------------------------
def make_bgm_loop(sample_rate: int = 44100):
    """
    落ち着いたアルペジオ(分散和音)を繰り返すだけの、シンプルなループBGMを作る。
    曲を追加/変えたい場合は CHORD_PROGRESSION を書き換えれば雰囲気を変えられる。
    """
    if not (HAS_AUDIO and HAS_NUMPY):
        return None

    tempo_bpm = 92
    note_duration = 60 / tempo_bpm / 2  # 8分音符の長さ

    # C - Am - F - G のコード進行を、それぞれ分散和音(アルペジオ)で鳴らす
    CHORD_PROGRESSION = [
        [261.63, 329.63, 392.00, 329.63],  # C  (ド ミ ソ ミ)
        [220.00, 261.63, 329.63, 261.63],  # Am (ラ ド ミ ド)
        [174.61, 220.00, 261.63, 220.00],  # F  (ファ ラ ド ラ)
        [196.00, 246.94, 293.66, 246.94],  # G  (ソ シ レ シ)
    ]

    def note_wave(freq: float, duration: float, volume: float = 0.18):
        n = max(int(sample_rate * duration), 1)
        t = np.linspace(0, duration, n, False)
        wave = np.sin(freq * t * 2 * math.pi)
        # 短い立ち上がり/立ち下がりを付けてプチノイズを防ぐ
        attack = max(int(n * 0.08), 1)
        release = max(int(n * 0.25), 1)
        envelope = np.ones(n)
        envelope[:attack] = np.linspace(0, 1, attack)
        envelope[-release:] *= np.linspace(1, 0, release)
        return wave * envelope * volume

    segments = []
    for chord in CHORD_PROGRESSION:
        for freq in chord:
            segments.append(note_wave(freq, note_duration))

    loop = np.concatenate(segments)
    stereo = np.column_stack((loop, loop))
    audio = (stereo * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(audio)


BGM_VOLUME = 0.25  # 歌詞(英文の読み上げ)の邪魔にならないよう控えめに
BGM_SOUND = make_bgm_loop()

if HAS_AUDIO:
    # 効果音(SOUND_PERFECTなど)が自動でこのチャンネルを使わないよう予約しておく
    pygame.mixer.set_reserved(1)
    BGM_CHANNEL = pygame.mixer.Channel(0)
    if BGM_SOUND is not None:
        BGM_CHANNEL.set_volume(BGM_VOLUME)
        BGM_CHANNEL.play(BGM_SOUND, loops=-1)
else:
    BGM_CHANNEL = None


def play_sound(sound) -> None:
    if sound is not None:
        sound.play()


# ----------------------------
# データ構造
# ----------------------------
@dataclass
class Target:
    word: str
    beat_time: float
    word_index: int = -1  # 文中の何番目の単語か(同じ単語が複数あるときの区別に使う)
    judged: bool = False
    result: str = ""


@dataclass
class WordCue:
    """generate_stage_audio.py が作った、単語ごとの再生スケジュール。"""
    word_index: int
    audio_path: str      # 解決済みの絶対パス
    start_time: float     # ゲーム内経過時間で何秒に再生するか
    played: bool = False
    sound: object = None  # 読み込み済みの pygame.mixer.Sound


@dataclass
class Stage:
    name: str
    sentence_words: list
    targets: list = field(default_factory=list)
    audio_file: str = ""       # 1本の音声ファイル(文章まるごと)のパス
    audio_offset: float = 0.0  # 音声とゲーム内タイマーがずれる場合に秒単位で補正
    word_cues: list = field(default_factory=list)  # (単語ごとに個別音声を使う場合。通常は空)
    duration: float = 0.0      # 音声ファイル全体の長さ(秒)。最後まで再生し切るために使う
    audio_start_delay: float = 0.0  # ステージ開始から実際に音声を鳴らし始めるまでの待ち時間(秒)


class GameState(Enum):
    START = auto()
    PLAYING = auto()
    PAUSED = auto()
    STAGE_CLEAR = auto()
    CHECKPOINT = auto()  # 10ステージごとの節目。続けるか、ここで終えるか選べる
    FINISHED = auto()


# ----------------------------
# ステージデータ(3ステージ、後半ほどタイトに)
# 生成済みの stages.json があればそちらを優先して読み込む
# (generate_stage_audio.py で音声とタイミングを自動生成した場合)
# ----------------------------
FALLBACK_STAGES = [
    Stage(
        name="Stage 1",
        sentence_words=["The", "QUICK", "brown", "FOX", "jumps", "OVER", "the", "LAZY", "dog."],
        targets=[
            Target("QUICK", 1.2, word_index=1),
            Target("FOX", 2.4, word_index=3),
            Target("OVER", 3.6, word_index=5),
            Target("LAZY", 4.8, word_index=7),
        ],
        # 用意した音声ファイルをここに指定(ファイル名はご自身の音声に合わせて変更してください)
        audio_file="assets/stage1.mp3",
        audio_offset=0.0,
    ),
    Stage(
        name="Stage 2",
        sentence_words=["SHE", "sells", "SEA", "shells", "by", "the", "SEA", "shore"],
        targets=[
            Target("SHE", 1.0, word_index=0),
            Target("SEA", 1.9, word_index=2),   # 1つ目のSEA
            Target("SEA", 2.8, word_index=6),   # 2つ目のSEA(位置で区別)
        ],
        audio_file="assets/stage2.mp3",
        audio_offset=0.0,
    ),
    Stage(
        name="Stage 3",
        sentence_words=["PETER", "Piper", "PICKED", "a", "PECK", "of", "PICKLED", "peppers"],
        targets=[
            Target("PETER", 0.8, word_index=0),
            Target("PICKED", 1.5, word_index=2),
            Target("PECK", 2.2, word_index=4),
            Target("PICKLED", 2.9, word_index=6),
        ],
        audio_file="assets/stage3.mp3",
        audio_offset=0.0,
    ),
]


def load_stages() -> list:
    """
    stages.json (generate_stage_audio.py が生成) があればそれを読み込み、
    無ければ手入力のFALLBACK_STAGESを使う。
    """
    json_path = os.path.join(BASE_DIR, "stages.json")
    if not os.path.isfile(json_path):
        return FALLBACK_STAGES

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        stages = []
        for s in data:
            targets = [
                Target(t["word"], t["beat_time"], word_index=t["word_index"])
                for t in s["targets"]
            ]

            word_cues = []
            for w in s.get("words", []):
                raw_path = w["audio_file"]
                abs_path = raw_path if os.path.isabs(raw_path) else os.path.join(BASE_DIR, raw_path)
                word_cues.append(
                    WordCue(
                        word_index=w["word_index"],
                        audio_path=abs_path,
                        start_time=w["start_time"],
                    )
                )

            stages.append(
                Stage(
                    name=s["name"],
                    sentence_words=s["sentence_words"],
                    targets=targets,
                    audio_file=s.get("audio_file", ""),
                    audio_offset=s.get("audio_offset", 0.0),
                    word_cues=word_cues,
                    duration=s.get("duration", 0.0),
                    audio_start_delay=s.get("audio_start_delay", 0.0),
                )
            )
        print(f"[stage] stages.json を読み込みました({len(stages)}ステージ)")
        return stages
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"[stage] stages.jsonの読み込みに失敗したため手入力データを使います: {e}")
        return FALLBACK_STAGES


STAGES = load_stages()


class Game:
    """ゲーム全体の状態を保持する。"""

    def __init__(self):
        self.state = GameState.START
        self.stage_index = 0
        self.score = 0
        self.combo = 0
        self.best_combo = 0
        self.high_score = 0
        self.message = ""
        self.message_color = NORMAL_COLOR
        self.message_timer = 0.0
        self.start_time = 0.0
        self.pause_started_at = 0.0
        self.paused_offset = 0.0
        self.current_target_index = 0
        self._audio_active = False  # 現在、音声再生を基準に時間を計っているか
        self._audio_started = False  # このステージの音声を(遅延後に)再生し始めたか
        self.difficulty = "EASY"  # START画面で選択できる難易度
        self.session_id = uuid.uuid4().hex[:8]  # 1プレイ(リトライ〜終了)ごとのID
        self.logger = PlayLogger(BASE_DIR)

    @property
    def stage(self) -> Stage:
        return STAGES[self.stage_index]

    def elapsed(self) -> float:
        if self.state != GameState.PLAYING:
            return 0.0

        if self.stage.word_cues:
            # 単語ごとに個別音声を鳴らす新方式は、ゲーム自身の時計が「正」。
            # 音声はこの時計に合わせて追いかけて再生されるだけなので、ズレが起きない。
            return time.perf_counter() - self.start_time - self.paused_offset

        since_start = time.perf_counter() - self.start_time - self.paused_offset

        # audio_start_delay秒が経つまでは、まだ音声を再生していない
        # (短い文章でも、最初のノーツが降りてくる時間を必ず確保するため)
        if not self._audio_started or since_start < self.stage.audio_start_delay:
            return since_start

        # (旧方式) 音声を再生できている場合は、PCの時計ではなく「音声が今どこを再生しているか」を
        # 基準にする。これにより再生開始時のデコード遅延などがあってもズレなくなる。
        if self._audio_active:
            pos_ms = pygame.mixer.music.get_pos()
            if pos_ms >= 0:
                return self.stage.audio_start_delay + (pos_ms / 1000.0) + self.stage.audio_offset

        return since_start + self.stage.audio_offset

    def update_playback(self) -> None:
        """audio_start_delay秒が経過したタイミングで、実際に音声を再生し始める。"""
        if self.stage.word_cues or self._audio_started:
            return

        since_start = time.perf_counter() - self.start_time - self.paused_offset
        if since_start >= self.stage.audio_start_delay:
            self._play_stage_audio()
            self._audio_started = True

    def start_stage(self, index: int) -> None:
        self.stage_index = index
        self.current_target_index = 0
        self.paused_offset = 0.0
        self.message = ""
        self._audio_started = False
        for t in self.stage.targets:
            t.judged = False
            t.result = ""

        if self.stage.word_cues:
            self._prepare_word_cues()
            self._audio_started = True  # こちらの方式は開始と同時に単語再生を始めるため
        elif self.stage.audio_start_delay <= 0:
            # 遅延なし(古い形式のstages.json等)の場合は、これまで通り即座に再生する
            self._play_stage_audio()
            self._audio_started = True

        self.start_time = time.perf_counter()
        self.state = GameState.PLAYING

    def _prepare_word_cues(self) -> None:
        """単語ごとの音声を(初回のみ)読み込み、再生済みフラグをリセットする。"""
        for cue in self.stage.word_cues:
            cue.played = False
            if cue.sound is None and HAS_AUDIO:
                if os.path.isfile(cue.audio_path):
                    try:
                        cue.sound = pygame.mixer.Sound(cue.audio_path)
                    except pygame.error as e:
                        print(f"[audio] 単語音声の読み込みに失敗しました: {cue.audio_path} ({e})")
                else:
                    print(f"[audio] 単語音声が見つかりません: {cue.audio_path}")

    def update_word_audio(self, elapsed: float) -> None:
        """経過時間が各単語の予定時刻に達したら、その単語の音声を再生する。"""
        if not self.stage.word_cues:
            return
        for cue in self.stage.word_cues:
            if not cue.played and elapsed >= cue.start_time:
                cue.played = True
                if cue.sound is not None:
                    cue.sound.play()

    def _play_stage_audio(self) -> None:
        """ステージ用の音声ファイルを読み込んで再生する。ファイルが無ければ無音で続行する。"""
        self._audio_active = False

        if not HAS_AUDIO:
            print("[audio] mixerが使えないため音声は再生されません")
            return

        pygame.mixer.music.stop()

        audio_file = self.stage.audio_file
        if not audio_file:
            return  # そのステージには音声を設定していない

        # 相対パスの場合はスクリプトのある場所を基準に解決する
        path = audio_file if os.path.isabs(audio_file) else os.path.join(BASE_DIR, audio_file)

        if not os.path.isfile(path):
            print(f"[audio] ファイルが見つかりません: {path}")
            return

        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            self._audio_active = True
            print(f"[audio] 再生開始: {path}")
        except pygame.error as e:
            # 対応していない形式や壊れたファイルの場合は音無しで続行
            print(f"[audio] 読み込み/再生に失敗しました: {path} ({e})")
            self._audio_active = False

    def reset_run(self) -> None:
        self.score = 0
        self.combo = 0
        self.best_combo = 0
        self.session_id = uuid.uuid4().hex[:8]
        self.start_stage(0)

    def combo_multiplier(self) -> float:
        if self.combo >= 10:
            return 2.0
        if self.combo >= 5:
            return 1.5
        return 1.0

    def judge_tap(self) -> None:
        if self.current_target_index >= len(self.stage.targets):
            return

        elapsed = self.elapsed()
        target = self.stage.targets[self.current_target_index]
        difference = abs(elapsed - target.beat_time)

        if difference <= PERFECT_WINDOW:
            result = "PERFECT"
            gained = int(100 * self.combo_multiplier())
            self.score += gained
            self.combo += 1
            self.message_color = HIT_COLOR
            play_sound(SOUND_PERFECT)
        elif difference <= GOOD_WINDOW:
            result = "GOOD"
            gained = int(50 * self.combo_multiplier())
            self.score += gained
            self.combo += 1
            self.message_color = GOOD_COLOR
            play_sound(SOUND_GOOD)
        else:
            result = "MISS"
            self.combo = 0
            self.message_color = MISS_COLOR
            play_sound(SOUND_MISS)

        self.best_combo = max(self.best_combo, self.combo)
        target.judged = True
        target.result = result
        self.message = f"{result}  {target.word}"
        self.message_timer = 0.6
        self.current_target_index += 1

        # 較正用: 実際に押した時刻・正解時刻・その差をコンソールに出す。
        # 差が毎回同じ方向に偏っているなら audio_offset か beat_time で補正する目安になる。
        signed_diff = elapsed - target.beat_time
        print(
            f"[calib] {target.word:<10} tap={elapsed:.3f}s  target={target.beat_time:.3f}s  "
            f"diff={signed_diff:+.3f}s  -> {result}"
        )

        self.logger.log(
            session_id=self.session_id,
            difficulty=self.difficulty,
            sentence_id=self.stage.name,
            target_word=target.word,
            word_index=target.word_index,
            target_time=target.beat_time,
            tap_time=elapsed,
            result=result,
        )

    def check_missed_target(self) -> None:
        if self.current_target_index >= len(self.stage.targets):
            return

        elapsed = self.elapsed()
        target = self.stage.targets[self.current_target_index]

        if elapsed > target.beat_time + MISS_GRACE:
            target.judged = True
            target.result = "MISS"
            self.combo = 0
            self.message = f"MISS  {target.word}"
            self.message_color = MISS_COLOR
            self.message_timer = 0.6
            play_sound(SOUND_MISS)
            self.current_target_index += 1

            self.logger.log(
                session_id=self.session_id,
                difficulty=self.difficulty,
                sentence_id=self.stage.name,
                target_word=target.word,
                word_index=target.word_index,
                target_time=target.beat_time,
                tap_time=None,
                result="MISS",
            )

    def update_stage_progress(self) -> None:
        if self.current_target_index >= len(self.stage.targets):
            last_beat = self.stage.targets[-1].beat_time if self.stage.targets else 0.0
            # 最後のターゲット単語の判定終了だけでなく、音声そのものが最後まで
            # 鳴り終わるのも待ってから次に進む(途中で切れて聞こえるのを防ぐ)
            end_threshold = max(
                last_beat + 1.0, self.stage.audio_start_delay + self.stage.duration + 0.3
            )
            if self.elapsed() > end_threshold:
                self.high_score = max(self.high_score, self.score)
                next_index = self.stage_index + 1

                if next_index >= len(STAGES):
                    self.state = GameState.FINISHED
                elif next_index % STAGES_PER_CHECKPOINT == 0:
                    # 10ステージ区切り: ここで続けるか終えるか選べる
                    self.state = GameState.CHECKPOINT
                else:
                    self.state = GameState.STAGE_CLEAR

    def toggle_pause(self) -> None:
        if self.state == GameState.PLAYING:
            self.state = GameState.PAUSED
            self.pause_started_at = time.perf_counter()
            if HAS_AUDIO:
                pygame.mixer.music.pause()
                pygame.mixer.pause()
        elif self.state == GameState.PAUSED:
            self.paused_offset += time.perf_counter() - self.pause_started_at
            self.state = GameState.PLAYING
            if HAS_AUDIO:
                pygame.mixer.music.unpause()
                pygame.mixer.unpause()


game = Game()


# ----------------------------
# 描画関連
# ----------------------------
def draw_sentence(elapsed_time: float) -> None:
    """英文を単語ごとに描画する。難易度によってハイライトの見え方が変わる。"""
    word_surfaces = []
    total_width = 0
    active_index = None

    settings = DIFFICULTIES[game.difficulty]
    if settings["show_highlight"]:
        targets = game.stage.targets
        if game.current_target_index < len(targets):
            target = targets[game.current_target_index]
            if abs(elapsed_time - target.beat_time) <= settings["highlight_window"]:
                active_index = target.word_index

    for i, word in enumerate(game.stage.sentence_words):
        color = ACTIVE_COLOR if i == active_index else NORMAL_COLOR
        surface = font.render(word, True, color)
        word_surfaces.append(surface)
        total_width += surface.get_width() + 15

    x = (WIDTH - total_width) // 2
    y = 170
    for surface in word_surfaces:
        screen.blit(surface, (x, y))
        x += surface.get_width() + 15


def draw_note_lane(elapsed_time: float) -> None:
    """降ってくるノーツでタイミングを可視化する(Hardでは丸自体を表示しない)。"""
    # レーンの縦線とヒットライン
    pygame.draw.line(screen, LANE_COLOR, (LANE_X, LANE_TOP_Y), (LANE_X, HIT_LINE_Y + 40), 4)
    pygame.draw.circle(screen, HIT_LINE_COLOR, (LANE_X, HIT_LINE_Y), NOTE_RADIUS + 10, 3)

    if not DIFFICULTIES[game.difficulty]["show_notes"]:
        return

    for target in game.stage.targets:
        if target.judged:
            continue

        time_until_hit = target.beat_time - elapsed_time
        if -0.2 <= time_until_hit <= TRAVEL_TIME:
            progress = 1 - (time_until_hit / TRAVEL_TIME)
            y = LANE_TOP_Y + progress * (HIT_LINE_Y - LANE_TOP_Y)
            near = abs(time_until_hit) <= GOOD_WINDOW
            color = ACTIVE_COLOR if near else NORMAL_COLOR
            pygame.draw.circle(screen, color, (LANE_X, int(y)), NOTE_RADIUS)
            label = small_font.render(target.word, True, BACKGROUND)
            screen.blit(label, (LANE_X - label.get_width() // 2, int(y) - 15))


def draw_hud() -> None:
    score_text = small_font.render(f"Score: {game.score}", True, NORMAL_COLOR)
    screen.blit(score_text, (40, 30))

    combo_text = small_font.render(f"Combo: {game.combo}", True, NORMAL_COLOR)
    screen.blit(combo_text, (WIDTH - 200, 30))

    mult = game.combo_multiplier()
    if mult > 1.0:
        mult_text = small_font.render(f"x{mult:.1f}", True, ACTIVE_COLOR)
        screen.blit(mult_text, (WIDTH - 200, 65))

    stage_text = small_font.render(
        f"{game.stage.name}  ({game.stage_index + 1}/{len(STAGES)})", True, NORMAL_COLOR
    )
    screen.blit(stage_text, (WIDTH // 2 - stage_text.get_width() // 2, 30))

    diff_label = DIFFICULTIES[game.difficulty]["label"]
    diff_text = small_font.render(diff_label, True, ACTIVE_COLOR)
    screen.blit(diff_text, (WIDTH // 2 - diff_text.get_width() // 2, 60))

    if game.high_score:
        hs_text = small_font.render(f"High Score: {game.high_score}", True, NORMAL_COLOR)
        screen.blit(hs_text, (40, 65))


def draw_message() -> None:
    if game.message and game.message_timer > 0:
        result_text = large_font.render(game.message, True, game.message_color)
        screen.blit(
            result_text,
            (WIDTH // 2 - result_text.get_width() // 2, HIT_LINE_Y + 60),
        )


def draw_center_title(text: str, y: int, color=ACTIVE_COLOR) -> None:
    surf = large_font.render(text, True, color)
    screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))


def draw_center_sub(text: str, y: int, color=NORMAL_COLOR) -> None:
    surf = small_font.render(text, True, color)
    screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))


# ----------------------------
# メインループ
# ----------------------------
running = True
prev_time = time.perf_counter()

while running:
    dt = clock.tick(FPS) / 1000.0
    screen.blit(BACKGROUND_SURFACE, (0, 0))

    if game.message_timer > 0:
        game.message_timer -= dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_RETURN and game.state == GameState.START:
                game.reset_run()

            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3) and game.state == GameState.START:
                index = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}[event.key]
                game.difficulty = DIFFICULTY_ORDER[index]

            elif event.key == pygame.K_SPACE and game.state == GameState.PLAYING:
                game.judge_tap()

            elif event.key == pygame.K_p and game.state in (GameState.PLAYING, GameState.PAUSED):
                game.toggle_pause()

            elif event.key == pygame.K_RETURN and game.state == GameState.STAGE_CLEAR:
                game.start_stage(game.stage_index + 1)

            elif event.key == pygame.K_RETURN and game.state == GameState.CHECKPOINT:
                game.start_stage(game.stage_index + 1)

            elif event.key == pygame.K_q and game.state == GameState.CHECKPOINT:
                game.high_score = max(game.high_score, game.score)
                game.state = GameState.FINISHED

            elif event.key == pygame.K_r and game.state == GameState.FINISHED:
                game.reset_run()

    if game.state == GameState.PLAYING:
        game.update_playback()
        elapsed_time = game.elapsed()
        game.update_word_audio(elapsed_time)
        game.check_missed_target()
        game.update_stage_progress()

        title = small_font.render("Press SPACE on the stressed words  (P: pause)", True, NORMAL_COLOR)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT - 40))

        draw_sentence(elapsed_time)
        draw_note_lane(elapsed_time)
        draw_hud()
        draw_message()

    elif game.state == GameState.PAUSED:
        draw_sentence(game.elapsed())
        draw_note_lane(game.elapsed())
        draw_hud()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        draw_center_title("PAUSED", 220)
        draw_center_sub("Press P to resume", 300)

    elif game.state == GameState.START:
        draw_center_title("English Rhythm Game", 150)

        # 難易度選択(1/2/3キーで選ぶ。選択中のものだけ色を変える)
        diff_y = 250
        gap = 160
        start_x = WIDTH // 2 - gap
        for i, key in enumerate(DIFFICULTY_ORDER):
            settings = DIFFICULTIES[key]
            selected = key == game.difficulty
            color = ACTIVE_COLOR if selected else NORMAL_COLOR
            label = f"[{i + 1}] {settings['label']}"
            surf = small_font.render(label, True, color)
            x = start_x + i * gap - surf.get_width() // 2
            screen.blit(surf, (x, diff_y))
            if selected:
                pygame.draw.line(
                    screen, ACTIVE_COLOR, (x, diff_y + 34), (x + surf.get_width(), diff_y + 34), 3
                )

        draw_center_sub("Press 1 / 2 / 3 to choose difficulty", 300)
        draw_center_sub("Press ENTER to start", 350)
        if game.high_score:
            draw_center_sub(f"High Score: {game.high_score}", 390)

    elif game.state == GameState.STAGE_CLEAR:
        draw_center_title("STAGE CLEAR!", 150, HIT_COLOR)
        draw_center_sub(f"Score so far: {game.score}", 260)
        draw_center_sub("Press ENTER for next stage", 320)

    elif game.state == GameState.CHECKPOINT:
        cleared = game.stage_index + 1
        draw_center_title("CHECKPOINT!", 130, HIT_COLOR)
        draw_center_sub(f"{cleared} stages cleared  -  Score: {game.score}", 230)
        draw_center_sub("Press ENTER to keep going", 300)
        draw_center_sub("Press Q to finish here", 340)

    elif game.state == GameState.FINISHED:
        draw_center_title("FINISH!", 130)
        draw_center_sub(f"Final Score: {game.score}", 240, NORMAL_COLOR)
        draw_center_sub(f"Best Combo: {game.best_combo}", 280, NORMAL_COLOR)
        draw_center_sub("Press R to retry", 340)

    pygame.display.flip()

game.logger.close()
pygame.quit()
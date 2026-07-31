"""
edge-tts (無料のオンラインTTS) を使って、各ステージの音声ファイルと
「大文字で書かれた単語(強勢を置く単語)が実際に何秒地点で発音されているか」を
自動生成するスクリプト。

方式について:
    単語を1つずつ切り離して合成すると、
      - 短い大文字の単語が「頭字語」と誤認識されてアルファベット読みになる
      - 文としての自然なイントネーション・リズムが失われる
      - 単語ごとの再生スケジュールを組む都合上、最後の単語が再生されないまま
        ゲームが終わってしまうことがある
    という問題があったため、「文章をまるごと自然に読み上げる」方式に戻しています。

    タイミングは以下の優先順で決めます:
      1. TTSが単語ごとのタイムスタンプ(WordBoundary)を返せる場合はそれを使う(最も正確)
      2. 返せない場合は、音声全体の長さを測ったうえで、各単語の文字数の比率から
         「だいたいこのあたりで発音されているはず」という時刻を計算する(概算)
    概算の場合はズレることがあるので、実際にプレイして [calib] のログを見ながら
    stages.json の該当する beat_time を手で微調整してください。

事前準備:
    pip install edge-tts mutagen

使い方:
    python generate_stage_audio.py

実行すると
    ./assets/stage1.mp3, stage2.mp3, ...
    ./stages.json
を生成します。english_rhythm_game.py は起動時に stages.json があれば
そちらを自動的に読み込みます(なければ従来の手入力タイミングで動作します)。
"""

import asyncio
import json
import os
import re

import edge_tts
from mutagen.mp3 import MP3

# ----------------------------
# 設定
# ----------------------------
VOICE = "en-US-AriaNeural"   # 他の候補: en-US-GuyNeural, en-GB-SoniaNeural など
RATE = "+0%"                 # 発話速度。ゆっくりにしたい場合は "-10%" のようにマイナスにする

LEAD_IN = 1.6                 # 最初のノーツが降り始めてから当たるまで、必ずこれだけの時間を確保する(秒)

# --- 以下は「WordBoundaryが使えない場合の概算」専用の値 ---
# TTSが読み上げの前後につける無音(間)のおおよその長さ。
# 短い文章ほど、この無音が全体の長さに占める割合が大きくなりやすいため、
# 少なめに見積もっていると「実際にはもう単語を言い終わっているのに、
# 判定タイミングがまだ来ていない(遅れて感じる)」原因になる。
SPEECH_LEAD_IN = 0.2  # 音声の先頭にある無音のおおよその長さ
TAIL = 0.35           # 音声の末尾にある無音のおおよその長さ

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# 大文字で書かれた単語が「強勢=タップすべき単語」という、既存ゲームのルールに合わせている
STAGE_DEFINITIONS = [
    {
        "name": "Stage 1",
        "sentence_words": ["The", "QUICK", "brown", "FOX", "jumps", "OVER", "the", "LAZY", "dog."],
        "audio_filename": "stage1.mp3",
    },
    {
        "name": "Stage 2",
        "sentence_words": ["SHE", "sells", "SEA", "shells", "by", "the", "SEA", "shore"],
        "audio_filename": "stage2.mp3",
    },
    {
        "name": "Stage 3",
        "sentence_words": ["PETER", "Piper", "PICKED", "a", "PECK", "of", "PICKLED", "peppers"],
        "audio_filename": "stage3.mp3",
    },
    {
        "name": "Stage 4",
        "sentence_words": ["I", "REALLY", "love", "this", "SONG."],
        "audio_filename": "stage4.mp3",
    },
    {
        "name": "Stage 5",
        "sentence_words": ["She", "CAN'T", "find", "her", "KEYS."],
        "audio_filename": "stage5.mp3",
    },
    {
        "name": "Stage 6",
        "sentence_words": ["We", "ARE", "going", "to", "the", "PARK."],
        "audio_filename": "stage6.mp3",
    },
    {
        "name": "Stage 7",
        "sentence_words": ["He", "WORKS", "very", "HARD", "every", "day."],
        "audio_filename": "stage7.mp3",
    },
    {
        "name": "Stage 8",
        "sentence_words": ["They", "ALWAYS", "play", "SOCCER", "on", "Sundays."],
        "audio_filename": "stage8.mp3",
    },
    {
        "name": "Stage 9",
        "sentence_words": ["Please", "CLOSE", "the", "DOOR", "quietly."],
        "audio_filename": "stage9.mp3",
    },
    {
        "name": "Stage 10",
        "sentence_words": ["This", "is", "the", "BEST", "day", "EVER."],
        "audio_filename": "stage10.mp3",
    },
    {
        "name": "Stage 11",
        "sentence_words": ["I", "NEED", "some", "HELP", "right", "now."],
        "audio_filename": "stage11.mp3",
    },
    {
        "name": "Stage 12",
        "sentence_words": ["Let's", "MEET", "at", "the", "STATION."],
        "audio_filename": "stage12.mp3",
    },
    {
        "name": "Stage 13",
        "sentence_words": ["The", "WEATHER", "looks", "really", "NICE", "today."],
        "audio_filename": "stage13.mp3",
    },
    {
        "name": "Stage 14",
        "sentence_words": ["Can", "you", "HELP", "me", "with", "this", "PROBLEM?"],
        "audio_filename": "stage14.mp3",
    },
    {
        "name": "Stage 15",
        "sentence_words": ["I", "WANT", "to", "learn", "a", "new", "LANGUAGE."],
        "audio_filename": "stage15.mp3",
    },
    {
        "name": "Stage 16",
        "sentence_words": ["The", "MOVIE", "starts", "at", "SEVEN", "o'clock."],
        "audio_filename": "stage16.mp3",
    },
    {
        "name": "Stage 17",
        "sentence_words": ["My", "SISTER", "lives", "in", "a", "big", "CITY."],
        "audio_filename": "stage17.mp3",
    },
    {
        "name": "Stage 18",
        "sentence_words": ["We", "SHOULD", "leave", "EARLY", "tomorrow."],
        "audio_filename": "stage18.mp3",
    },
    {
        "name": "Stage 19",
        "sentence_words": ["He", "BOUGHT", "a", "new", "PAIR", "of", "shoes."],
        "audio_filename": "stage19.mp3",
    },
    {
        "name": "Stage 20",
        "sentence_words": ["I", "FORGOT", "my", "UMBRELLA", "at", "home."],
        "audio_filename": "stage20.mp3",
    },
    {
        "name": "Stage 21",
        "sentence_words": ["The", "CHILDREN", "are", "playing", "in", "the", "GARDEN."],
        "audio_filename": "stage21.mp3",
    },
    {
        "name": "Stage 22",
        "sentence_words": ["She", "WORKS", "as", "a", "NURSE", "at", "the", "hospital."],
        "audio_filename": "stage22.mp3",
    },
    {
        "name": "Stage 23",
        "sentence_words": ["Let's", "ORDER", "some", "PIZZA", "tonight."],
        "audio_filename": "stage23.mp3",
    },
    {
        "name": "Stage 24",
        "sentence_words": ["I", "HAVEN'T", "seen", "him", "in", "a", "LONG", "time."],
        "audio_filename": "stage24.mp3",
    },
    {
        "name": "Stage 25",
        "sentence_words": ["The", "TRAIN", "was", "DELAYED", "this", "morning."],
        "audio_filename": "stage25.mp3",
    },
    {
        "name": "Stage 26",
        "sentence_words": ["He", "ALWAYS", "arrives", "EARLY", "for", "meetings."],
        "audio_filename": "stage26.mp3",
    },
    {
        "name": "Stage 27",
        "sentence_words": ["Could", "you", "PASS", "me", "the", "SALT,", "please?"],
        "audio_filename": "stage27.mp3",
    },
    {
        "name": "Stage 28",
        "sentence_words": ["We", "WATCHED", "a", "great", "FILM", "last", "night."],
        "audio_filename": "stage28.mp3",
    },
    {
        "name": "Stage 29",
        "sentence_words": ["The", "COFFEE", "is", "TOO", "hot", "to", "drink."],
        "audio_filename": "stage29.mp3",
    },
    {
        "name": "Stage 30",
        "sentence_words": ["I'm", "LOOKING", "for", "a", "QUIET", "place", "to", "study."],
        "audio_filename": "stage30.mp3",
    },
    {
        "name": "Stage 31",
        "sentence_words": ["They", "MOVED", "to", "a", "new", "HOUSE", "last", "year."],
        "audio_filename": "stage31.mp3",
    },
    {
        "name": "Stage 32",
        "sentence_words": ["The", "DOG", "barked", "LOUDLY", "at", "the", "mailman."],
        "audio_filename": "stage32.mp3",
    },
    {
        "name": "Stage 33",
        "sentence_words": ["She", "SPEAKS", "three", "DIFFERENT", "languages."],
        "audio_filename": "stage33.mp3",
    },
    {
        "name": "Stage 34",
        "sentence_words": ["I", "CAN'T", "remember", "his", "NAME."],
        "audio_filename": "stage34.mp3",
    },
    {
        "name": "Stage 35",
        "sentence_words": ["The", "FLIGHT", "leaves", "at", "MIDNIGHT."],
        "audio_filename": "stage35.mp3",
    },
    {
        "name": "Stage 36",
        "sentence_words": ["He", "PLAYS", "the", "GUITAR", "every", "evening."],
        "audio_filename": "stage36.mp3",
    },
    {
        "name": "Stage 37",
        "sentence_words": ["We", "NEED", "more", "TIME", "to", "finish", "this."],
        "audio_filename": "stage37.mp3",
    },
    {
        "name": "Stage 38",
        "sentence_words": ["The", "STORE", "closes", "at", "NINE", "tonight."],
        "audio_filename": "stage38.mp3",
    },
    {
        "name": "Stage 39",
        "sentence_words": ["I", "JUST", "finished", "my", "HOMEWORK."],
        "audio_filename": "stage39.mp3",
    },
    {
        "name": "Stage 40",
        "sentence_words": ["She", "SMILED", "and", "WAVED", "at", "us."],
        "audio_filename": "stage40.mp3",
    },
    {
        "name": "Stage 41",
        "sentence_words": ["The", "WEATHER", "changed", "VERY", "suddenly."],
        "audio_filename": "stage41.mp3",
    },
    {
        "name": "Stage 42",
        "sentence_words": ["He", "DRIVES", "to", "work", "EVERY", "day."],
        "audio_filename": "stage42.mp3",
    },
    {
        "name": "Stage 43",
        "sentence_words": ["I", "LOVE", "the", "SMELL", "of", "fresh", "bread."],
        "audio_filename": "stage43.mp3",
    },
    {
        "name": "Stage 44",
        "sentence_words": ["They", "ARE", "planning", "a", "SURPRISE", "party."],
        "audio_filename": "stage44.mp3",
    },
    {
        "name": "Stage 45",
        "sentence_words": ["The", "BABY", "fell", "asleep", "QUICKLY."],
        "audio_filename": "stage45.mp3",
    },
    {
        "name": "Stage 46",
        "sentence_words": ["We", "WALKED", "along", "the", "BEACH", "at", "sunset."],
        "audio_filename": "stage46.mp3",
    },
    {
        "name": "Stage 47",
        "sentence_words": ["He", "FIXED", "the", "BROKEN", "chair", "himself."],
        "audio_filename": "stage47.mp3",
    },
    {
        "name": "Stage 48",
        "sentence_words": ["I", "HOPE", "you", "FEEL", "better", "soon."],
        "audio_filename": "stage48.mp3",
    },
    {
        "name": "Stage 49",
        "sentence_words": ["The", "TEACHER", "explained", "it", "VERY", "clearly."],
        "audio_filename": "stage49.mp3",
    },
    {
        "name": "Stage 50",
        "sentence_words": ["Let's", "TAKE", "a", "break", "and", "RELAX."],
        "audio_filename": "stage50.mp3",
    },
]


def normalize(word: str) -> str:
    """大文字/小文字・句読点の違いを無視して比較するための正規化。"""
    return re.sub(r"[^a-zA-Z0-9]", "", word).lower()


def clean_for_speech(word: str) -> str:
    """句読点を除いた単語だけを残す(読み上げ用)。"""
    return re.sub(r"[^a-zA-Z']", "", word)


def build_speech_text(sentence_words: list) -> str:
    """
    読み上げ用のテキストを作る。
    大文字のまま渡すと「頭字語」と誤認識されてアルファベット読みされることがあるため、
    いったん全部小文字にしてから、文の先頭だけ大文字に戻す(自然な文として読ませるため)。
    """
    words = [clean_for_speech(w).lower() for w in sentence_words]
    words = [w for w in words if w]
    text = " ".join(words)
    if text:
        text = text[0].upper() + text[1:] + "."
    return text


async def synth_with_word_boundaries(text: str, out_path: str):
    """edge-ttsで音声を合成しつつ、単語ごとの開始時刻(秒)が取れれば取得する。"""
    communicate = edge_tts.Communicate(text, voice=VOICE, rate=RATE)
    boundaries = []
    chunk_type_counts = {}

    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            chunk_type = chunk.get("type", "?")
            chunk_type_counts[chunk_type] = chunk_type_counts.get(chunk_type, 0) + 1

            if chunk_type == "audio":
                f.write(chunk["data"])
            elif chunk_type == "WordBoundary":
                start_seconds = chunk["offset"] / 10_000_000  # 100ns単位 -> 秒
                boundaries.append({"text": chunk["text"], "start": start_seconds})

    print(f"       [debug] 受信したチャンク種別: {chunk_type_counts}")
    return boundaries


def get_duration_seconds(path: str) -> float:
    """mp3ファイルの再生時間を取得する(ffmpeg不要、mutagenのみで完結)。"""
    try:
        return MP3(path).info.length
    except Exception as e:
        print(f"       [warn] 長さの取得に失敗しました({path}): {e} -> 3.0秒として扱います")
        return 3.0


def try_boundary_word_times(sentence_words, boundaries):
    """
    WordBoundaryが取れている場合に、sentence_wordsの各語へ順番に対応付ける。
    途中で1つでも対応が取れなければ None を返し、呼び出し側で概算方式に切り替える。
    """
    if not boundaries:
        return None

    word_times = []
    b_index = 0

    for word_index, word in enumerate(sentence_words):
        key = normalize(word)
        if not key:
            continue

        search_index = b_index
        found = None
        while search_index < len(boundaries):
            if normalize(boundaries[search_index]["text"]) == key:
                found = boundaries[search_index]
                b_index = search_index + 1
                break
            search_index += 1

        if found is None:
            return None

        word_times.append({"word_index": word_index, "start_time": round(found["start"], 3)})

    return word_times


def estimate_word_times(sentence_words, total_duration: float):
    """
    WordBoundaryが使えない場合の概算。各単語の文字数(+固定値)を重みにして、
    音声全体の長さを比例配分する。完全に正確ではないが、実用上十分な近さになる。
    ここで返す時刻は「音声そのものの先頭を0秒」とした相対時刻(LEAD_INは含まない)。
    """
    speakable = [(idx, clean_for_speech(w)) for idx, w in enumerate(sentence_words)]
    speakable = [(idx, w) for idx, w in speakable if w]

    if not speakable:
        return []

    weights = [len(w) + 2 for _, w in speakable]  # 文字数 + 単語間の間の分
    total_weight = sum(weights)
    speaking_duration = max(total_duration - SPEECH_LEAD_IN - TAIL, 0.3)

    word_times = []
    cursor = SPEECH_LEAD_IN
    for (word_index, _), weight in zip(speakable, weights):
        word_times.append({"word_index": word_index, "start_time": round(cursor, 3)})
        cursor += speaking_duration * (weight / total_weight)

    return word_times


async def build_stage(definition: dict) -> dict:
    sentence_words = definition["sentence_words"]
    speech_text = build_speech_text(sentence_words)
    out_path = os.path.join(ASSETS_DIR, definition["audio_filename"])

    print(f"[gen] {definition['name']} を生成中... ({speech_text})")

    boundaries = await synth_with_word_boundaries(speech_text, out_path)
    duration = get_duration_seconds(out_path)

    word_times = try_boundary_word_times(sentence_words, boundaries)
    if word_times is not None:
        source = "TTSの単語タイムスタンプ(高精度)"
    else:
        word_times = estimate_word_times(sentence_words, duration)
        source = "文字数に基づく概算(必要ならstages.jsonを手動調整してください)"

    # ここまでの時刻は「音声そのものの先頭を0秒」とした相対時刻。
    # 文章の長さに関係なく、最初のノーツが必ずLEAD_IN秒だけ降ってくる時間を
    # 確保できるよう、全ての単語の時刻に一律でLEAD_INを足す。
    # (実際の音声再生も、ゲーム側でLEAD_IN秒待ってから開始する)
    times_by_index = {t["word_index"]: round(t["start_time"] + LEAD_IN, 3) for t in word_times}

    targets = []
    for word_index, word in enumerate(sentence_words):
        if word.isupper() and word_index in times_by_index:
            targets.append(
                {"word": word, "word_index": word_index, "beat_time": times_by_index[word_index]}
            )

    print(f"       タイミング取得方法: {source}  (音声の長さ: {duration:.2f}秒)")
    for t in targets:
        print(f"       {t['word']:<10} -> {t['beat_time']}秒")

    return {
        "name": definition["name"],
        "sentence_words": sentence_words,
        "targets": targets,
        "audio_file": f"assets/{definition['audio_filename']}",
        "audio_offset": 0.0,
        "audio_start_delay": LEAD_IN,
        "duration": round(duration, 3),
    }


async def main() -> None:
    os.makedirs(ASSETS_DIR, exist_ok=True)

    try:
        print(f"[debug] edge-tts version: {edge_tts.__version__}")
    except AttributeError:
        pass

    stages_out = []
    for definition in STAGE_DEFINITIONS:
        stage = await build_stage(definition)
        stages_out.append(stage)

    stages_json_path = os.path.join(BASE_DIR, "stages.json")
    with open(stages_json_path, "w", encoding="utf-8") as f:
        json.dump(stages_out, f, ensure_ascii=False, indent=2)

    print(f"\n完了しました。 {stages_json_path} を生成しました。({len(stages_out)}ステージ)")
    print("english_rhythm_game.py を実行すると、この音声とタイミングが自動的に使われます。")


if __name__ == "__main__":
    asyncio.run(main())
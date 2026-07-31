CREATE TABLE IF NOT EXISTS play_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    played_at TEXT NOT NULL,
    session_id TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    sentence_id TEXT NOT NULL,
    target_word TEXT NOT NULL,
    word_index INTEGER NOT NULL,
    target_time REAL NOT NULL,
    tap_time REAL,
    timing_error REAL,
    result TEXT NOT NULL
);

INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:29:21', 'b949ee3c', 'NORMAL', 'Stage 1', 'QUICK', 1, 2.099, 2.034, -0.065, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:29:22', 'b949ee3c', 'NORMAL', 'Stage 1', 'FOX', 3, 2.936, 2.832, -0.104, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:29:22', 'b949ee3c', 'NORMAL', 'Stage 1', 'OVER', 5, 3.654, 3.552, -0.102, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:29:23', 'b949ee3c', 'NORMAL', 'Stage 1', 'LAZY', 7, 4.312, 4.173, -0.139, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:09', '3c23aea8', 'HARD', 'Stage 1', 'QUICK', 1, 2.099, 2.363, 0.264, 'GOOD');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:10', '3c23aea8', 'HARD', 'Stage 1', 'FOX', 3, 2.936, 2.996, 0.06, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:10', '3c23aea8', 'HARD', 'Stage 1', 'OVER', 5, 3.654, 3.58, -0.074, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:11', '3c23aea8', 'HARD', 'Stage 1', 'LAZY', 7, 4.312, 4.114, -0.198, 'GOOD');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:15', '3c23aea8', 'HARD', 'Stage 2', 'SHE', 0, 1.8, 2.081, 0.281, 'GOOD');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:16', '3c23aea8', 'HARD', 'Stage 2', 'SEA', 2, 2.439, 2.497, 0.058, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:16', '3c23aea8', 'HARD', 'Stage 2', 'SEA', 6, 3.611, 3.324, -0.287, 'GOOD');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:21', '3c23aea8', 'HARD', 'Stage 3', 'PETER', 0, 1.8, 2.072, 0.272, 'GOOD');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:21', '3c23aea8', 'HARD', 'Stage 3', 'PICKED', 2, 2.555, 2.5, -0.055, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:22', '3c23aea8', 'HARD', 'Stage 3', 'PECK', 4, 3.148, 2.909, -0.239, 'GOOD');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:22', '3c23aea8', 'HARD', 'Stage 3', 'PICKLED', 6, 3.687, 3.29, -0.397, 'MISS');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:28', '3c23aea8', 'HARD', 'Stage 4', 'I', 0, 1.8, 2.138, 0.338, 'MISS');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:28', '3c23aea8', 'HARD', 'Stage 4', 'REALLY', 1, 1.996, NULL, NULL, 'MISS');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:28', '3c23aea8', 'HARD', 'Stage 4', 'SONG.', 4, 3.305, 2.469, -0.836, 'MISS');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:32', '3c23aea8', 'HARD', 'Stage 5', 'CAN''T', 1, 2.131, 2.112, -0.019, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:33', '3c23aea8', 'HARD', 'Stage 5', 'KEYS.', 4, 3.324, 2.475, -0.849, 'MISS');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:37', '3c23aea8', 'HARD', 'Stage 6', 'ARE', 1, 2.02, 2.108, 0.088, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:38', '3c23aea8', 'HARD', 'Stage 6', 'PARK.', 5, 3.176, 2.803, -0.373, 'MISS');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:42', '3c23aea8', 'HARD', 'Stage 7', 'WORKS', 1, 2.05, 2.137, 0.087, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:42', '3c23aea8', 'HARD', 'Stage 7', 'HARD', 3, 2.862, 2.568, -0.294, 'GOOD');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:47', '3c23aea8', 'HARD', 'Stage 8', 'ALWAYS', 1, 2.176, 2.245, 0.069, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:48', '3c23aea8', 'HARD', 'Stage 8', 'SOCCER', 3, 3.054, 2.643, -0.411, 'MISS');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:53', '3c23aea8', 'HARD', 'Stage 9', 'CLOSE', 1, 2.278, 2.261, -0.017, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:53', '3c23aea8', 'HARD', 'Stage 9', 'DOOR', 3, 2.994, 2.543, -0.451, 'MISS');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:59', '3c23aea8', 'HARD', 'Stage 10', 'BEST', 3, 2.69, 2.479, -0.211, 'GOOD');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-20 19:31:59', '3c23aea8', 'HARD', 'Stage 10', 'EVER.', 5, 3.342, 2.729, -0.613, 'MISS');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-31 14:39:31', '0c0a24c4', 'HARD', 'Stage 1', 'QUICK', 1, 2.099, NULL, NULL, 'MISS');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-31 14:39:32', '0c0a24c4', 'HARD', 'Stage 1', 'FOX', 3, 2.936, NULL, NULL, 'MISS');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-31 14:39:32', '0c0a24c4', 'HARD', 'Stage 1', 'OVER', 5, 3.654, 3.542, -0.112, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-31 14:39:33', '0c0a24c4', 'HARD', 'Stage 1', 'LAZY', 7, 4.312, 3.933, -0.379, 'MISS');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-31 14:39:37', '0c0a24c4', 'HARD', 'Stage 2', 'SHE', 0, 1.8, 2.047, 0.247, 'GOOD');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-31 14:39:37', '0c0a24c4', 'HARD', 'Stage 2', 'SEA', 2, 2.439, 2.513, 0.074, 'PERFECT');
INSERT INTO play_log (played_at, session_id, difficulty, sentence_id, target_word, word_index, target_time, tap_time, timing_error, result) VALUES ('2026-07-31 14:39:38', '0c0a24c4', 'HARD', 'Stage 2', 'SEA', 6, 3.611, 3.002, -0.609, 'MISS');

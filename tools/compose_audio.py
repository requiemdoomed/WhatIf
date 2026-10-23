"""Render WhatIf's original instrumental loops. Author: Swayam Shakya.

Optional development command: python -m pip install numpy; python tools/compose_audio.py
Playback uses the bundled WAV files and does not require NumPy.
"""
from pathlib import Path
import json
import wave
import numpy as np

RATE = 22050
SCORES = {
 'main': ('Between Possibilities', 48, [0, 7, 10, 5], [0, 7, 12, 10, 3, 7, 14, 12], 'sine', 0.006),
 'orbital': ('Distant Habitats', 45, [0, 5, 8, 3], [0, 12, 7, 15, 12, 7, 3, 10], 'sine', 0.012),
 'tape': ('After the Last Broadcast', 53, [0, 5, 7, 3], [0, 4, 7, 12, 9, 7, 4, 2], 'warm', 0.018),
 'noir': ('An Unfinished Statement', 43, [0, 3, 8, 7], [0, 3, 7, 10, 7, 6, 3, 2], 'warm', 0.010),
 'mystery': ('Under the Familiar', 50, [0, 8, 5, 7], [0, 7, 3, 14, 12, 10, 7, 2], 'bell', 0.008),
 'neon': ('Rain on Circuit Glass', 41, [0, 10, 8, 5], [0, 12, 7, 10, 3, 15, 12, 7], 'pulse', 0.020),
 'city': ('Windows After Sunset', 55, [0, 5, 9, 7], [0, 4, 7, 11, 12, 7, 4, 2], 'warm', 0.009),
 'quantum': ('A Second Morning', 48, [0, 6, 9, 3], [0, 12, 6, 15, 9, 18, 12, 7], 'bell', 0.005),
 'clock': ('The Minute Between', 50, [0, 7, 3, 8], [0, 12, 7, 3, 10, 15, 12, 2], 'bell', 0.006),
 'wilderness': ('Beyond the Shelter', 43, [0, 5, 10, 7], [0, 7, 12, 5, 10, 7, 3, 0], 'sine', 0.025),
 'uncanny': ('The Room Remembers', 41, [0, 8, 3, 6], [0, 12, 1, 7, 10, 3, 13, 7], 'sine', 0.015),
}


def note(output, start, duration, midi, volume, kind, pan):
    begin = int(start * RATE)
    count = min(int(duration * RATE), len(output) - begin)
    t = np.arange(count) / RATE
    frequency = 440 * 2 ** ((midi - 69) / 12)
    phase = 2 * np.pi * frequency * t
    tone = np.sin(phase)
    if kind == 'warm':
        tone += 0.22 * np.sin(phase * 2) + 0.08 * np.sin(phase * 3)
    elif kind == 'bell':
        tone += 0.3 * np.sin(phase * 2.01) * np.exp(-t * 2)
    elif kind == 'pulse':
        tone += 0.18 * np.sin(phase * 3) + 0.05 * np.sin(phase * 5)
    attack = np.minimum(t / 0.09, 1)
    release = np.minimum((duration - t) / min(0.7, duration / 3), 1)
    envelope = attack * np.maximum(release, 0) * np.exp(-t * (0.5 if kind == 'bell' else 0.08))
    sound = tone * envelope * volume
    output[begin:begin+count, 0] += sound * np.sqrt((1 - pan) / 2)
    output[begin:begin+count, 1] += sound * np.sqrt((1 + pan) / 2)


def environment(key, samples, rng):
    """Original synthesized location textures; no licensed samples or sudden peaks."""
    t = np.arange(samples) / RATE
    noise = rng.normal(0, 1, (samples, 2))
    bed = np.zeros_like(noise)
    if key in ('noir', 'neon', 'city'):
        # Stereo rain, with slow passing traffic in the modern city.
        bed += noise * (.006 if key == 'city' else .011)
        for channel in range(2):
            wind = np.convolve(noise[:, channel], np.ones(250)/250, mode='same')
            bed[:, channel] += wind * (.17 + .1*np.sin(2*np.pi*t/8+channel))
    elif key == 'wilderness':
        for channel in range(2):
            wind = np.convolve(noise[:, channel], np.ones(160)/160, mode='same')
            bed[:, channel] += wind * (.26+.15*np.sin(2*np.pi*t/12+channel))
        for start in (3, 11, 19):
            local = t-start
            envelope = np.where((local>0)&(local<.65), np.sin(np.pi*np.clip(local,0,.65)/.65)**2, 0)
            bird = np.sin(2*np.pi*(1700*local+400*local**2))*envelope*.012
            bed[:, 0] += bird; bed[:, 1] += np.roll(bird, 700)*.6
    elif key in ('clock', 'tape'):
        bed += noise * (.003 if key == 'tape' else .0005)
        interval = 1 if key == 'clock' else 3
        for start in np.arange(.1, samples/RATE, interval):
            n = int(start*RATE); count = min(int(.06*RATE), samples-n)
            tick = noise[n:n+count]*np.exp(-np.arange(count)[:,None]/(RATE*.009))*.035
            bed[n:n+count] += tick
    elif key in ('orbital', 'uncanny'):
        for channel in range(2):
            bed[:,channel] += .012*np.sin(2*np.pi*(55+channel*.13)*t)*( .7+.3*np.sin(2*np.pi*t/12))
            bed[:,channel] += np.convolve(noise[:,channel], np.ones(300)/300, mode='same')*.11
    elif key in ('quantum', 'mystery'):
        for channel in range(2):
            bed[:,channel] += .008*np.sin(2*np.pi*(660+channel*1.5)*t)*np.sin(2*np.pi*t/8)**4
    return bed


def render(key, score, destination):
    title, root, progression, melody, timbre, texture = score
    duration = 32 if key == 'main' else 24
    samples = int(duration * RATE)
    mix = np.zeros((samples, 2))
    bar = duration / 4
    for i, chord in enumerate(progression):
        start = i * bar
        third = 4 if key in ('tape', 'city', 'main') else 3
        for interval, pan in [(0, -.45), (third, .4), (7, .1)]:
            note(mix, start, bar, root + chord + interval, .055, 'sine', pan)
        note(mix, start, bar, root + chord - 12, .065, 'sine', 0)
        for j in range(8):
            midi = root + 12 + melody[(j + i * 2) % len(melody)]
            note(mix, start + j * bar / 8, bar / 5, midi, .065, timbre, (-.3 if j % 2 else .3))
    # A quiet filtered texture avoids abrupt samples, spoken content and borrowed recordings.
    rng = np.random.default_rng(sum(key.encode()))
    noise = rng.normal(0, 1, samples)
    smooth = np.convolve(noise, np.ones(100) / 100, mode='same')
    texture_envelope = (0.6 + 0.4 * np.sin(np.linspace(0, np.pi * 8, samples))) * texture
    mix += (smooth * texture_envelope)[:, None]
    mix += environment(key, samples, rng)
    # Short stereo reflections add space without overpowering the prose.
    dry = mix.copy()
    for seconds, level in ((.19,.13),(.37,.08),(.61,.04)):
        delay = int(seconds*RATE)
        mix += np.roll(dry[:, ::-1], delay, axis=0)*level
    fade = int(.04 * RATE)
    mix[:fade] *= np.linspace(0, 1, fade)[:, None]
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    peak = float(np.max(np.abs(mix)))
    if peak > .65:
        mix *= .65 / peak
    pcm = (mix * 32767).astype('<i2')
    with wave.open(str(destination / (key + '.wav')), 'wb') as wav:
        wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(RATE)
        wav.writeframes(pcm.tobytes())
    return {'title': title, 'seconds': duration, 'peak': round(float(np.max(np.abs(mix))), 6),
            'rms': round(float(np.sqrt(np.mean(mix ** 2))), 6), 'file': key + '.wav'}


if __name__ == '__main__':
    destination = Path(__file__).resolve().parents[1] / 'static' / 'audio'
    destination.mkdir(exist_ok=True)
    report = {key: render(key, score, destination) for key, score in SCORES.items()}
    (destination / 'scores.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Rendered', len(report), 'original stereo scores.')

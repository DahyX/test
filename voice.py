# -*- coding: utf-8 -*-
"""
voice.py — Jarvis Voice Interface
Wake word detection → STT (Whisper) → Jarvis → TTS (pyttsx3)
All local, no external API needed.

Requirements (add to requirements.txt):
    SpeechRecognition>=3.10.0
    pyttsx3>=2.90
    pyaudio>=0.2.14
    openai-whisper>=20231117   # optional: better STT
"""

import threading
import queue
import time

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

WAKE_WORD = "jarvis"


class VoiceInterface:
    """Local STT + TTS voice interface."""

    def __init__(self, jarvis_run_fn):
        """
        Args:
            jarvis_run_fn: callable — takes a text string, returns response string.
                           This should be jarvis.run
        """
        self.run_fn = jarvis_run_fn
        self.running = False
        self._tts_queue = queue.Queue()
        self._recognizer = None
        self._tts_engine = None

        if HAS_SR:
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = 300
            self._recognizer.dynamic_energy_threshold = True

        if HAS_TTS:
            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty("rate", 175)
            self._tts_engine.setProperty("volume", 0.9)
            # Prefer a male voice if available
            voices = self._tts_engine.getProperty("voices")
            for v in voices:
                if "david" in v.name.lower() or "mark" in v.name.lower():
                    self._tts_engine.setProperty("voice", v.id)
                    break

        caps = []
        if HAS_SR:
            caps.append("STT (SpeechRecognition)")
        if HAS_TTS:
            caps.append("TTS (pyttsx3)")
        print(f"[Voice] Ready: {', '.join(caps) if caps else 'no audio libraries installed'}")

    def speak(self, text: str):
        """Speak text aloud."""
        if not HAS_TTS or not text:
            return
        try:
            self._tts_engine.say(text)
            self._tts_engine.runAndWait()
        except Exception as e:
            print(f"[Voice] TTS error: {e}")

    def listen_once(self, timeout: int = 5) -> str:
        """Listen for one utterance and return transcribed text."""
        if not HAS_SR:
            return ""
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                print("[Voice] Listening...")
                audio = self._recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
            text = self._recognizer.recognize_google(audio)
            print(f"[Voice] Heard: {text}")
            return text.lower().strip()
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except Exception as e:
            print(f"[Voice] STT error: {e}")
            return ""

    def start_wake_word_loop(self):
        """Background thread: listen for wake word, then process command."""
        self.running = True
        thread = threading.Thread(target=self._wake_loop, daemon=True)
        thread.start()
        print(f"[Voice] Wake word loop started. Say '{WAKE_WORD}' to activate.")
        return thread

    def stop(self):
        self.running = False

    def _wake_loop(self):
        while self.running:
            text = self.listen_once(timeout=3)
            if WAKE_WORD in text:
                self.speak("Yes?")
                command = self.listen_once(timeout=8)
                if command:
                    print(f"[Voice] Command: {command}")
                    try:
                        response = self.run_fn(command)
                        self.speak(response)
                    except Exception as e:
                        self.speak("Sorry, I ran into an error.")
                        print(f"[Voice] Error: {e}")
            time.sleep(0.1)

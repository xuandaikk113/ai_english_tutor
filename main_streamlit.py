import tkinter as tk
from tkinter import ttk
import requests
import speech_recognition as sr
import pyttsx3
import json
import os
import pyaudio
import wave
from threading import Thread
import time


class EnglishPracticeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("English Speaking Practice with AI")
        self.root.geometry("800x600")
        self.scenarios = {}

        # Initialize Ollama API
        self.ollama_api_url = "https://api.ollama.com/v1/chat"
        self.ollama_api_key = "your_ollama_api_key_here"

        # Initialize TTS engine
        self.setup_tts_engine()

        # Initialize variables
        self.is_recording = False
        self.audio_filename = "temp_recording.wav"
        self.conversation_active = False

        self.setup_scenarios()
        self.setup_gui()
        self.setup_audio()

    def setup_gui(self):
        # Main container with padding
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill="both", expand=True)

        # Left Panel - Scenarios
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        # Scenario Selection Frame
        scenario_frame = ttk.LabelFrame(
            left_panel, text="Select Scenario", padding="10"
        )
        scenario_frame.pack(fill="x", expand=True)

        # Scenario Description
        self.scenario_desc = tk.Text(left_panel, height=8, wrap=tk.WORD)
        self.scenario_desc.pack(fill="x", pady=10)
        self.scenario_desc.insert("1.0", "Select a scenario to see its description...")
        self.scenario_desc.config(state="disabled")

        # Create radio buttons for scenarios
        self.scenario_var = tk.StringVar()
        for scenario in self.scenarios.keys():
            rb = ttk.Radiobutton(
                scenario_frame,
                text=scenario,
                value=scenario,
                variable=self.scenario_var,
                command=self.on_scenario_selected,
            )
            rb.pack(anchor="w", pady=2)

        # Start button
        self.start_button = ttk.Button(
            left_panel, text="Start Conversation", command=self.start_new_conversation
        )
        self.start_button.pack(fill="x", pady=10)
        self.start_button.config(state="disabled")

        # Right Panel - Conversation
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side="right", fill="both", expand=True)

        # Conversation Frame
        conv_frame = ttk.LabelFrame(right_panel, text="Conversation", padding="10")
        conv_frame.pack(fill="both", expand=True)

        # Chat Display
        self.chat_display = tk.Text(conv_frame, wrap=tk.WORD)
        self.chat_display.pack(fill="both", expand=True)

        # Scrollbar for chat display
        scrollbar = ttk.Scrollbar(
            conv_frame, orient="vertical", command=self.chat_display.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.chat_display.configure(yscrollcommand=scrollbar.set)

        # Control Frame
        control_frame = ttk.Frame(right_panel, padding="10")
        control_frame.pack(fill="x", pady=5)

        # Record button
        self.record_button = ttk.Button(
            control_frame, text="Start Recording", command=self.toggle_recording
        )
        self.record_button.pack(side="left", padx=5)
        self.record_button.config(state="disabled")

        # Status label
        self.status_label = ttk.Label(control_frame, text="Please select a scenario")
        self.status_label.pack(side="left", padx=5)

        # Voice Settings Frame
        voice_frame = ttk.LabelFrame(right_panel, text="Voice Settings", padding="5")
        voice_frame.pack(fill="x", pady=5)

        # Speed control
        speed_frame = ttk.Frame(voice_frame)
        speed_frame.pack(side="left", padx=10)
        ttk.Label(speed_frame, text="Speed:").pack(side="left")
        self.speed_var = tk.IntVar(value=150)
        speed_spinbox = ttk.Spinbox(
            speed_frame,
            from_=50,
            to=300,
            width=5,
            textvariable=self.speed_var,
            command=self.update_voice_settings,
        )
        speed_spinbox.pack(side="left", padx=5)

        # Volume control
        volume_frame = ttk.Frame(voice_frame)
        volume_frame.pack(side="left", padx=10)
        ttk.Label(volume_frame, text="Volume:").pack(side="left")
        self.volume_var = tk.DoubleVar(value=1.0)
        volume_spinbox = ttk.Spinbox(
            volume_frame,
            from_=0.0,
            to=1.0,
            increment=0.1,
            width=5,
            textvariable=self.volume_var,
            command=self.update_voice_settings,
        )
        volume_spinbox.pack(side="left", padx=5)

    def setup_scenarios(self):
        self.scenarios = {
            "Casual Chat": {
                "system_prompt": "You are a friendly conversation partner. Keep responses natural and casual. Ask follow-up questions to maintain conversation flow.",
                "initial_prompt": "Hi there! How are you doing today?",
                "description": "Practice casual conversation with topics like weather, hobbies, and daily life. Perfect for building basic conversation skills.",
            },
            "Daily Routines": {
                "system_prompt": "You are helping someone practice discussing daily routines and activities in English. Ask about their schedule and habits.",
                "initial_prompt": "I'm curious about your daily routine. What time do you usually wake up?",
                "description": "Practice describing your daily schedule, habits, and regular activities. Learn time-related vocabulary and expressions.",
            },
            "Giving Directions": {
                "system_prompt": "You are a local helping someone find their way. Ask where they want to go and practice giving directions.",
                "initial_prompt": "Hello! You seem lost. Can I help you find somewhere?",
                "description": "Learn to give and follow directions in English. Practice using location-based vocabulary and prepositions.",
            },
            "Personal Information": {
                "system_prompt": "You are meeting someone new and exchanging basic personal information. Ask appropriate questions about their background.",
                "initial_prompt": "Nice to meet you! Where are you from?",
                "description": "Practice introducing yourself and sharing basic personal information. Learn to ask and answer common questions about yourself.",
            },
            "Time Expressions": {
                "system_prompt": "You are helping someone practice telling time and using time expressions in English.",
                "initial_prompt": "Do you know what time it is? Could you tell me?",
                "description": "Learn to tell time and use time-related expressions in English. Practice different ways to talk about time and schedules.",
            },
            "Numbers Practice": {
                "system_prompt": "You are helping someone practice using numbers in English conversation.",
                "initial_prompt": "Let's practice with numbers! Could you tell me your phone number?",
                "description": "Practice using numbers in different contexts like prices, dates, phone numbers, and measurements.",
            },
            "Party Meeting": {
                "system_prompt": "You are at a party meeting new people. Keep the conversation light and social.",
                "initial_prompt": "Hey! I don't think we've met before. What brings you to this party?",
                "description": "Practice social interactions at parties or gatherings. Learn small talk and how to make new connections.",
            },
            "Dating Scenario": {
                "system_prompt": "You are on a first date. Keep the conversation appropriate and friendly.",
                "initial_prompt": "It's nice to finally meet you! Have you been to this place before?",
                "description": "Practice conversation skills for dating scenarios. Learn appropriate topics and questions for first dates.",
            },
        }

    def on_scenario_selected(self):
        scenario = self.scenario_var.get()
        if scenario in self.scenarios:
            # Update description
            self.scenario_desc.config(state="normal")
            self.scenario_desc.delete(1.0, tk.END)
            self.scenario_desc.insert(1.0, self.scenarios[scenario]["description"])
            self.scenario_desc.config(state="disabled")

            # Enable start button
            self.start_button.config(state="normal")
            self.status_label.config(text="Click 'Start Conversation' to begin")

    def setup_audio(self):
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()

    def on_scenario_selected(self):
        scenario = self.scenario_var.get()
        if scenario in self.scenarios:
            self.chat_display.delete(1.0, tk.END)
            self.start_conversation(scenario)

    def start_conversation(self, scenario):
        system_prompt = self.scenarios[scenario]["system_prompt"]
        initial_prompt = self.scenarios[scenario]["initial_prompt"]

        # Get AI response
        response = self.get_ai_response(system_prompt, initial_prompt)

        # Display and speak response
        self.display_message("AI: " + response)
        self.speak_text(response)

    def start_new_conversation(self):
        # Clear chat display
        self.chat_display.delete(1.0, tk.END)

        # Get selected scenario
        scenario = self.scenario_var.get()

        # Enable recording button
        self.record_button.config(state="normal")

        # Start conversation
        self.conversation_active = True
        system_prompt = self.scenarios[scenario]["system_prompt"]
        initial_prompt = self.scenarios[scenario]["initial_prompt"]

        # Get AI response
        response = self.get_ai_response(system_prompt, initial_prompt)

        # Display and speak response
        self.display_message("AI: " + response)
        self.speak_text(response)

        # Update status
        self.status_label.config(text="Ready for your response")

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.record_button.configure(text="Stop Recording")
        self.status_label.configure(text="Recording...")

        # Start recording in a separate thread
        self.recording_thread = Thread(target=self.record_audio)
        self.recording_thread.start()

    def stop_recording(self):
        self.is_recording = False
        self.record_button.configure(text="Start Recording")
        self.status_label.configure(text="Processing...")

        # Wait for recording thread to finish
        self.recording_thread.join()

        # Process the recording
        text = self.speech_to_text()
        if text:
            self.display_message("You: " + text)

            # Get AI response
            scenario = self.scenario_var.get()
            system_prompt = self.scenarios[scenario]["system_prompt"]
            response = self.get_ai_response(system_prompt, text)

            # Display and speak AI response
            self.display_message("AI: " + response)
            self.speak_text(response)

        self.status_label.configure(text="Ready")

    def record_audio(self):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100

        p = pyaudio.PyAudio()
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )

        frames = []
        while self.is_recording:
            data = stream.read(CHUNK)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        # Save the recording
        wf = wave.open(self.audio_filename, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
        wf.close()

    def speech_to_text(self):
        with sr.AudioFile(self.audio_filename) as source:
            audio = self.recognizer.record(source)
            try:
                text = self.recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                self.status_label.configure(text="Could not understand audio")
                return None
            except sr.RequestError:
                self.status_label.configure(text="Could not request results")
                return None

    def get_ai_response(self, system_prompt, user_message):
        headers = {
            "Authorization": f"Bearer {self.ollama_api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "ollama-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        }
        try:
            response = requests.post(self.ollama_api_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            return f"Error getting AI response: {str(e)}"

    def setup_tts_engine(self):

        try:
            self.engine = pyttsx3.init()

            # Get available voices
            voices = self.engine.getProperty("voices")

            # Find and set English voice
            english_voice = None
            for voice in voices:
                # Print voice information for debugging
                print(f"Voice ID: {voice.id}")
                print(f"Voice Name: {voice.name}")
                print(f"Voice Languages: {voice.languages}")
                print("---")

                # Try to find an English voice
                if "EN" in voice.id.upper():
                    english_voice = voice
                    break

            if english_voice:
                self.engine.setProperty("voice", english_voice.id)
                print(f"Selected voice: {english_voice.name}")
            else:
                print("No English voice found, using default voice")

            # Set default properties
            self.engine.setProperty("rate", 150)  # Speed of speech
            self.engine.setProperty("volume", 1.0)  # Volume (0.0 to 1.0)

        except Exception as e:
            print(f"Error initializing TTS engine: {str(e)}")
            self.status_label.configure(text="TTS initialization failed")

    def update_voice_settings(self):
        try:
            # Update the TTS engine settings based on the current values of speed and volume
            self.engine.setProperty("rate", self.speed_var.get())
            self.engine.setProperty("volume", self.volume_var.get())
            self.status_label.configure(text="Voice settings updated")
        except Exception as e:
            self.status_label.configure(text=f"Error updating voice settings: {str(e)}")

    def speak_text(self, text):
        try:
            # Run speech in a separate thread to prevent GUI freezing
            def speak():
                self.engine.say(text)
                self.engine.runAndWait()

            Thread(target=speak).start()
        except Exception as e:
            self.status_label.configure(text=f"TTS Error: {str(e)}")

    def display_message(self, message):
        self.chat_display.insert(tk.END, message + "\n\n")
        self.chat_display.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = EnglishPracticeApp(root)
    root.mainloop()

import tkinter as tk
from tkinter import ttk
import speech_recognition as sr
import pyttsx3
import pyaudio
import wave
from threading import Thread
import requests  # Added for Ollama API calls
import edge_tts
import asyncio


class EnglishPracticeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("English Speaking Practice with AI")
        self.root.geometry("800x600")
        self.scenarios = {}

        # Initialize Ollama endpoint
        self.ollama_endpoint = "http://localhost:11434/api/chat"

        # Initialize TTS engine
        self.setup_tts_engine()

        # Initialize variables
        self.is_recording = False
        self.audio_filename = "temp_recording.wav"
        self.conversation_active = False
        self.is_speaking = False  # Add flag to track TTS state

        self.setup_scenarios()
        self.setup_gui()
        self.setup_audio()

        # Initialize conversation history
        self.conversation_history = []

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
        self.record_button.config(state="enabled")

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

        # Configure tags for user and bot messages
        self.chat_display.tag_configure("user", justify="right", foreground="blue")
        self.chat_display.tag_configure("bot", justify="left", foreground="green")

    def setup_scenarios(self):
        self.scenarios = {
            "Casual Chat": {
                "system_prompt": "You are a friendly conversation partner. Keep responses natural and casual. Ask follow-up questions to maintain conversation flow.",
                "initial_prompt": "you are my english tutor, please help me practice talking in english, i want us to talk about Chitchat topic. please ask me first",
                "description": "Practice casual conversation with topics like weather, hobbies, and daily life. Perfect for building basic conversation skills.",
            },
            "Daily Routines": {
                "system_prompt": "You are helping someone practice discussing daily routines and activities in English. Ask about their schedule and habits.",
                "initial_prompt": "you are my english tutor, please help me practice talking in english, i want us to talk about Daily Routines topic. please ask me first",
                "description": "Practice describing your daily schedule, habits, and regular activities. Learn time-related vocabulary and expressions.",
            },
            "Giving Directions": {
                "system_prompt": "You are a local helping someone find their way. Ask where they want to go and practice giving directions.",
                "initial_prompt": "you are my english tutor, please help me practice talking in english, i want us to talk about Giving Directions topic. please ask me first",
                "description": "Learn to give and follow directions in English. Practice using location-based vocabulary and prepositions.",
            },
            "Personal Information": {
                "system_prompt": "You are meeting someone new and exchanging basic personal information. Ask appropriate questions about their background.",
                "initial_prompt": "you are my english tutor, please help me practice talking in english, i want us to talk about Personal Information topic. please ask me first",
                "description": "Practice introducing yourself and sharing basic personal information. Learn to ask and answer common questions about yourself.",
            },
            "Time Expressions": {
                "system_prompt": "You are helping someone practice telling time and using time expressions in English.",
                "initial_prompt": "you are my english tutor, please help me practice talking in english, i want us to talk about Time Expressions topic. please ask me first",
                "description": "Learn to tell time and use time-related expressions in English. Practice different ways to talk about time and schedules.",
            },
            "Numbers Practice": {
                "system_prompt": "You are helping someone practice using numbers in English conversation.",
                "initial_prompt": "you are my english tutor, please help me practice talking in english, i want us to talk about Numbers Practice topic. please ask me first",
                "description": "Practice using numbers in different contexts like prices, dates, phone numbers, and measurements.",
            },
            "Party Meeting": {
                "system_prompt": "You are at a party meeting new people. Keep the conversation light and social.",
                "initial_prompt": "you are my english tutor, please help me practice talking in english, i want us to talk about Party Meeting topic. please ask me first",
                "description": "Practice social interactions at parties or gatherings. Learn small talk and how to make new connections.",
            },
            "Dating Scenario": {
                "system_prompt": "You are on a first date. Keep the conversation appropriate and friendly.",
                "initial_prompt": "you are my english tutor, please help me practice talking in english, i want us to talk about Dating Scenario topic. please ask me first",
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
        # system_prompt = self.scenarios[scenario]["system_prompt"]
        initial_prompt = self.scenarios[scenario]["initial_prompt"]

        # Get AI response
        # response = self.get_ai_response(system_prompt, initial_prompt)
        response = self.get_ai_response(initial_prompt)

        # Display and speak response
        self.display_message("AI: " + response, "bot")
        self.speak_text(response)

    def start_new_conversation(self):
        # Clear chat display
        self.chat_display.delete(1.0, tk.END)

        # Get selected scenario
        scenario = self.scenario_var.get()

        # Enable recording button
        self.start_button.config(state="disabled")

        # Start conversation
        self.conversation_active = True
        # system_prompt = self.scenarios[scenario]["system_prompt"]
        initial_prompt = self.scenarios[scenario]["initial_prompt"]

        # Get AI response
        # response = self.get_ai_response(system_prompt, initial_prompt)
        response = self.get_ai_response(initial_prompt)

        # Display and speak response
        self.display_message("AI: " + response, role="bot")
        self.speak_text(response)

        # Update status
        self.status_label.config(text="Ready for your response")

    # [Rest of the methods remain the same...]
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
            # scenario = self.scenario_var.get()
            # system_prompt = self.scenarios[scenario]["system_prompt"]
            # response = self.get_ai_response(system_prompt, text)
            response = self.get_ai_response(text)

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

    def get_ai_response(self, user_message):
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})

            # Prepare the request payload for Ollama
            payload = {
                "model": "llama3.2",
                "messages": self.conversation_history,
                "stream": False,
            }

            # Make the request to Ollama
            response = requests.post(self.ollama_endpoint, json=payload)

            if response.status_code == 200:
                response_data = response.json()
                ai_message = response_data["message"]["content"]

                # Add AI response to conversation history
                self.conversation_history.append(
                    {"role": "assistant", "content": ai_message}
                )

                return ai_message
            else:
                return f"Error: Received status code {response.status_code} from Ollama"

        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to Ollama. Make sure Ollama is running on localhost:11434"
        except Exception as e:
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

    async def speak_text(self, text):
        try:
            # Set speaking flag
            self.is_speaking = True

            async def speak():
                try:
                    communicate = edge_tts.Communicate(text, voice="en-US-JennyNeural")
                    await communicate.save("output.mp3")
                    os.system("start output.mp3")
                finally:
                    # Clear speaking flag and ensure recording button is enabled
                    self.is_speaking = False
                    self.root.after(0, self.enable_recording_button)

            await speak()
        except Exception as e:
            self.is_speaking = False
            self.status_label.configure(text=f"TTS Error: {str(e)}")
            self.enable_recording_button()

    def enable_recording_button(self):
        if self.conversation_active:
            self.record_button.config(state="normal")
            self.status_label.configure(text="Ready for your response")

    def toggle_recording(self):
        if not self.is_recording and not self.is_speaking:
            self.start_recording()
        elif self.is_recording:
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
            self.display_message("You: " + text, "user")

            # Get AI response
            response = self.get_ai_response(text)

            # Display and speak AI response
            self.display_message("AI: " + response, "bot")
            asyncio.run(self.speak_text(response))

        self.status_label.configure(text="Ready")

    def display_message(self, message, role):
        if role == "user":
            self.chat_display.insert(tk.END, message + "\n\n", "user")
        else:
            self.chat_display.insert(tk.END, message + "\n\n", "bot")

        self.chat_display.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = EnglishPracticeApp(root)
    root.mainloop()

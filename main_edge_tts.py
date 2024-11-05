import tkinter as tk
from tkinter import ttk
import speech_recognition as sr
import os
import pyaudio
import wave
from threading import Thread
import requests  # Added for Ollama API calls
import json
import edge_tts
import asyncio
import subprocess


class EnglishPracticeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("English Speaking Practice with AI")
        self.root.geometry("1280x720")
        self.root.attributes("-topmost", True)  # Make the window always on top
        self.scenarios = {}

        # Initialize Ollama endpoint
        self.ollama_endpoint = "http://localhost:11434/api/chat"

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

    def setup_audio(self):
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()

    def on_scenario_selected(self):
        scenario = self.scenario_var.get()
        if scenario in self.scenarios:
            # Enable start button
            self.start_button.config(state="normal")
            self.status_label.config(text="Click 'Start Conversation' to begin")

    def start_conversation(self, scenario):
        initial_prompt = self.scenarios[scenario]["initial_prompt"]

        # Get AI response
        response = self.get_ai_response(initial_prompt)

    def start_new_conversation(self):
        # Clear chat display
        self.chat_display.delete(1.0, tk.END)

        # Get selected scenario
        scenario = self.scenario_var.get()

        # Enable recording button
        self.start_button.config(state="disabled")

        # Start conversation
        self.conversation_active = True
        initial_prompt = self.scenarios[scenario]["initial_prompt"]

        # Get AI response
        response = self.get_ai_response(initial_prompt)

        asyncio.run(self.speak_text(response))

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
                "messages": self.conversation_history[-10:],
                "stream": True,
            }

            # Make the request to Ollama
            response = requests.post(self.ollama_endpoint, json=payload, stream=True)

            if response.status_code == 200:
                ai_message = ""

                # Track if we've started displaying the message
                message_started = False

                for chunk in response.iter_lines():
                    if chunk:
                        chunk_data = json.loads(chunk.decode("utf-8"))
                        if (
                            "message" in chunk_data
                            and "content" in chunk_data["message"]
                        ):
                            # Get the new content
                            new_content = chunk_data["message"]["content"]
                            ai_message += new_content

                            # If this is the first chunk, insert new message
                            if not message_started:
                                self.chat_display.insert(tk.END, "AI: ", "bot")
                                message_started = True

                            # Insert the new content
                            self.chat_display.insert(tk.END, new_content, "bot")
                            self.chat_display.see(tk.END)
                            self.root.update_idletasks()

                # Add newlines after the complete message
                self.chat_display.insert(tk.END, "\n\n")

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

    async def speak_text(self, text):
        try:
            # Set speaking flag
            self.is_speaking = True

            async def speak():
                try:
                    communicate = edge_tts.Communicate(text, voice="en-US-JennyNeural")
                    await communicate.save("output.mp3")
                    print("TTS: output.mp3 saved successfully")

                    if os.path.exists("output.mp3"):
                        # Initialize pygame mixer
                        #
                        # os.system("start output.mp3")
                        subprocess.Popen(["start", "output.mp3"], shell=True)
                    else:
                        print("TTS: output.mp3 file not found")
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

            asyncio.run(self.speak_text(response))

        self.status_label.configure(text="Ready")

    def display_message(self, message, role):
        if role == "user":
            self.chat_display.insert(tk.END, message + "\n\n", "user")
        else:
            # For AI messages, just insert the message with proper formatting
            self.chat_display.insert(tk.END, message + "\n\n", "bot")

        self.chat_display.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = EnglishPracticeApp(root)
    root.mainloop()

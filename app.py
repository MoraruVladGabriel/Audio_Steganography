import wave
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from pydub import AudioSegment
from cryptography.fernet import Fernet
from datetime import datetime

LOG_FILE = "activity_log.txt"


def log_activity(message):
    """Log activity to a file."""
    with open(LOG_FILE, "a") as log:
        log.write(f"{datetime.now()}: {message}\n")


def generate_key():
    """Generate a new encryption key."""
    key = Fernet.generate_key()
    return key


def save_key_to_file(key, input_audio_path):
    """Save the encryption key to a file, named after the input audio file."""
    # Extrage numele fișierului fără extensie
    base_name = os.path.splitext(os.path.basename(input_audio_path))[0]

    # Creează un nume de fișier pentru cheia de criptare
    key_file_path = f"{base_name}_key.txt"

    # Salvează cheia în fișierul respectiv
    with open(key_file_path, "wb") as key_file:
        key_file.write(key)

    messagebox.showinfo("Success", f"Key saved to {key_file_path}")
    log_activity(f"Key saved to {key_file_path}")


def load_key_from_file():
    """Load an encryption key from a file."""
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if file_path:
        with open(file_path, "rb") as key_file:
            return key_file.read()
    messagebox.showerror("Error", "No key file selected.")
    return None


def convert_to_wav(input_audio_path):
    """
    Convert audio file to WAV format if it's not already a WAV file.
    :param input_audio_path: Path to the input audio file
    :return: Path to the converted WAV file
    """
    if input_audio_path.lower().endswith('.wav'):
        return input_audio_path

    audio = AudioSegment.from_file(input_audio_path)
    wav_path = os.path.splitext(input_audio_path)[0] + "_converted.wav"
    audio.export(wav_path, format="wav")
    return wav_path

def encode_audio(input_audio_path, secret_message, encryption_key):
    """
    Encode a secret message into an audio file.

    :param input_audio_path: Path to the input audio file
    :param secret_message: The secret message to encode
    :param encryption_key: Encryption key for securing the message
    :return: Path to the output WAV file with the secret message encoded
    """
    wav_path = convert_to_wav(input_audio_path)
    cipher = Fernet(encryption_key)
    encrypted_message = cipher.encrypt(secret_message.encode())

    secret_message_binary = ''.join(format(byte, '08b') for byte in encrypted_message) + '00000000'

    with wave.open(wav_path, 'rb') as audio:
        params = audio.getparams()
        frames = audio.readframes(params.nframes)

        audio_data = np.frombuffer(frames, dtype=np.int16)

    if len(secret_message_binary) > len(audio_data):
        raise ValueError("The secret message is too large to encode in this audio file.")

    encoded_audio_data = audio_data.copy()
    for i, bit in enumerate(secret_message_binary):
        encoded_audio_data[i] = (encoded_audio_data[i] & ~1) | int(bit)

    output_audio_path = os.path.splitext(wav_path)[0] + "_encoded.wav"
    with wave.open(output_audio_path, 'wb') as encoded_audio:
        encoded_audio.setparams(params)
        encoded_audio.writeframes(encoded_audio_data.tobytes())

    log_activity(f"Message encoded into {output_audio_path}")

    # Plot the spectrogram of the encoded audio
    return output_audio_path


def decode_audio(encoded_audio_path, encryption_key):
    """
    Decode a secret message from an audio file.

    :param encoded_audio_path: Path to the encoded WAV file
    :param encryption_key: Encryption key for decoding the message
    :return: The decoded secret message
    """
    wav_path = convert_to_wav(encoded_audio_path)

    with wave.open(wav_path, 'rb') as audio:
        frames = audio.readframes(audio.getnframes())
        audio_data = np.frombuffer(frames, dtype=np.int16)

    bits = [str(sample & 1) for sample in audio_data]

    message_bytes = [bits[i:i + 8] for i in range(0, len(bits), 8)]
    encrypted_message = b''
    for byte in message_bytes:
        char = chr(int(''.join(byte), 2))
        if char == '\x00':
            break
        encrypted_message += bytes([int(''.join(byte), 2)])

    cipher = Fernet(encryption_key)
    decrypted_message = cipher.decrypt(encrypted_message).decode()

    log_activity(f"Message decoded from {encoded_audio_path}")
    return decrypted_message


def select_input_file(entry):
    file_path = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav *.mp3 *.flac *.ogg *.aac *.m4a")])
    entry.delete(0, tk.END)
    entry.insert(0, file_path)


def encode_message_ui(input_entry, message_entry, key_entry):
    input_path = input_entry.get()
    secret_message = message_entry.get()
    encryption_key = key_entry.get().encode()

    try:
        # Apelează funcția pentru a salva cheia, folosind calea fișierului audio
        save_key_to_file(encryption_key, input_path)

        output_path = encode_audio(input_path, secret_message, encryption_key)
        key_entry.delete(0, tk.END)  # Clear the decryption key field
        messagebox.showinfo("Success", f"Message encoded successfully into {output_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def decode_message_ui(input_entry, key_entry, message_label):
    input_path = input_entry.get()
    encryption_key = key_entry.get().encode()

    try:
        decoded_message = decode_audio(input_path, encryption_key)
        message_label.config(text=f"Decoded message: {decoded_message}")
        key_entry.delete(0, tk.END)  # Clear the decryption key field
    except Exception as e:
        messagebox.showerror("Error", str(e))


def create_gui():
    root = tk.Tk()
    root.title("Audio Steganography")

    tab_control = tk.Frame(root)
    tab_control.pack(pady=10, padx=10)

    encode_frame = tk.Frame(tab_control)
    encode_frame.pack(side=tk.LEFT, padx=20)

    decode_frame = tk.Frame(tab_control)
    decode_frame.pack(side=tk.RIGHT, padx=20)

    # Encoding Section
    tk.Label(encode_frame, text="Encoding", font=("Arial", 14)).pack()

    tk.Label(encode_frame, text="Input Audio File:").pack(anchor="w")
    input_entry = tk.Entry(encode_frame, width=40)
    input_entry.pack()
    tk.Button(encode_frame, text="Browse", command=lambda: select_input_file(input_entry)).pack()

    tk.Label(encode_frame, text="Secret Message:").pack(anchor="w")
    message_entry = tk.Entry(encode_frame, width=40)
    message_entry.pack()

    tk.Label(encode_frame, text="Encryption Key:").pack(anchor="w")
    key_entry = tk.Entry(encode_frame, width=40, show="*")
    key_entry.pack()

    tk.Button(encode_frame, text="Generate Key", command=lambda: key_entry.insert(0, generate_key().decode())).pack()
    # tk.Button(encode_frame, text="Save Key", command=lambda: save_key_to_file(key_entry.get().encode(), input_entry.get())).pack()

    tk.Button(encode_frame, text="Encode Message",
              command=lambda: encode_message_ui(input_entry, message_entry, key_entry)).pack(pady=10)

    # Decoding Section
    tk.Label(decode_frame, text="Decoding", font=("Arial", 14)).pack()

    tk.Label(decode_frame, text="Encoded Audio File:").pack(anchor="w")
    decode_input_entry = tk.Entry(decode_frame, width=40)
    decode_input_entry.pack()
    tk.Button(decode_frame, text="Browse", command=lambda: select_input_file(decode_input_entry)).pack()

    tk.Label(decode_frame, text="Encryption Key:").pack(anchor="w")
    decode_key_entry = tk.Entry(decode_frame, width=40, show="*")
    decode_key_entry.pack()
    tk.Button(decode_frame, text="Load Key",
              command=lambda: decode_key_entry.insert(0, load_key_from_file().decode())).pack()

    message_label = tk.Label(decode_frame, text="Decoded message will appear here.")
    message_label.pack(pady=10)

    tk.Button(decode_frame, text="Decode Message",
              command=lambda: decode_message_ui(decode_input_entry, decode_key_entry, message_label)).pack()

    root.mainloop()


if __name__ == "__main__":
    create_gui()

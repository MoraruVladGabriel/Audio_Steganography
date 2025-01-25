import wave
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from pydub import AudioSegment


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


def encode_audio(input_audio_path, secret_message):
    """
    Encode a secret message into an audio file.

    :param input_audio_path: Path to the input audio file
    :param secret_message: The secret message to encode
    :return: Path to the output WAV file with the secret message encoded
    """
    wav_path = convert_to_wav(input_audio_path)

    with wave.open(wav_path, 'rb') as audio:
        params = audio.getparams()
        frames = audio.readframes(params.nframes)

        audio_data = np.frombuffer(frames, dtype=np.int16)

    secret_message_binary = ''.join(format(ord(char), '08b') for char in secret_message) + '00000000'

    if len(secret_message_binary) > len(audio_data):
        raise ValueError("The secret message is too large to encode in this audio file.")

    encoded_audio_data = audio_data.copy()
    for i, bit in enumerate(secret_message_binary):
        encoded_audio_data[i] = (encoded_audio_data[i] & ~1) | int(bit)

    output_audio_path = os.path.splitext(wav_path)[0] + "_encoded.wav"
    with wave.open(output_audio_path, 'wb') as encoded_audio:
        encoded_audio.setparams(params)
        encoded_audio.writeframes(encoded_audio_data.tobytes())

    return output_audio_path


def decode_audio(encoded_audio_path):
    """
    Decode a secret message from an audio file.

    :param encoded_audio_path: Path to the encoded WAV file
    :return: The decoded secret message
    """
    wav_path = convert_to_wav(encoded_audio_path)

    with wave.open(wav_path, 'rb') as audio:
        frames = audio.readframes(audio.getnframes())
        audio_data = np.frombuffer(frames, dtype=np.int16)

    bits = [str(sample & 1) for sample in audio_data]

    message_bytes = [bits[i:i + 8] for i in range(0, len(bits), 8)]
    message = ''
    for byte in message_bytes:
        char = chr(int(''.join(byte), 2))
        if char == '\x00':
            break
        message += char

    return message


def select_input_file(entry):
    file_path = filedialog.askopenfilename(filetypes=[("Audio files", "*.wav *.mp3 *.flac *.ogg *.aac *.m4a")])
    entry.delete(0, tk.END)
    entry.insert(0, file_path)


def encode_message_ui(input_entry, message_entry):
    input_path = input_entry.get()
    secret_message = message_entry.get()

    try:
        output_path = encode_audio(input_path, secret_message)
        messagebox.showinfo("Success", f"Message encoded successfully into {output_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def decode_message_ui(input_entry, message_label):
    input_path = input_entry.get()

    try:
        decoded_message = decode_audio(input_path)
        message_label.config(text=f"Decoded message: {decoded_message}")
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

    tk.Button(encode_frame, text="Encode Message", command=lambda: encode_message_ui(input_entry, message_entry)).pack(
        pady=10)

    # Decoding Section
    tk.Label(decode_frame, text="Decoding", font=("Arial", 14)).pack()

    tk.Label(decode_frame, text="Encoded Audio File:").pack(anchor="w")
    decode_input_entry = tk.Entry(decode_frame, width=40)
    decode_input_entry.pack()
    tk.Button(decode_frame, text="Browse", command=lambda: select_input_file(decode_input_entry)).pack()

    message_label = tk.Label(decode_frame, text="Decoded message will appear here.")
    message_label.pack(pady=10)

    tk.Button(decode_frame, text="Decode Message",
              command=lambda: decode_message_ui(decode_input_entry, message_label)).pack()

    root.mainloop()


if __name__ == "__main__":
    create_gui()

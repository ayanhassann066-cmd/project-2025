import wave, struct, math

# === Generate a simple short "pew" sound ===
file_name = "bullet_hit.wav"
sample_rate = 44100
duration = 0.2  # seconds
frequency = 600  # Hz

amplitude = 32767
n_samples = int(sample_rate * duration)

with wave.open(file_name, "w") as wav_file:
    wav_file.setparams((1, 2, sample_rate, n_samples, "NONE", "not compressed"))

    for i in range(n_samples):
        value = int(amplitude * math.sin(2 * math.pi * frequency * (i / sample_rate)))
        data = struct.pack("<h", value)
        wav_file.writeframesraw(data)

print(f"✅ Created '{file_name}' successfully in this folder!")

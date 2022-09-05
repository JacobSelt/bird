import sounddevice as sd
from scipy.io.wavfile import write
import datetime

FS = 44100      # Sample rate
SECONDS = 60    # Duration of recording


def main():
    # TODO: remove when deploying
    print("#####  Starting sound recording #####")

    while True:
        myrecording = sd.rec(int(SECONDS * FS), samplerate=FS, channels=2)
        sd.wait()
        write(f'input/{datetime.datetime.now().strftime("%H_%M_%S_%d_%m_%Y")}.wav',
              FS, myrecording)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Finished")

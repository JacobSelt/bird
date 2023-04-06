import sounddevice as sd
from scipy.io.wavfile import write
import datetime
# import noisereduce as nr
from decouple import config



FS = 44100      # Sample rate
SECONDS = 60    # Duration of recording

# ENV
INPUT_LOCATION = config("INPUT_LOCATION", default="input", cast=str)


def main():
    # TODO: remove when deploying
    print("#####  Starting sound recording #####")

    while True:
        myrecording = sd.rec(int(SECONDS * FS), samplerate=FS, channels=1)
        sd.wait()
        #myrecording = myrecording.flatten()
        #myrecording = nr.reduce_noise(y=myrecording, sr=FS)
        write(f'{INPUT_LOCATION}/{datetime.datetime.now().strftime("%H_%M_%S_%d_%m_%Y")}.wav',
              FS, myrecording)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Finished")

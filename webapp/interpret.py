from django.utils.timezone import make_aware
import time
import subprocess
import os
import django
import datetime
from pydub import AudioSegment
import noisereduce as nr
from scipy.io import wavfile


from dotenv import load_dotenv
load_dotenv()

# Set the django settings, so this script can access the django models
os.environ['DJANGO_SETTINGS_MODULE'] = 'webapp.settings'
django.setup()

from birds.models import Bird

interval_time = 120                 # seconds
RECORD_INTERVAL_TIME = 60           # seconds
INPUT_DIR = "../recordings/input"   # where the recorded .wav files are stored
OUTPUT_DIR = "../recordings/output" # location of saved result text files
TRANSLATE_FILE = "../recordings/translation.csv"

def translate_bird(en_name: str) -> str:
    """Translates the bird name from English to German
    
    Returns the German name and if there is a error, it returns 'Virginiauhu'
    """
    with open(TRANSLATE_FILE, "r") as file:
        lines = file.read().split("\n")
        temp = []

        for line in lines:
            # filter(..) eliminates the empty empty items
            temp.append(list(filter(None, line.split(","))))

        lines = temp[:-1]
    
    for line in lines:
        if line[1] == en_name:
            return line[0]
    
    return en_name #FIXME: return error code and act accordingly below


def get_time_recorded(file_name: str, recording_start: int) -> datetime.datetime:
    """Returns the exact time of bird call. 
    Gets the recording time from the file_name and the time passed from the recording start
    from recording_start
    """
    date_from_file = datetime.datetime.strptime(file_name[:19], "%H_%M_%S_%d_%m_%Y")
    date = date_from_file - \
        datetime.timedelta(seconds=RECORD_INTERVAL_TIME) + \
        datetime.timedelta(seconds=recording_start)
    
    return make_aware(date)


def save_audio_snippet(file_name: str, recording_start: int, recording_end: int, bird_name: str):
    newAudio = AudioSegment.from_wav(f"{INPUT_DIR}/{file_name}")
    newAudio = newAudio[(recording_start * 1000):(recording_end * 1000)]
    newAudio.export(
        f"birds/static/recordings_birds/{bird_name}.mp3", format="mp3")

    # sampleRate, waveData = wavfile.read(f"{INPUT_DIR}/{file_name}")
    # startSample = int( recording_start * sampleRate )
    # endSample = int( recording_end * sampleRate )
    # wavfile.write(f"../recordings/recordings_birds/{bird_name}.wav", sampleRate, waveData[startSample:endSample])


def check_if_bird_recording_exist_with_prob(bird_name: str, probability: float) -> bool:
    #TODO: Is the searching with Django or this approach faster?
    with open("../recordings/recordings_birds/recordings_birds_prob.csv", "w") as file:
        birds = file.read().split("\n")

def noise_reduction():
    for file in os.listdir(INPUT_DIR):
        rate, data = wavfile.read(f"{INPUT_DIR}/{file}")
        reduced_noise = nr.reduce_noise(y=data, sr=rate)
        wavfile.write(f"{INPUT_DIR}/{file}", rate, reduced_noise)


def main():
    # Starting the process and setting starting time
    started = time.time()

    while True:
        birds = []

        # During night (22:00 - 6:00) increase the interval time to 2 hours
        now = datetime.datetime.now().hour
        if now >= 22 or now < 6:
            interval_time = 7200
        else:
            interval_time = 120
        

        print("Removing noise")
        noise_reduction()
        print("Finished removing noise")

        # Get month for species detection
        week = str(now.isocalendar().week)
        if week > 48: week = 48

        # Analyze the files in the input folder
        subprocess.run(["python", "birds/birdnet/BirdNET-Analyzer/analyze.py",
                        "--i", INPUT_DIR, "--o", OUTPUT_DIR, "--lat", "47.971", "--lon",
                         "11.653", "--week", week],
        ) #stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) TODO ent-comment

        # The files in OUTPUT_DIR are the ones already analyzed -> save them, so 
        files_to_analyze = os.listdir(OUTPUT_DIR)

        # Extracting the birds from the results
        # Only birds with probability > 0.6 count TODO: what is good cutoff?
        for file_in_dir in os.listdir(OUTPUT_DIR):
            with open(f"{OUTPUT_DIR}/{file_in_dir}", "r") as file:
                text = file.read()
            lines = text.split("\n")[1:]
            if lines:
                for line in lines:
                    line = line.split("\t")
                    if line[0] != "" and float(line[9]) > 0.6:
                        birds.append({
                            "name": translate_bird(line[8]),
                            "prob": line[9],
                            "start": int(float(line[3])),
                            "end": int(float(line[4])),
                            "datetime": get_time_recorded(file_in_dir, int(float(line[3]))),
                            "file_name": f"{file_in_dir[0:19]}.wav",
                        })

            # Remove the output folders
            os.remove(f"{OUTPUT_DIR}/{file_in_dir}")

        # Make django Bird instances from the bird list
        for bird in birds:
            bird_obj = Bird(bird_id=-1,
                            bird_name=bird["name"],
                            recorded_datetime=bird["datetime"],
                            probability=bird["prob"])
            bird_obj.save()


            # # Save the audio file if the probability of the recording is the highest ever
            # if not Bird.objects.filter(bird_name=bird["name"]).filter(probability__gt=bird["prob"]):
            #     # TODO: Change the filter mechanism to a list
            #     save_audio_snippet(bird["file_name"], bird["start"], bird["end"], bird["name"])
            # else:
            #     pass


        # Delete the ANALYZED input sound files
        # The first 18 chars of the output files are the same as the input file names
        for f in files_to_analyze:
            os.remove(f"{INPUT_DIR}/{f[:19]}.wav")

        # Sleep for the remaining time interval
        time.sleep(interval_time -
                   ((time.time() - started) % interval_time))


try:
    main()
except KeyboardInterrupt:
    print("Finished")

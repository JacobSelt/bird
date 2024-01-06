from birdnetlib.watcher import DirectoryWatcher
from birdnetlib.analyzer import Analyzer #LiteAnalyzer
from datetime import datetime, timedelta
from pprint import pprint
import django
from django.utils.timezone import make_aware
import os
from decouple import config


# from dotenv import load_dotenv
# load_dotenv()

# Set the django settings, so this script can access the django models
os.environ['DJANGO_SETTINGS_MODULE'] = 'webapp.settings'
django.setup()

"""
TODO: ent-comment when deploying!
import sys
sys.path.append("/bin/ffmpeg")"""

from birds.models import Bird


# ENV
PATH_FOLDER = config("PATH_FOLDER", default="", cast=str)
INPUT_DIR =  PATH_FOLDER + "/recordings/input"   # where the recorded .wav files are stored
TRANSLATE_FILE = PATH_FOLDER + "/recordings/translation2.txt"
RECORD_INTERVAL_TIME = 60           # seconds


def get_week() -> int:
    """Returns the current week\n
    Weeks from 0 to 48 because this is obligatory by birdnetlib"""
    week = datetime.now().isocalendar().week
    if week > 48:
        week = 48
    return week


def load_translations() -> dict:
    """Load the translations from TRANSLATE_FILE\n
    
    Returns loaded dictionary of birds"""

    with open(TRANSLATE_FILE, "r") as file:
        # filter(..) eliminates the empty empty items
        lines = filter(None, file.read().split("\n"))

    # Key is Latin name and value the german name
    transl_dict = dict()

    for line in lines:
        # line is split by '_'. Example: 'Latin latin_Deutsch deutsch'
        temp = line.split("_")
        transl_dict[temp[0]] = temp[1]

    return transl_dict


def translate_bird(lat_name: str) -> str:
    """Translate the bird"""

    try:
        translation = BIRD_DICT[lat_name]
    except:
        translation = lat_name
        print(lat_name)
    
    return translation


def get_time_recorded(date_from_file: datetime, recording_start: int) -> datetime:
    """Returns the exact time of bird call. \n
    Gets the recording time from the file_name and the time passed from the recording start
    from recording_start
    """
    date = date_from_file - \
        timedelta(seconds=RECORD_INTERVAL_TIME) + \
        timedelta(seconds=recording_start)
    return make_aware(date)

def on_analyze_complete(recording):
    # Each analyzation as it is completed.
    pass

def save_audio_file(detection):
    pass


def on_analyze_file_complete(recording_list):
    # All analyzations are completed. Results passed as a list of Recording objects.
    for recording in recording_list:
        for detection in recording.detections:
            bird_obj = Bird(bird_id=-1,
                            bird_name=translate_bird(detection["scientific_name"]),
                            recorded_datetime=get_time_recorded(recording.date, detection["start_time"]),
                            probability=detection["confidence"])
            
            if detection["confidence"] > 0.95:
                save_audio_file(detection)

            bird_obj.save()

        # Deleting the analyzed file
        os.remove(f"{INPUT_DIR}/{recording.filename}")


def on_error(recording, error):
    print("An exception occurred: {}".format(error))
    print(recording.path)


def preanalyze(recording):
    # Used to modify the recording object before analyzing.
    filename = recording.filename
    dt = datetime.strptime(filename, "%H_%M_%S_%d_%m_%Y.wav")
    recording.date = dt


analyzer_lite = Analyzer()


directory = INPUT_DIR
watcher = DirectoryWatcher(
    directory,
    analyzers=[analyzer_lite],
    lon=11.653,
    lat=47.971,
    min_conf=0.6,
    week_48=get_week(),
)

BIRD_DICT = load_translations()

watcher.recording_preanalyze = preanalyze
watcher.on_analyze_complete = on_analyze_complete
watcher.on_analyze_file_complete = on_analyze_file_complete
watcher.on_error = on_error
watcher.watch()

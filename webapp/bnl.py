from birdnetlib.watcher import DirectoryWatcher
from birdnetlib.analyzer_lite import LiteAnalyzer
from datetime import datetime, timedelta
from pprint import pprint
import django
from django.utils.timezone import make_aware
import os

from dotenv import load_dotenv
load_dotenv()

# Set the django settings, so this script can access the django models
os.environ['DJANGO_SETTINGS_MODULE'] = 'webapp.settings'
django.setup()

from birds.models import Bird


INPUT_DIR = "../recordings/input"   # where the recorded .wav files are stored
TRANSLATE_FILE = "../recordings/translation2.txt"
RECORD_INTERVAL_TIME = 60           # seconds


def get_week():
    # Get month for species detection
    week = str(datetime.datetime.now().isocalendar().week)
    if week > 48:
        week = 48
    return week


def load_translations() -> dict:
    """Load the translations from TRANSLATE_FILE
    
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

    """
    #OLD TRANSLATION DOC

    global BIRD_DICT
    with open(TRANSLATE_FILE, "r") as file:
        lines = file.read().split("\n")
    temp = []

    for line in lines:
        # filter(..) eliminates the empty empty items
        temp.append(list(filter(None, line.split(","))))

    return temp[:-1]
    """
    
"""
def translate_bird(lat_name: str) -> str:
    #Translates the bird name from Latin to German
    
    #Returns the German name and if there is a error, it returns 'Virginiauhu'

    for line in BIRD_DICT:
        if line[1] == en_name:
            return line[0]

    return en_name  # FIXME: return error code and act accordingly below
"""


def get_time_recorded(date_from_file: datetime, recording_start: int) -> datetime:
    """Returns the exact time of bird call. 
    Gets the recording time from the file_name and the time passed from the recording start
    from recording_start
    """
    date = date_from_file - \
        timedelta(seconds=RECORD_INTERVAL_TIME) + \
        timedelta(seconds=recording_start)
    return make_aware(date)

def on_analyze_complete(recording):
    """print("on_analyze_complete")
    # Each analyzation as it is completed.
    print(recording.path, recording.analyzer.name)
    pprint(recording.detections)"""

    pass


def on_analyze_file_complete(recording_list):
    print("---------------------------")
    print("on_analyze_file_complete")
    print("---------------------------")
    # All analyzations are completed. Results passed as a list of Recording objects.
    for recording in recording_list:
        print(recording.filename, recording.date, recording.analyzer.name)
        for detection in recording.detections:
            bird_obj = Bird(bird_id=-1,
                            bird_name=BIRD_DICT[detection["scientific_name"]],
                            recorded_datetime=get_time_recorded(recording.date, detection["start_time"]),
                            probability=detection["confidence"])
            bird_obj.save()
        pprint(recording.detections)
        print("---------------------------")

        # Deleting the analyzed file
        os.remove(f"{INPUT_DIR}/{recording.filename}")


def on_error(recording, error):
    print("An exception occurred: {}".format(error))
    print(recording.path)


def preanalyze(recording):
    # Used to modify the recording object before analyzing.
    filename = recording.filename
    # 2022-08-15-birdnet-21:05:51.wav, as an example, use BirdNET-Pi's preferred format for testing.
    dt = datetime.strptime(filename, "%H_%M_%S_%d_%m_%Y.wav")
    # Modify the recording object here as needed.
    # For testing, we're changing the date. We could also modify lat/long here.
    recording.date = dt


print("Starting Analyzers")
analyzer_lite = LiteAnalyzer()
#analyzer = Analyzer()


print("Starting Watcher")
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
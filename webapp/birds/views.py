from datetime import datetime
from time import time
from django.shortcuts import render, redirect
from .models import Bird
from django.utils import timezone
import datetime
import pandas as pd
from django.forms.models import model_to_dict


from plotly.offline import plot
import plotly.graph_objects as go

PROB_TO_SHOW = 0.7


def get_date(hours_ago):
    time_x_hours_ago = timezone.now() - datetime.timedelta(hours=hours_ago)
    return time_x_hours_ago


def latest_birds(request):
    """Show the latest birds"""

    # TODO: when deploying change the hour count to 24
    birds = Bird.objects.filter(recorded_datetime__gt=get_date(10)).filter(probability__gt=PROB_TO_SHOW)
    birds = birds.order_by('-recorded_datetime')
    bird_df = pd.DataFrame(list(birds.values())) #TODO: make more efficient

    #bird_df = bird_df.groupby("bird_name")
    #bird_df = [[name, group] for name, group in bird_df]
    #print(bird_df)

    bird_list = []

    if len(bird_df) > 0:
        for bird in bird_df["bird_name"].unique():
            temp = bird_df.groupby(bird_df[bird_df["bird_name"] == bird]['recorded_datetime'].dt.hour).bird_name.count()

            bird_list.append({
                "name": bird,
                "count": len(bird_df[bird_df["bird_name"] == bird]),
                "dates": bird_df[bird_df["bird_name"] == bird]["recorded_datetime"],
                "last_call": bird_df[bird_df["bird_name"] == bird]["recorded_datetime"].iloc[0],
                "prob": 100*bird_df[bird_df["bird_name"] == bird]["probability"].mean(),
                "img": f"birds/{bird}.jpg" , #TODO: somehow get access to image_path
                "temp": temp,
            })
    else:
        pass
    

    context = {
        'birds': bird_list,
    }

    return render(request, 'birds/latest_birds.html', context)


def last_day(request):
    birds = Bird.objects.filter(
        recorded_datetime__gt=get_date(24)
        ).filter(
        probability__gt=PROB_TO_SHOW
        ).order_by(
        "-bird_name"
    )

    #TODO: make the conversion better and more eficcient
    data = {"Vogel": [bird.bird_name for bird in birds],
            "Date": [bird.recorded_datetime for bird in birds]}

    df = pd.DataFrame(data, columns=["Vogel", "Date"])

    bird_count = len(df["Vogel"].unique())
    if bird_count == 0: bird_count=10

    trace1 = go.Scatter(x=df["Date"],
                        y=df["Vogel"],
                        mode='markers',
                        marker=dict(size=8,
                                    line=dict(width=2,
                                              color='DarkSlateGrey')),
                        )

    layout = go.Layout(xaxis={'title': 'Stunden'},
                       hovermode='x',
                       margin={'t': 15, 'b': 10, 'r': 10, 'l': 10},
                       height=30*bird_count,
                       font={"size": 15},
                       modebar={"remove": ["zoom", "reset",
                                           "pan", "zoomin", "zoomout", "lasso", "autoscale", "select", "resetscale"]},
                       dragmode=False,
                       paper_bgcolor="#f3f3f3",
                       )
    figure = go.Figure(data=trace1, layout=layout)
    plot_div = figure.to_html(include_plotlyjs=False)

    context = {
        'plot_div': plot_div,
        'birds': birds,
    }

    return render(request, "birds/last_day_birds.html", context=context)


def search_bird(request):
    if request.method == "POST":
        bird = request.POST.get("bird")
        response = redirect(f"/{bird}/")
        return response
    else:
        pass


def bird_detail(request, bird_name):
    # Check if bird exists
    with open("../liste_vögel.txt", "r") as list_birds_file:
        list_birds = list_birds_file.read().split("\n")
        if bird_name not in list_birds:
            return render(request, "birds/bird_not_found.html",
                          context={"bird_name": bird_name, "error_img_path": "birds/bird_not_found.jpg"})

    # display last 50 birds
    birds = Bird.objects.filter(bird_name=bird_name).filter(
        probability__gt=PROB_TO_SHOW)
    last_birds = birds.order_by('-recorded_datetime')[0:50]

    # Hourly diagram of when bird is calling
    if len(birds):
        df = pd.DataFrame(list(birds.values()))
        df["month"] = pd.DatetimeIndex(df["recorded_datetime"]).month_name()
        df["hour"] = pd.DatetimeIndex(df["recorded_datetime"]).hour
        #print(df)

        # Grouping by the hour and count the bird callings
        df = df.groupby(['month', 'hour'],sort=False,as_index=False).count() #df.groupby(df['recorded_datetime'].dt.hour).bird_name.count()
 

        trace1 = go.Heatmap(
            x=df.hour,
            y=df.month,
            z=df.bird_name,
            connectgaps=True,
            zsmooth="best",
        )


        layout = go.Layout(xaxis={'title': 'Uhrzeit', "ticksuffix": ":00"},
                           yaxis={'title': 'Häufigkeit'},
                           hovermode='x',
                           margin={'t': 20, 'b': 10, 'r': 10, 'l': 20},
                           font={"size": 15},
                           modebar={"remove": ["zoom", "reset",
                                               "pan", "zoomin", "zoomout", "lasso", "autoscale", "select", "resetscale"]},
                           dragmode=False,
                           paper_bgcolor="#f3f3f3"
                           )
        figure = go.Figure(data=trace1, layout=layout)
        plot_div = figure.to_html(include_plotlyjs=False)
    else:
        plot_div = ""

    # TODO: display one example of how the bird is calling

    context = {
        'bird_pic_url': f"birds/{bird_name}.jpg",
        'bird_name': bird_name,
        'last_birds': last_birds,
        'plot_div': plot_div,
        'bird_audio': f"recordings_birds/{bird_name}.mp3",
    }

    return render(request, "birds/bird_detail.html", context=context)


def list_all_birds(request):
    birds = Bird.objects.all().filter(probability__gt=PROB_TO_SHOW)
    birds = pd.DataFrame(list(birds.values()))


    unique_birds = birds.bird_name.unique()
    output = []
    for bird in unique_birds:
        output.append(birds[birds["bird_name"] == bird].tail(1).values[0])

    output = pd.DataFrame(output)
    output = output.sort_values(by=[2])

    context = {
        "birds": output.values
    }

    return render(request, "birds/list_all_birds.html", context=context)


def show_most_frequent_birds(request):
    """Shows the most frequent birds in a time range (default is 24h) """
    time_range = 100000
    birds = Bird.objects.filter(recorded_datetime__gt=get_date(time_range)).filter(probability__gt=PROB_TO_SHOW)
    birds = pd.DataFrame(list(birds.values()))

    freq = birds["bird_name"].value_counts()

    context = {
        "freq": freq,
        "keys": freq.keys(),
    }

    return render(request, "birds/most_frequent_birds.html", context=context)


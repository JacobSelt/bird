from datetime import datetime
from time import time
from django.shortcuts import render, redirect
from .models import Bird
from django.utils import timezone
import datetime
import pandas as pd
from plotly_calplot import calplot
# from django.forms.models import model_to_dict
from decouple import config
import numpy as np


import plotly.graph_objects as go

# ENV
PROB_TO_SHOW = 0.7
HOURS_TO_SHOW = config("HOURS_TO_SHOW", default=24, cast=int)


def get_date(hours_ago):
    time_x_hours_ago = timezone.now() - datetime.timedelta(hours=hours_ago)
    return time_x_hours_ago


def latest_birds(request):
    """Show the latest birds"""

    # TODO: when deploying change the hour count to 24
    bird_df = pd.DataFrame.from_records(
        Bird.objects.filter(recorded_datetime__gt=get_date(HOURS_TO_SHOW/2))
        .filter(probability__gt=PROB_TO_SHOW)
        .order_by('-recorded_datetime')
        .values()
    )

    bird_list = []

    if len(bird_df) > 0:
        bird_df["recorded_datetime"] = bird_df["recorded_datetime"].dt.tz_convert(
            "Europe/Berlin")
        
        for bird in bird_df["bird_name"].unique():
            temp = bird_df.groupby(
                bird_df[bird_df["bird_name"] == bird]['recorded_datetime'].dt.hour).bird_name.count()

            bird_list.append({
                "name": bird,
                "count": len(bird_df[bird_df["bird_name"] == bird]),
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
    df = pd.DataFrame.from_records(
        Bird.objects.filter(recorded_datetime__gt=get_date(HOURS_TO_SHOW))
        .filter(probability__gt=PROB_TO_SHOW)
        .order_by("-bird_name")
        .values(),
        columns=["bird_name", "recorded_datetime"]
    )
    df["recorded_datetime"] = df["recorded_datetime"].dt.tz_convert(
        "Europe/Berlin")

    bird_count = len(df["bird_name"].unique())
    if bird_count != 0:
        trace1 = go.Scatter(x=df["recorded_datetime"],
                            y=df["bird_name"],
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
    else:
        plot_div=""

    context = {
        'plot_div': plot_div,
        'birds': bird_count,
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
    # ENV
    with open("../liste_vögel.txt", "r") as list_birds_file:
        list_birds = list_birds_file.read().split("\n")
        if bird_name not in list_birds:
            return render(request, "birds/bird_not_found.html",
                          context={"bird_name": bird_name, "error_img_path": "birds/bird_not_found.jpg"})

    # display last 50 birds
    df = pd.DataFrame.from_records(
        Bird.objects.filter(bird_name=bird_name)
        .filter(probability__gt=PROB_TO_SHOW)
        .order_by('-recorded_datetime')
        .values()
    )
    df["recorded_datetime"] = df["recorded_datetime"].dt.tz_convert(
        "Europe/Berlin")

    last_birds = df[0:50]


    # Hourly diagram of when bird is calling
    if len(df):
        df["hour"] = pd.DatetimeIndex(df["recorded_datetime"]).hour
        df["week"] = pd.to_datetime(df["recorded_datetime"]).dt.isocalendar().week

        df = df.groupby(['week', 'hour'], sort=True, as_index=False).count()[
            ['week', 'hour', "bird_name"]]

        # Make a blank df to fill the gaps
        weeks_zeros = np.sort(np.array([np.arange(1, 53) for _ in range(24)]).flatten())
        hours_zeros = np.array([np.arange(1,25) for _ in range(52)]).flatten()
        zeros = np.zeros(1248)
        data = {"week": weeks_zeros, "hour": hours_zeros, "bird_name": zeros}
        df_zeros = pd.DataFrame(data=data)

        # Combine the dfs
        df = df_zeros.merge(df, how="left", on=["week", "hour"]) \
                    .drop("bird_name_x", axis=1) \
                    .rename(columns={"bird_name_y":"freq"}) \
                    .fillna(0)
            
        heatmap_trace = go.Heatmap(
            x=df.hour,
            y=df.week,
            z=df.freq,
            connectgaps=True,
            zsmooth="best",
            colorscale='Picnic',
            showscale=False,
        )

        fig = go.Figure(go.Bar(
            x=df.week.unique(),
            y=df.set_index("week")["freq"].groupby("week").sum(),
            marker_color="rgb(0, 215, 29)",
        ))


        layout = go.Layout(#xaxis={'title': 'Uhrzeit', "ticksuffix": ":00"},
                           #yaxis={'title': 'Häufigkeit'},
                           hovermode='x',
                           margin={'t': 20, 'b': 10, 'r': 10, 'l': 20},
                           font={"size": 10},
                           modebar={"remove": ["zoom", "reset",
                                               "pan", "zoomin", "zoomout", "lasso", "autoscale", "select", "resetscale"]},
                           dragmode=False,
                           paper_bgcolor="#f3f3f3"
                           )
        figure = go.Figure(data=heatmap_trace, layout=layout)
        figure.update_yaxes(autorange="reversed")

        """ADD LINES TO TIME"""
        present_week = datetime.datetime.now().isocalendar().week

        fig.add_vline(
            x=present_week,
            line_width=1,
            line_color="red",
            annotation_text="Aktuelle Woche",
        )
        hour = datetime.datetime.now().hour
        figure.add_shape(
            type="circle",
            line_color='orange',
            x0=hour-1,
            y0=present_week,
            x1=hour,
            y1=present_week+1,
        )

        heatmap_plot = figure.to_html(include_plotlyjs=False)

        fig.update_layout(
            paper_bgcolor="#f3f3f3",
            modebar={"remove": ["zoom", "reset",
                                "pan", "zoomin", "zoomout", "lasso", "autoscale", "select", "resetscale"]},
            dragmode=False,
            margin={'t': 20, 'b': 10, 'r': 10, 'l': 20},
            height=170
        )
        week_plot = fig.to_html(include_plotlyjs=False)
    else:
        heatmap_plot = ""
        week_plot = ""

    # TODO: display one example of how the bird is calling

    context = {
        'bird_pic_url': f"birds/{bird_name}.jpg",
        'bird_name': bird_name,
        'last_birds': last_birds,
        'plot_div': heatmap_plot,
        'bird_audio': f"recordings_birds/{bird_name}.mp3",
        'plot_calplot': week_plot,
    }

    return render(request, "birds/bird_detail.html", context=context)


def list_all_birds(request):
    birds = Bird.objects.all().filter(probability__gt=PROB_TO_SHOW)
    birds = pd.DataFrame(list(birds.values()))

    #TODO: make faster


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

    figure = go.Figure(
        data=[go.Pie(labels=freq.keys(), values=freq)],
        layout=go.Layout(dragmode=False, margin={
                         't': 15, 'b': 10, 'r': 10, 'l': 10},),
    )
    figure.update_traces(textposition="inside")
    figure.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
    plot_div = figure.to_html(include_plotlyjs=False)

    context = {
        "freq": freq,
        "keys": freq.keys(),
        "plot_div": plot_div,
    }

    return render(request, "birds/most_frequent_birds.html", context=context)


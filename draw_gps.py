import numpy as np
import plotly.graph_objects as go


def draw_scatters(lats, lons, speeds):
    fig = go.Figure(go.Scattermapbox(
        # fill = "toself",
        lon=lons, lat=lats, mode='markers',
        marker=dict(size=4, autocolorscale=False,
                    colorscale=[[0, 'rgb(255,0,0)'], [0.3, "rgb(255, 255, 0)"],
                                [1, 'rgb(0,255,0)']],
                    cmin=0,
                    color=speeds,
                    cmax=20, reversescale=False,
                    colorbar_title="Speed (m/s)")))
    fig.update_layout(
        mapbox={
            'accesstoken': 'pk.eyJ1IjoieGluZ21pbnciLCJhIjoiY2tyZmNzeXI5NXY2bjJvcnUydmpsMDRhbCJ9.1hLwPieGHFDYK9aQcfkwyA',
            'style': "satellite-streets",
            'center': {'lon': np.average(lons), 'lat': np.average(lats)},
            'zoom': 12},
        showlegend=False, title_text="trip_id")
    fig.show()

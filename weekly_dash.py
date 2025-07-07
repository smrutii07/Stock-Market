import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go

# Load and prepare data
df = pd.read_parquet("weekly_data.parquet")
df = df.dropna(subset=["Date", "Open", "High", "Low", "Close", "Volume", "Ticker", 'EMA_High', 'EMA_Low'])
df["Ticker"] = df["Ticker"].str.strip().str.upper()
df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date")

tickers = sorted(df["Ticker"].unique())
fields = ["Open", "High", "Low", "Close", "Volume", 'EMA_High', 'EMA_Low']
date_labels = df["Date"].dt.strftime("%Y-%m-%d").tolist()

font_stack = (
    "system-ui, -apple-system, BlinkMacSystemFont, "
    "'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
)
custom_colors = ["#0f5499", "#9e2f50", "#6a737b", "#ffbc42", "#005f73", "#b08968"]

# Initialize app
app = Dash(__name__)
server = app.server  

app.layout = html.Div(
    style={"backgroundColor": "#fcd0b1", "minHeight": "100vh", "paddingBottom": "80px"},
    children=[
        html.Div(
            style={"width": "80%", "margin": "auto", "padding": "30px", "display": "flex", "flexDirection": "column"},
            children=[
                html.H1(
                    "Weekly Stock Trends",
                    style={
                        "fontFamily": font_stack,
                        "color": "#0f5499",
                        "marginBottom": "0",
                        "fontSize": "48px",
                    },
                ),
                html.P(
                    "1-Week Interval • Last 2 Years",
                    style={
                        "fontFamily": font_stack,
                        "color": "#333",
                        "marginTop": "0",
                        "marginBottom": "20px",
                    },
                ),
                html.Div(
                    style={
                        "display": "flex",
                        "gap": "40px",
                        "alignItems": "center",
                        "marginBottom": "25px",
                        "flexWrap": "wrap",
                    },
                    children=[
                        dcc.Dropdown(
                            tickers,
                            value=tickers[0],
                            id="ticker-dropdown",
                            style={"width": "250px", "fontSize": "18px"},
                        ),
                        dcc.Checklist(
                            options=[{"label": f, "value": f} for f in fields],
                            value=["Close"],
                            id="field-checklist",
                            inline=True,
                            inputStyle={"marginRight": "8px", "marginLeft": "16px"},
                            labelStyle={"marginRight": "20px", "fontFamily": font_stack, "fontSize": "20px"},
                        ),
                        html.Button("Download Data", id="download-button", n_clicks=0),
                        dcc.Download(id="download-dataframe-csv"),
                    ],
                ),
                html.Div(
                    id="ema-display",
                    style={
                        "marginTop": "20px",
                        "fontFamily": font_stack,
                        "fontSize": "20px",
                        "color": "#0f5499",
                    },
                ),
                dcc.Graph(
                    id="line-chart",
                    config={"displayModeBar": False},
                    style={"backgroundColor": "#fcd0b1"},
                ),
                # RANGESLIDER PLACED AT BOTTOM
                html.Div(
                    style={"marginTop": "50px", "paddingBottom": "40px"},
                    children=[
                        html.Label(
                            "Select Week Range:",
                            style={"fontSize": "22px", "fontFamily": font_stack, "color": "#0f5499"},
                        ),
                        dcc.RangeSlider(
                            id="date-range-slider",
                            min=0,
                            max=len(date_labels) - 1,
                            value=[0, len(date_labels) - 1],
                            marks={
                                i: {
                                    "label": date_labels[i],
                                    "style": {
                                        "transform": "rotate(45deg)",
                                        "fontSize": "16px",
                                        "whiteSpace": "nowrap",
                                        "color": "#0f5499",
                                    },
                                }
                                for i in range(0, len(date_labels), max(1, len(date_labels) // 10))
                            },
                            tooltip={"always_visible": False, "placement": "bottom"},
                            allowCross=False,
                            step=1,
                            updatemode="mouseup",
                            className="custom-slider",
                        ),
                    ],
                ),
            ],
        )
    ],
)

# Callback
@app.callback(
    Output("line-chart", "figure"),
    Output("ema-display", "children"),
    Output("download-dataframe-csv", "data"),
    Input("ticker-dropdown", "value"),
    Input("field-checklist", "value"),
    Input("date-range-slider", "value"),
    Input("download-button", "n_clicks"),
)
def update_chart(selected_ticker, selected_fields, selected_range, n_clicks):
    start_idx, end_idx = selected_range
    start_date = pd.to_datetime(date_labels[start_idx])
    end_date = pd.to_datetime(date_labels[end_idx])

    dff = df[(df["Ticker"] == selected_ticker) & (df["Date"] >= start_date) & (df["Date"] <= end_date)]

    fig = go.Figure()
    for i, fld in enumerate(selected_fields):
        fig.add_trace(
            go.Scatter(
                x=dff["Date"],
                y=dff[fld],
                mode="lines",
                name=fld,
                line=dict(width=2, color=custom_colors[i % len(custom_colors)]),
                hovertemplate=f"<b>{fld}</b><br>Date: %{{x}}<br>Value: %{{y:.2f}}<extra></extra>",
            )
        )

    fig.update_layout(
        template="none",
        paper_bgcolor="#fcd0b1",
        plot_bgcolor="#fcd0b1",
        title=selected_ticker,
        font=dict(family=font_stack, size=14, color="#222"),
        title_font=dict(size=20, color="#0f5499"),
        margin=dict(l=40, r=40, t=50, b=40),
        height=550,
        xaxis=dict(title="Date", showgrid=True, gridcolor="#ddd", linecolor="#333", ticks="outside"),
        yaxis=dict(title="Value", showgrid=True, gridcolor="#ddd", linecolor="#333", ticks="outside"),
        legend=dict(title="Field", orientation="h", yanchor="bottom", y=1.02),
        hoverlabel=dict(font_size=18),
    )

    if not dff.empty:
        latest_row = dff.loc[dff["Date"] == dff["Date"].max()].iloc[0]
        ema_text = f"Latest Week: {latest_row['Date'].strftime('%Y-%m-%d')} | EMA 48-Week High: {latest_row['EMA_High']:.2f} | EMA 48-Week Low: {latest_row['EMA_Low']:.2f}"
    else:
        ema_text = "No data in selected range."

    download_data = None
    if n_clicks > 0:
        download_data = dff.to_csv(index=False)

    return fig, ema_text, dict(content=download_data, filename=f"{selected_ticker}_weekly.csv") if download_data else None

# Add external styles if desired
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Weekly Stock Dashboard</title>
        {%favicon%}
        {%css%}
        <style>
        .custom-slider .rc-slider-rail {
            background-color: #0f5499;
        }
        .custom-slider .rc-slider-track {
            background-color: #0f5499;
        }
        .custom-slider .rc-slider-handle {
            background-color: #0f5499;
            border-color: #0f5499;
        }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Run app
if __name__ == "__main__":
    app.run(debug=True)

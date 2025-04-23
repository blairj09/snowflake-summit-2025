import chatlas, querychat, snowflake.connector, os
import polars as pl
import plotly.express as px

from pathlib import Path
from shiny import App, render, ui, reactive
from shinywidgets import output_widget, render_widget
from dotenv import load_dotenv
from distutils.util import strtobool

load_dotenv()

# Dataset - Snowflake Air Quality Data ----

snowflake_enabled = bool(strtobool(os.getenv("SNOWFLAKE", "False")))
if snowflake_enabled:
    conn = snowflake.connector.connect()
    cur = conn.cursor()
    cur.execute("select * from AIR_QUALITY_DATA_UNITED_STATES.PUBLIC.AIR_QUALITY")
    df = cur.fetch_pandas_all()
else:
    data_path = Path(__file__).parent / "data" / "air_quality_sample.csv"
    df = pl.read_csv(data_path)

# querychat config ----
with open(Path(__file__).parent / "greeting.md", "r") as f:
    greeting = f.read()
with open(Path(__file__).parent / "data_description.md", "r") as f:
    data_desc = f.read()
with open(Path(__file__).parent / "instructions.md", "r") as f:
    instructions = f.read()


def cortex_chat(system_prompt: str) -> chatlas.Chat:
    return chatlas.ChatSnowflake(model="claude-3-5-sonnet", system_prompt=system_prompt)


def anthropic_chat(system_prompt: str) -> chatlas.Chat:
    return chatlas.ChatAnthropic(
        model="claude-3-5-sonnet-latest", system_prompt=system_prompt
    )


querychat_config = querychat.init(
    df,
    "data",
    greeting=greeting,
    data_description=data_desc,
    create_chat_callback=anthropic_chat,
    extra_instructions=instructions,
)

# Additional data ----
parameter_choices = (
    df.group_by(pl.col("PARAMETERNAME"))
    .agg(pl.len())
    .sort("len", descending=True)["PARAMETERNAME"]
    .to_list()
)

state_abbreviations = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District Of Columbia": "DC",
}

# Shiny App ----
# Create UI
app_ui = ui.page_sidebar(
    # Create sidebar chat
    querychat.sidebar(
        "chat",
        ui.input_select(
            "parameter", "Air Quality Measurement", choices=parameter_choices
        ),
    ),
    # Main panel with data viewer and plots
    ui.layout_columns(
        # Row 1
        ui.card(ui.output_text("filtered_metric"), fill=True),
        # Row 2
        ui.card(output_widget("plot_map"), fill=True),
        # Row 3
        ui.card(output_widget("plot_line"), fill=True),
        # Row 4
        ui.card(output_widget("plot_hist"), fill=True),
        ui.card(output_widget("plot_scatter"), fill=True),
        # Row 5
        ui.card(ui.output_data_frame("data_table"), fill=True),
        col_widths=[12, 12, 6, 6, 12],
    ),
    title="US Air Quality",
    fillable=True,
)


# Define server logic
def server(input, output, session):
    # Initialize querychat server with the config from step 1
    chat = querychat.server("chat", querychat_config)

    # Create reactive value for dataframe
    @reactive.calc
    def df():
        return pl.from_dataframe(chat["df"]())

    @reactive.calc
    def filter_name():
        # We choose only the first value, assuming all values are the same.
        # This assumption is accurate except for when the application is first initialized
        return df().select("PARAMETERNAME").row(0)[0]

    @render.text
    def filtered_metric():
        return f"Applied Filter: {filter_name()}"

    @render_widget
    def plot_map():
        data = (
            df()
            .group_by("STATENAME")
            .agg(pl.col("ARITHMETICMEAN").mean())
            .with_columns(
                pl.col("STATENAME").replace(state_abbreviations).alias("STATEABB")
            )
        )

        map_output = px.choropleth(
            data,
            locations="STATEABB",
            locationmode="USA-states",
            color="ARITHMETICMEAN",
            scope="usa",
            color_continuous_scale="Viridis",
            title=f"Average {filter_name()} Levels by State",
            labels={"ARITHMETICMEAN": ""},
        )

        return map_output

    @render_widget
    def plot_line():
        data = (
            df()
            .group_by(["STATENAME", "YEAR"])
            .agg(pl.col("ARITHMETICMEAN").mean())
            .sort(["STATENAME", "YEAR"])
        )

        line_output = px.line(
            data,
            x="YEAR",
            y="ARITHMETICMEAN",
            color="STATENAME",
            title=f"Average {filter_name()} Trends by State",
            labels={
                "YEAR": "Year",
                "ARITHMETICMEAN": "Average Metric",
                "STATENAME": "State",
            },
        ).update_layout(showlegend=False)

        return line_output

    @render_widget
    def plot_hist():
        hist_output = px.histogram(
            data_frame=df(), x="ARITHMETICMEAN", title=f"{filter_name()} Distribution"
        )

        return hist_output

    @render_widget
    def plot_scatter():
        scatter_output = px.scatter(
            data_frame=chat["df"](),
            x="90THPERCENTILE",
            y="10THPERCENTILE",
            title=f"{filter_name()} Percentile Comparison",
            labels={"ARITHMETICMEAN": "Measurement Value"},
            color="PARAMETERNAME",
        ).update_layout(showlegend=False)

        return scatter_output

    @render.data_frame
    def data_table():
        # Access filtered data via chat.df() reactive
        return chat["df"]()


# Create Shiny app
app = App(app_ui, server)

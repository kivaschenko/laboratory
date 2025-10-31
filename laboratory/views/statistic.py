"""
Fixed version of statistic.py with improved Bokeh compatibility and error handling.
This addresses the RangeError issues with Bokeh 3.x and buffer alignment problems.
"""

import json
import decimal
import datetime
import logging
from math import pi

import colander
import deform
import pandas as pd
from bokeh.palettes import viridis, inferno
from bokeh.plotting import figure
from bokeh.transform import cumsum
from bokeh.models import ColumnDataSource
from bokeh.embed import components
from deform.exception import ValidationFailure

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPSeeOther
from sqlalchemy import text, desc, func
from sqlalchemy.exc import DBAPIError

from .. import models


def safe_create_bokeh_plot(data_frame, plot_type="pie"):
    """Safely create Bokeh plots with error handling."""
    try:
        if plot_type == "pie":
            return create_pie_chart(data_frame)
        elif plot_type == "bar":
            return create_bar_chart(data_frame)
    except Exception as e:
        logging.error(f"Bokeh plot creation failed: {e}")
        return (
            "",
            f"<div class='alert alert-warning'>Chart could not be generated due to compatibility issues.</div>",
        )


def create_pie_chart(df_subs):
    """Create pie chart with improved error handling."""
    try:
        # Ensure we have valid data
        if len(df_subs) == 0:
            return "", "<div>No data for chart</div>"

        # Calculate angles safely
        total_cost = df_subs["costs"].sum()
        if total_cost <= 0:
            return "", "<div>No positive cost data for chart</div>"

        df_subs = df_subs.copy()
        df_subs["angle"] = df_subs["costs"] / total_cost * 2 * pi

        # Ensure we have colors
        num_colors = len(df_subs)
        if num_colors <= 0:
            return "", "<div>No data for chart</div>"

        colors = viridis(max(3, num_colors))
        df_subs["color"] = colors[:num_colors]

        # Create ColumnDataSource with explicit data conversion
        source_data = {}
        for col in ["subs_name", "costs", "angle", "color"]:
            if col in df_subs.columns:
                source_data[col] = df_subs[col].tolist()

        source = ColumnDataSource(data=source_data)

        # Create figure
        pieplot = figure(
            height=600,
            sizing_mode="scale_both",
            title="Частки витрат речовин, грн.",
            toolbar_location=None,
            tools="hover",
            tooltips="@subs_name: @costs грн.",
        )

        # Add wedges
        pieplot.wedge(
            x=0,
            y=1,
            radius=0.4,
            line_color="white",
            start_angle=cumsum("angle", include_zero=True),
            end_angle=cumsum("angle"),
            fill_color="color",
            legend_field="subs_name",
            source=source,
        )

        # Style the plot
        pieplot.axis.axis_label = None
        pieplot.axis.visible = False
        pieplot.grid.grid_line_color = None
        if pieplot.legend:
            pieplot.legend.label_text_font_size = "7pt"

        script, div = components(pieplot)
        return script, div

    except Exception as e:
        logging.error(f"Pie chart creation failed: {e}")
        return (
            "",
            f"<div class='alert alert-warning'>Pie chart could not be generated: {str(e)}</div>",
        )


def create_bar_chart(df_an):
    """Create bar chart with improved error handling."""
    try:
        if len(df_an) == 0:
            return "", "<div>No analysis data for chart</div>"

        # Prepare data
        analysis_names = df_an["analysis"].tolist()
        numbers = df_an["numbers"].tolist()

        # Create source data
        source_data = {
            "analysis": analysis_names,
            "numbers": numbers,
            "cost": df_an["cost"].tolist(),
        }
        source = ColumnDataSource(data=source_data)

        # Create figure with categorical y-axis
        plot_an = figure(
            y_range=analysis_names,
            height=450,
            sizing_mode="scale_both",
            title="Кількість виконаних аналізів",
            toolbar_location=None,
            tools="hover",
            tooltips="@analysis: @numbers раз, @cost грн.",
        )

        # Add horizontal bars
        plot_an.hbar(
            y="analysis",
            right="numbers",
            height=0.8,
            alpha=0.5,
            source=source,
            color="green",
        )

        # Style the plot
        plot_an.axis.minor_tick_line_color = None

        # Set x-axis ticks if we have numbers
        max_numbers = max(numbers) if numbers else 0
        if max_numbers > 0:
            ticks = list(range(0, int(max_numbers) + 1, max(1, int(max_numbers) // 10)))
            plot_an.xaxis[0].ticker = ticks

        script, div = components(plot_an)
        return script, div

    except Exception as e:
        logging.error(f"Bar chart creation failed: {e}")
        return (
            "",
            f"<div class='alert alert-warning'>Bar chart could not be generated: {str(e)}</div>",
        )


@view_config(
    route_name="statistic",
    permission="create",
    renderer="../templates/statistic_form.jinja2",
)
def statistic_form(request):
    message = ""
    csrf_token = request.session.get_csrf_token()

    def validate_csrf(node, value):
        if value != csrf_token:
            raise ValueError("Bad CSRF token")

    class CSRFSchema(colander.Schema):
        csrf = colander.SchemaNode(
            colander.String(),
            default=csrf_token,
            validator=validate_csrf,
            widget=deform.widget.HiddenWidget(),
        )

    substances = []
    pie_script = ""
    pie_div = ""
    today = datetime.date.today()

    class StatisticSchema(CSRFSchema):
        begin_date = colander.SchemaNode(
            colander.Date(),
            title="Початок періоду",
            default=today,
            description="Включає день з 00:00",
        )
        end_date = colander.SchemaNode(
            colander.Date(),
            title="Кінець періоду",
            default=today,
            description="Не включає цей день",
        )

    schema = StatisticSchema().bind(request=request)
    button = deform.form.Button(type="submit", name="submit", title="Вибрати")
    form = deform.Form(schema, buttons=(button,))

    if "submit" in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            start = appstruct["begin_date"]
            end = appstruct["end_date"]

            # Query substances
            subs_query = (
                request.dbsession.query(
                    models.Stock.substance_name,
                    models.Stock.measurement,
                    models.Stock.amount,
                    models.Stock.total_cost,
                )
                .filter(models.Stock.amount < 0)
                .filter(models.Stock.creation_date >= start)
                .filter(models.Stock.creation_date < end)
                .all()
            )

            if len(subs_query) == 0:
                return {
                    "form": form,
                    "message": f"Немає даних за період: {start} - {end}",
                    "substances": [],
                    "piescript": "",
                    "piediv": "",
                    "subs_total": 0,
                    "analysis": [],
                    "barscript": "",
                    "bardiv": "",
                    "total_analysis": 0,
                    "sum_cost_analysis": 0,
                }

            # Process substances data
            data_records = []
            for row in subs_query:
                data_records.append(
                    {
                        "subs_name": str(row.substance_name),
                        "measurement": str(row.measurement),
                        "amount": float(row.amount) * -1,  # Convert to positive
                        "costs": float(row.total_cost) * -1,  # Convert to positive
                    }
                )

            df_subs = pd.DataFrame(data_records)

            # Group by substance and measurement
            df_subs = df_subs.groupby(["subs_name", "measurement"], as_index=False).agg(
                {"amount": "sum", "costs": "sum"}
            )

            subs_total_cost = df_subs["costs"].sum()

            # Create pie chart
            pie_script, pie_div = safe_create_bokeh_plot(df_subs, "pie")

            # Query analysis data
            analysis_sql = """SELECT analysis.recipe_name AS analysis,
                SUM (analysis.quantity) AS numbers,
                SUM (analysis.total_cost) AS cost
                FROM analysis
                WHERE analysis.done_date BETWEEN :x AND :y
                GROUP BY analysis.recipe_name ORDER BY numbers DESC"""

            analysis_q = request.dbsession.execute(
                text(analysis_sql), {"x": start, "y": end}
            ).fetchall()

            # Process analysis data
            analysis_records = []
            for row in analysis_q:
                analysis_records.append(
                    {
                        "analysis": str(row.analysis),
                        "numbers": float(row.numbers),
                        "cost": float(row.cost),
                    }
                )

            df_an = pd.DataFrame(analysis_records)

            if len(df_an) == 0:
                total_analysis = 0
                sum_cost_analysis = 0
                an_script = ""
                an_div = ""
            else:
                total_analysis = df_an["numbers"].sum()
                sum_cost_analysis = df_an["cost"].sum()

                # Create bar chart
                an_script, an_div = safe_create_bokeh_plot(df_an, "bar")

            return {
                "form": form,
                "message": f"Дані періоду: {start} - {end}",
                "substances": df_subs.to_dict("records"),
                "piescript": pie_script,
                "piediv": pie_div,
                "subs_total": subs_total_cost,
                "analysis": analysis_q,
                "barscript": an_script,
                "bardiv": an_div,
                "total_analysis": total_analysis,
                "sum_cost_analysis": sum_cost_analysis,
            }

        except ValidationFailure as e:
            return {
                "form": e,
                "message": "Помилки у формі",
                "substances": substances,
                "piescript": "",
                "piediv": "",
                "barscript": "",
                "bardiv": "",
            }
        except Exception as e:
            logging.error(f"Statistics processing error: {e}")
            return {
                "form": form,
                "message": f"Помилка обробки даних: {str(e)}",
                "substances": [],
                "piescript": "",
                "piediv": "",
                "barscript": "",
                "bardiv": "",
            }

    return {"form": form, "message": message}

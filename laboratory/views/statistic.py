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
from bokeh.transform import cumsum, dodge
from bokeh.models import ColumnDataSource
from bokeh.embed import components
from deform.exception import ValidationFailure

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPSeeOther
from sqlalchemy import text, desc, func
from sqlalchemy.exc import DBAPIError

from .. import models


# ===========================
# STATISTIC
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
                }
            else:
                df_subs = pd.DataFrame.from_records(
                    subs_query,
                    coerce_float=True,
                    columns=["subs_name", "measurement", "amount", "costs"],
                )
                df_subs["amount"] = df_subs["amount"] * -1
                df_subs["costs"] = df_subs["costs"] * -1
                df_subs = df_subs.groupby(["subs_name", "measurement"]).sum()
                df_subs.reset_index(inplace=True)
                subs_total_cost = df_subs["costs"].sum()
                # plot pie chart
                df_subs["angle"] = df_subs["costs"] / df_subs["costs"].sum() * 2 * pi
                num_colors = df_subs.shape[0]
                df_subs["color"] = viridis(num_colors)
                source = ColumnDataSource(data=df_subs)
                # Correcting the plot_height attribute to height
                pieplot = figure(
                    height=600,
                    sizing_mode="scale_both",
                    title="Частки витрат речовин, грн.",
                    toolbar_location=None,
                    tools="hover",
                    tooltips="@subs_name: @costs" + " грн.",
                    x_range=(-0.5, 1.0),
                )
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
                pieplot.axis.axis_label = None
                pieplot.axis.visible = False
                pieplot.grid.grid_line_color = None
                pieplot.legend.label_text_font_size = "7pt"
                pie_script, pie_div = components(pieplot)
                # analysis horizontal bar and table
                analysis_sql = """SELECT analysis.recipe_name AS analysis,
                    SUM (analysis.quantity) AS numbers,
                    SUM (analysis.total_cost) AS cost
                    FROM analysis
                    WHERE analysis.done_date BETWEEN :x AND :y
                    GROUP BY analysis.recipe_name ORDER BY numbers DESC"""
                analysis_q = request.dbsession.execute(
                    analysis_sql, {"x": start, "y": end}
                ).fetchall()
                df_an = pd.DataFrame.from_records(
                    analysis_q,
                    coerce_float=True,
                    columns=["analysis", "numbers", "cost"],
                )
                total_analysis = df_an["numbers"].sum()
                sum_cost_analysis = df_an["cost"].sum()
                source_num = ColumnDataSource(data=df_an)
                plot_an = figure(
                    y_range=df_an["analysis"].tolist(),
                    x_range=(0, df_an["numbers"].max()),
                    height=450,
                    sizing_mode="scale_both",
                    title="Кількість виконаних аналізів",
                    toolbar_location=None,
                    tools="hover",
                    tooltips="@analysis: @numbers раз, @cost грн.",
                )
                plot_an.hbar(
                    y=dodge("analysis", 0.0, range=plot_an.y_range),
                    right="numbers",
                    height=0.8,
                    alpha=0.5,
                    source=source_num,
                    color="green",
                )
                plot_an.y_range.range_padding = 0.1
                plot_an.axis.minor_tick_line_color = None
                ticks = [i for i in range(0, df_an["numbers"].max() + 1, 1)]
                plot_an.xaxis[0].ticker = ticks
                an_script, an_div = components(plot_an)
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
            return {"form": e, "message": "Помилки у формі", "substances": substances}
    return {"form": form, "message": message}


# ===============================================
# DRY MIXTURE

import json
import datetime
import logging

import colander
import deform
import pandas as pd
from deform.exception import ValidationFailure

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import DBAPIError

from .. import models
from .default import db_err_msg


# ========
# ANALYSIS


@view_config(
    route_name="add_analysis",
    permission="create",
    renderer="../templates/add_analysis.jinja2",
)
def add_done_analysis(request):
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

    id_recipe = request.matchdict["id_recipe"]
    query = request.dbsession.query(models.Recipe).get(id_recipe)
    recipe = query.__dict__
    recipe_name = recipe["name"]
    substances = ""
    solutions = ""
    if len(recipe["substances"]) > 0:
        substances = json.loads(recipe["substances"])
    if len(recipe["solutions"]) > 0:
        solutions = json.loads(recipe["solutions"])

    class AddAnalysisSchema(CSRFSchema):
        done_date = colander.SchemaNode(
            colander.Date(),
            title="Дата виконання",
            validator=colander.Range(
                min=datetime.date(datetime.date.today().year - 1, 1, 1),
                min_err=("${val} раніше чим дозволено мінімальну: ${min}"),
            ),
            default=datetime.date.today(),
        )
        quantity = colander.SchemaNode(
            colander.Integer(), title="кількість виконаних досліджень", default=1
        )

    schema = AddAnalysisSchema().bind(request=request)
    button = deform.form.Button(name="submit", type="submit", title="Записати")
    form = deform.Form(schema, buttons=(button,))
    if "submit" in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            done_date = appstruct["done_date"]
            quantity = appstruct["quantity"]
            # handling substances
            if isinstance(substances, dict):
                subsbstances_quantity = {
                    key: -value * quantity for key, value in substances.items()
                }
                substances_names = list(substances.keys())
                # check remainders
                query_stock = (
                    request.dbsession.query(models.Stock)
                    .filter(models.Stock.substance_name.in_(substances_names))
                    .all()
                )
                if len(query_stock) == 0:
                    message = f"На складі відсутні речовини!"
                    return {"form": form, "message": message, "recipe": recipe}
                else:
                    query_stock_dicts = [qs.__dict__ for qs in query_stock]
                    df = pd.DataFrame.from_records(query_stock_dicts)
                got_substances = df["substance_name"].unique().tolist()
                missing = set(substances_names) - set(got_substances)
                if len(missing) > 0:
                    missing_string = " ".join(missing)
                    message = f"Відсутні залишки: {missing_string}"
                    return {"form": form, "message": message, "recipe": recipe}
                # list to collect instances of class Stock: to_insert_into_stock
                insert_into_stock = []
                substances_cost = {}
                for key, value in subsbstances_quantity.items():
                    df_key = df[df.substance_name == key]
                    subs_measurement = df_key["measurement"].values[0]
                    sum_remainder = df_key["amount"].sum()
                    sum_remainder = sum_remainder.__float__()
                    if sum_remainder == 0.0:
                        message = "Залишок речовини '{key}' дорівнює 0! Неможливо \
    порахувати середню ціну, тому ділення на 0! Відкорегуйте залишок {key}".format(
                            key=key
                        )
                        return {"form": form, "message": message, "recipe": recipe}
                    new_remainder = sum_remainder + value
                    avg_price = df_key["total_cost"].sum() / df_key["amount"].sum()
                    avg_price = avg_price.__float__()
                    subs_total_cost = avg_price * value
                    subs_notes = f"Аналіз {recipe_name} в кількості: {quantity}"
                    new_stock = models.Stock(
                        substance_name=key,
                        measurement=subs_measurement,
                        amount=value,
                        remainder=new_remainder,
                        price=avg_price,
                        total_cost=subs_total_cost,
                        creation_date=done_date,
                        notes=subs_notes,
                        recipe=recipe_name,
                    )
                    insert_into_stock.append(new_stock)
                    substances_cost[key] = subs_total_cost
                total_substances_cost = [v for v in substances_cost.values()]
                total_substances_cost = sum(total_substances_cost) * -1
                substances_cost = json.dumps(substances_cost)
                for stock in insert_into_stock:
                    request.dbsession.add(stock)
            else:
                total_substances_cost = 0.0
                substances_cost = ""
            # handling solutions
            if isinstance(solutions, dict):
                solutions_quantity = {
                    key: -value * quantity for key, value in solutions.items()
                }
                solutions_names = [*solutions.keys()]
                query_solutions = (
                    request.dbsession.query(models.Solution)
                    .filter(models.Solution.normative.in_(solutions_names))
                    .all()
                )
                if len(query_solutions) == 0:
                    message = f"Немає готових розчинів для цього аналізу."
                    return {"form": form, "message": message, "recipe": recipe}
                else:
                    query_solutions_dicts = [qs.__dict__ for qs in query_solutions]
                    df2 = pd.DataFrame.from_records(query_solutions_dicts)
                got_solutions = df2["normative"].unique().tolist()
                missing = set(solutions_names) - set(got_solutions)
                if len(missing) > 0:
                    missing_string = " ".join(missing)
                    message = f"Відсутні залишки: {missing_string}"
                    return {"form": form, "message": message, "recipe": recipe}
                insert_into_solutions = []
                solutions_cost = {}
                for key, value in solutions_quantity.items():
                    df2_key = df2[df2.normative == key]
                    sol_measurement = df2_key["measurement"].values[0]
                    sol_remainder = df2_key["amount"].sum()
                    sol_remainder = sol_remainder.__float__()
                    if sol_remainder == 0.0:
                        message = "Залишок розчину '{key}' дорівнює 0! Неможливо \
    порахувати середню ціну, тому ділення на 0! Відкорегуйте залишок {key}".format(
                            key=key
                        )
                        return {"form": form, "message": message, "recipe": recipe}
                    new_remainder = sol_remainder + value
                    avg_price = df2_key["total_cost"].sum() / df2_key["amount"].sum()
                    avg_price = avg_price.__float__()
                    sol_total_cost = avg_price * value
                    sol_notes = f"Аналіз {recipe_name} в кількості: {quantity}"
                    new_solution = models.Solution(
                        normative=key,
                        measurement=sol_measurement,
                        amount=value,
                        remainder=new_remainder,
                        price=avg_price,
                        total_cost=sol_total_cost,
                        created_at=done_date,
                        notes=sol_notes,
                        recipe=recipe_name,
                    )
                    insert_into_solutions.append(new_solution)
                    solutions_cost[key] = sol_total_cost
                total_solutions_cost = [v for v in solutions_cost.values()]
                total_solutions_cost = sum(total_solutions_cost) * -1
                solutions_cost = json.dumps(solutions_cost)
                for sol in insert_into_solutions:
                    request.dbsession.add(sol)
            else:
                total_solutions_cost = 0.0
                solutions_cost = ""
            # create row for analysis
            this_analysis = models.Analysis(
                recipe_name=recipe_name,
                quantity=quantity,
                done_date=done_date,
                total_cost=abs(total_substances_cost + total_solutions_cost),
                substances_cost=substances_cost,
                solutions_cost=solutions_cost,
            )
            request.dbsession.add(this_analysis)
            next_url = request.route_url("analysis_done")
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {"form": e, "message": message, "recipe": recipe}
    return {"message": message, "recipe": recipe, "form": form}


@view_config(
    route_name="analysis_done",
    permission="create",
    renderer="../templates/analysis_done.jinja2",
)
def analysis_history(request):
    message = ""
    analysises = []
    try:
        query = request.dbsession.query(models.Analysis).all()
        analysises = [q.__dict__ for q in query]
    except DBAPIError:
        message = db_err_msg
    return {"analysises": analysises, "message": message}


@view_config(route_name="delete_analysis", permission="edit")
def delete_analysis(request):
    logging.info('Inside deleting analysis.')
    analysis_id = request.matchdict["analysis_id"]
    analysis_obj = request.dbsession.get(models.Analysis, analysis_id)
    logging.info('Analysis: %s', analysis_obj)
    analysis = analysis_obj.__dict__
    quantity = analysis.get("quantity")
    done_date = analysis.get("done_date")
    adopt_date = datetime.datetime(done_date.year, done_date.month, done_date.day)
    recipe_obj = (
        request.dbsession.query(models.Recipe)
        .filter_by(name=analysis["recipe_name"])
        .one()
    )
    recipe = recipe_obj.__dict__
    try:
        if substances := recipe.get("substances"):
            substances = json.loads(substances)
            logging.info('Substances: %s', substances)
            for name_ in substances:
                amount = -quantity * substances[name_]
                record = (
                    request.dbsession.query(models.Stock)
                    .filter_by(substance_name=name_)
                    .filter_by(amount=amount)
                    .filter_by(creation_date=adopt_date)
                    .one()
                )
                logging.info('Record will be deleted now: %s', record)
                request.dbsession.delete(record)
        else:
            pass
        if solutions := recipe.get("solutions"):
            solutions = json.loads(solutions)
            logging.info('Solutions: %s', solutions)
            for name_ in solutions:
                amount = -quantity * solutions[name_]
                record = (
                    request.dbsession.query(models.Solution)
                    .filter_by(normative=name_)
                    .filter_by(amount=amount)
                    .filter_by(created_at=done_date)
                    .one()
                )
                logging.info('Record will be deleted now: %s', record)
                request.dbsession.delete(record)
        else:
            pass
        # delete current analysis
        request.dbsession.delete(analysis_obj)
        logging.info('Completed deleting.')
    except Exception as exc:
        logging.error('Something went wrong durin deleting of analysis %s. Exception: %s', analysis_obj, exc)
    next_url = request.route_url("analysis_done")
    return HTTPFound(location=next_url)

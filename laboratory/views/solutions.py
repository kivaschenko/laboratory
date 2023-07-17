import json
import decimal
import datetime
import logging

import colander
import deform
import pandas as pd
from deform.exception import ValidationFailure

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPSeeOther
from sqlalchemy import text, desc
from sqlalchemy.exc import DBAPIError

from .. import models

# =========
# SOLUTIONS


@view_config(
    route_name="aggregate_solution",
    permission="create",
    renderer="../templates/aggregate_solution.jinja2",
)
def agregate_solution_remainder(request):
    message = ""
    solutions = []
    textual_sql = """SELECT solutions.normative AS normative, solutions.measurement AS measurement,
                SUM (solutions.amount) AS total_amount,
                AVG (solutions.price) AS avg_price,
                SUM (solutions.amount) * AVG (solutions.price) AS sum_cost
                FROM solutions
                GROUP BY solutions.normative, solutions.measurement"""
    try:
        query = request.dbsession.execute(text(textual_sql)).fetchall()
        solutions = [q for q in query]
        solutions_cleaned = []
        for sol in solutions:
            temp_dict = {}
            temp_dict["normative"] = sol[0]
            temp_dict["measurement"] = sol[1]
            temp_dict["total_amount"] = sol[2].__float__()
            temp_dict["avg_price"] = sol[3].__float__()
            temp_dict["sum_cost"] = sol[4]
            solutions_cleaned.append(temp_dict)
    except DBAPIError:
        message = db_err_msg
    return {"solutions": solutions_cleaned, "message": message}


@view_config(
    route_name="solutions",
    renderer="../templates/solutions.jinja2",
    permission="create",
)
def list_solutions(request):
    query = request.dbsession.query(models.Solution).all()
    # filter(text("remainder > 0")).\
    solutions = []
    if len(query) > 0:
        solutions = [q.__dict__ for q in query]
    return {"solutions": solutions}


@view_config(
    route_name="create_solution",
    permission="create",
    renderer="../templates/create_solution.jinja2",
)
def make_new_solution(request):
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

    normative_name = request.matchdict["normative"]
    current_normative = (
        request.dbsession.query(models.Normative)
        .filter(models.Normative.name == normative_name)
        .first()
    )
    current_normative = current_normative.__dict__
    current_measurement = ""
    curr_notes = ""
    if current_normative["type"] == "solution":
        current_measurement = "мл"
        curr_notes = f"Створено розчин {normative_name}"
    elif current_normative["type"] == "mixture":
        current_measurement = "г"
        curr_notes = f"Створено суміш {normative_name}"
    output = current_normative["output"].__float__()
    data_dict = json.loads(current_normative["data"])
    if isinstance(current_normative["solutions"], str):
        solutions = json.loads(current_normative["solutions"])
    else:
        solutions = None

    class SolutionSchema(CSRFSchema):
        amount = colander.SchemaNode(
            colander.Decimal(),
            validator=colander.Range(
                min=decimal.Decimal("0.000"), max=decimal.Decimal("1000000.000")
            ),
            title="Об'єм, вихід в мл або г відповідно типу",
            default=round(output, 3),
            description="Число у форматі 999999.999",
            widget=deform.widget.TextInputWidget(
                attributes={
                    "type": "numeric",
                    "inputmode": "decimal",
                    "step": "0.001",
                    "min": "0.000",
                    "max": "1000000.000",
                }
            ),
        )
        measurement = colander.SchemaNode(
            colander.String(),
            validator=colander.OneOf([x[0] for x in (("мл", "мл"), ("г", "г"))]),
            widget=deform.widget.RadioChoiceWidget(
                values=(("мл", "мл"), ("г", "г")), inline=True
            ),
            title="Одиниця виміру",
            default=current_measurement,
        )
        created_at = colander.SchemaNode(
            colander.Date(),
            validator=colander.Range(
                min=datetime.date(datetime.date.today().year - 1, 1, 1),
                max=datetime.date.today(),
                min_err=("${val} раніше чим дозволено мінімальну: ${min}"),
                max_err=("${val} пізніше ніж дозволено максимальну дату: ${max}"),
            ),
            title="Дата виготовлення",
            default=datetime.date.today(),
        )
        due_date = colander.SchemaNode(
            colander.Date(),
            validator=colander.Range(
                min=datetime.date(datetime.date.today().year - 1, 1, 1),
                min_err=("${val} раніше чим дозволено мінімальну: ${min}"),
            ),
            title="Дата придатності",
            default=datetime.date.today() + datetime.timedelta(days=15),
        )
        notes = colander.SchemaNode(
            colander.String(),
            title="Примітка",
            missing="",
            default="Створено новий розчин/суміш",
            validator=colander.Length(max=600),
            widget=deform.widget.TextAreaWidget(rows=5, cols=60),
            description="Необов'язково, до 600 символів з пробілами",
        )

    schema = SolutionSchema().bind(request=request)
    button = deform.form.Button(name="submit", type="submit", title="Зробити")
    form = deform.Form(schema, buttons=(button,))
    if "submit" in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            created_at = appstruct["created_at"]  # <- date for outcome substances
            due_date = appstruct["due_date"]
            notes = appstruct["notes"]
            amount = appstruct["amount"].__float__()
            measurement = appstruct["measurement"]
            coef = 1
            if amount != output:
                coef = amount / output
            if isinstance(coef, decimal.Decimal):
                coef = float(coef)
            # start handling substances quantity
            new_data = {key: -value * coef for key, value in data_dict.items()}
            substances_from_data = list(new_data.keys())
            query_stock = (
                request.dbsession.query(models.Stock)
                .filter(models.Stock.substance_name.in_(substances_from_data))
                .all()
            )
            if len(query_stock) == 0:
                message = f"На складі відсутні всі компоненти!"
                return {"form": form, "message": message, "normative": normative_name}
            else:
                substances_dicts = [qs.__dict__ for qs in query_stock]
                df = pd.DataFrame.from_records(substances_dicts)
            # check keys in df:
            needing_substances = set(new_data.keys())
            given_substances = df["substance_name"].unique().tolist()
            given_substances = set(given_substances)
            missing = needing_substances - given_substances
            if len(missing) > 0:
                missing_string = " ".join(missing)
                message = f"Відсутні залишки: {missing_string}"
                return {"form": form, "message": message, "normative": normative_name}
            new_records = []
            substances_cost = {}
            for key, value in new_data.items():
                df_key = df[df.substance_name == key]
                subs_measurement = df_key["measurement"].values[0]
                sum_remainder = df_key["amount"].sum()
                sum_remainder = sum_remainder.__float__()
                new_remainder = sum_remainder + value
                subs_price = df_key["total_cost"].sum() / df_key["amount"].sum()
                subs_price = subs_price.__float__()
                subs_total_cost = subs_price * value
                subs_notes = curr_notes
                new_stock = models.Stock(
                    substance_name=key,
                    measurement=subs_measurement,
                    amount=value,
                    remainder=new_remainder,
                    price=subs_price,
                    total_cost=subs_total_cost,
                    creation_date=created_at,
                    notes=subs_notes,
                    normative=normative_name,
                )
                new_records.append(new_stock)
                # define cost for each substance in this solution:
                substances_cost[key] = subs_total_cost
            for record in new_records:
                request.dbsession.add(record)
            total_substances_cost = [v for v in substances_cost.values()]
            total_substances_cost = sum(total_substances_cost) * -1
            # finish handling substances
            # start handling solutions quantity
            if solutions is None:
                total_solutions_cost = 0
            else:
                solutions_quantity = {
                    key: -value * coef for key, value in solutions.items()
                }
                solutions_names = [*solutions.keys()]
                query_solutions = (
                    request.dbsession.query(models.Solution)
                    .filter(models.Solution.normative.in_(solutions_names))
                    .all()
                )
                if len(query_solutions) == 0:
                    message = f"Немає готових розчинів для цього аналізу."
                    return {
                        "form": form,
                        "message": message,
                        "normative": normative_name,
                    }
                else:
                    query_solutions_dicts = [qs.__dict__ for qs in query_solutions]
                    df2 = pd.DataFrame.from_records(query_solutions_dicts)
                got_solutions = df2["normative"].unique().tolist()
                missing = set(solutions_names) - set(got_solutions)
                if len(missing) > 0:
                    missing_string = " ".join(missing)
                    message = f"Відсутні залишки: {missing_string}"
                    return {
                        "form": form,
                        "message": message,
                        "normative": normative_name,
                    }
                insert_into_solutions = []
                solutions_cost = {}
                for key, value in solutions_quantity.items():
                    df2_key = df2[df2.normative == key]
                    sol_measurement = df2_key["measurement"].values[0]
                    sol_remainder = df2_key["amount"].sum()
                    sol_remainder = sol_remainder.__float__()
                    if sol_remainder == 0.0:
                        message = f"Залишки {key} дорівнюють 0! \
    Неможливо порахувати середню ціну, тому що ділення на 0! Відкорегуйте залишок {key}."
                        return {
                            "form": form,
                            "message": message,
                            "normative": normative_name,
                        }
                    new_remainder = sol_remainder + value
                    avg_price = df2_key["total_cost"].sum() / df2_key["amount"].sum()
                    avg_price = avg_price.__float__()
                    sol_total_cost = avg_price * value
                    sol_notes = curr_notes
                    new_solution = models.Solution(
                        normative=key,
                        measurement=sol_measurement,
                        amount=value,
                        remainder=new_remainder,
                        price=avg_price,
                        total_cost=sol_total_cost,
                        created_at=created_at,
                        notes=sol_notes,
                        recipe=normative_name,
                    )
                    insert_into_solutions.append(new_solution)
                    solutions_cost[key] = sol_total_cost
                # new, to correct the reduction of residual solutions
                for record in insert_into_solutions:
                    request.dbsession.add(record)
                total_solutions_cost = [v for v in solutions_cost.values()]
                total_solutions_cost = sum(total_solutions_cost) * -1
            solution_price = round(
                (total_substances_cost + total_solutions_cost) / amount, 2
            )
            last_remainder = 0
            get_remainder = (
                request.dbsession.query(models.Solution.remainder)
                .filter(models.Solution.normative == normative_name)
                .order_by(desc(models.Solution.id))
                .first()
            )
            if get_remainder is not None:
                last_remainder += get_remainder[0].__float__()
            # add to solution model
            new_solution = models.Solution(
                normative=normative_name,
                measurement=measurement,
                amount=amount,
                remainder=last_remainder + amount,
                price=solution_price,
                total_cost=total_substances_cost + total_solutions_cost,
                created_at=created_at,
                due_date=due_date,
                notes=notes,
            )
            request.dbsession.add(new_solution)
            next_url = request.route_url("solutions")
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {"form": e, "normative": normative_name}
    return {"form": form, "normative": normative_name}


@view_config(
    route_name="correct_solution",
    permission="edit",
    renderer="../templates/correct_solution.jinja2",
)
def correct_solution(request):
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

    normative_name = request.matchdict["normative"]
    current_solution = (
        request.dbsession.query(models.Solution)
        .filter(models.Solution.normative == normative_name)
        .order_by(desc(models.Solution.id))
        .first()
    )
    current_solution = current_solution.__dict__
    curr_notes = f"Списано залишок"
    current_measurement = current_solution["measurement"]

    class SolutionSchema(CSRFSchema):
        amount = colander.SchemaNode(
            colander.Decimal(),
            default=-0.001,
            validator=colander.Range(
                min=-decimal.Decimal("1000000.000"), max=-decimal.Decimal("0.001")
            ),
            title="Кількість, {}".format(current_measurement),
            description="Число від -1000000.000 до -0.001",
            widget=deform.widget.TextInputWidget(
                attributes={
                    "type": "numeric",
                    "inputmode": "decimal",
                    "step": "-0.001",
                    "min": "-1000000.000",
                    "max": "-0.001",
                }
            ),
        )
        created_at = colander.SchemaNode(
            colander.Date(),
            validator=colander.Range(
                min=datetime.date(datetime.date.today().year - 1, 1, 1),
                max=datetime.date.today(),
                min_err=("${val} раніше чим дозволено мінімальну: ${min}"),
                max_err=("${val} пізніше ніж дозволено максимальну дату: ${max}"),
            ),
            title="Дата списання",
            default=datetime.date.today(),
        )
        notes = colander.SchemaNode(
            colander.String(),
            title="Примітка",
            missing="",
            default=curr_notes,
            validator=colander.Length(max=600),
            widget=deform.widget.TextAreaWidget(rows=5, cols=60),
            description="Необов'язково, до 600 символів з пробілами",
        )

    schema = SolutionSchema().bind(request=request)
    form = deform.Form(schema, buttons=("submit",))
    if "submit" in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            new_amount = appstruct["amount"].__float__()
            last_remainder = current_solution["remainder"].__float__()
            last_price = current_solution["price"].__float__()
            new_solution = models.Solution(
                normative=normative_name,
                measurement=current_measurement,
                amount=new_amount,
                remainder=last_remainder + new_amount,
                price=last_price,
                total_cost=abs(last_price * new_amount),
                created_at=appstruct["created_at"],
                notes=appstruct["notes"],
            )
            request.dbsession.add(new_solution)
            return HTTPSeeOther(request.route_url("solutions"))
        except ValidationFailure as e:
            return {"form": e, "current_solution": current_solution}
    return {"form": form, "current_solution": current_solution}


@view_config(route_name='delete_solution', permission='edit')
def delete_solution(request):
    logging.info('Inside deleting solution.')
    solution_id = request.matchdict.get('solution_id')
    solution_obj = request.dbsession.get(models.Solution, solution_id)
    print(solution_obj)
    breakpoint()
    logging.info('Solution: %s', solution_obj)
    norm = request.dbsession.query(models.Normative).filter_by(name=solution_obj).one()
    coef = solution_obj.amount / norm.output
    if substances := json.loads(norm.data):
        logging.info('Substances: %s', substances)
    if solutions := json.loads(norm.solutions):
        logging.info('Solutions: %s', solutions)
    next_url = request.route_url("solutions")
    return HTTPFound(location=next_url)
    
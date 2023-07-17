import decimal
import datetime
import logging

import colander
import deform
from deform.exception import ValidationFailure

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPSeeOther
from sqlalchemy import text, desc
from sqlalchemy.exc import DBAPIError

from .. import models
from .default import db_err_msg

# ===============
# SUBSTANCES
@view_config(
    route_name="add_substance",
    permission="create",
    renderer="../templates/add_substance.jinja2",
)
def new_substance(request):
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

    class SubstanceSchema(CSRFSchema):
        measure_types = (
            ("г", "грам"),
            ("мл", "міллілітр"),
            ("шт", "штука"),
        )
        name = colander.SchemaNode(colander.String(), title="Назва реактиву")
        measurement = colander.SchemaNode(
            colander.String(),
            widget=deform.widget.SelectWidget(values=measure_types),
            title="Одиниця виміру",
        )

    schema = SubstanceSchema().bind(request=request)
    button = deform.form.Button(name="submit", title="Створити", type="submit")
    form = deform.Form(schema, buttons=(button,), autocomplete="off")
    if request.method == "POST" and "submit" in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            certain_name = appstruct["name"]
            check_query = (
                request.dbsession.query(models.Substance)
                .filter(models.Substance.name == certain_name)
                .all()
            )
            if len(check_query) > 0:
                return {"message": "Така назва вже існує!", "form": form}
            new_substance = models.Substance(
                name=appstruct["name"], measurement=appstruct["measurement"]
            )
            request.dbsession.add(new_substance)
            next_url = request.route_url("substances")
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {"form": e.render(), "message": message}
    return {"message": message, "form": form.render()}


@view_config(route_name="delete_substance", permission="edit")
def delete_substance(request):
    subs_id = request.matchdict["subs_id"]
    subs = request.dbsession.query(models.Substance).get(subs_id)
    request.dbsession.delete(subs)
    next_url = request.route_url("substances")
    return HTTPFound(location=next_url)


@view_config(
    route_name="substances",
    renderer="../templates/substances.jinja2",
    permission="read",
)
def substances_list(request):
    query = (
        request.dbsession.query(models.Substance).order_by(models.Substance.name).all()
    )
    subs_list = []
    if len(query) > 0:
        subs_list = [q.__dict__ for q in query]
    return {"subs_list": subs_list}


@view_config(
    route_name="substances_edit",
    permission="edit",
    renderer="../templates/substances_edit.jinja2",
)
def substances_edit(request):
    query = (
        request.dbsession.query(models.Substance).order_by(models.Substance.name).all()
    )
    subs_list = []
    if len(query) > 0:
        subs_list = [q.__dict__ for q in query]
    return {"subs_list": subs_list}


# ========================
# STOCK
@view_config(
    route_name="buy_substance",
    permission="create",
    renderer="../templates/buy_substance.jinja2",
)
def input_substance(request):
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

    subs_query = request.dbsession.query(models.Substance).all()
    subs_list = []
    if len(subs_query) > 0:
        subs_list = [q.__dict__ for q in subs_query]
    else:
        message = "Каталог реактивів пустий! Неможливо створити форму прихода."
        return {"message": message}
    choices = [
        (subs["name"], subs["name"] + ", " + subs["measurement"]) for subs in subs_list
    ]

    class BuySchema(CSRFSchema):
        substance_name = colander.SchemaNode(
            colander.String(),
            title="Реактив (речовина, індикатор)",
            description="Вибреріть реактив (речовину, індикатор)",
            widget=deform.widget.SelectWidget(values=choices),
        )
        amount = colander.SchemaNode(
            colander.Decimal(),
            default=0.001,
            validator=colander.Range(
                min=-decimal.Decimal("1000000.000"), max=decimal.Decimal("1000000.000")
            ),
            title="Кількість",
            description="Число від -1000000.000 до 1000000.000 в залежності від напрямку - приход або розход",
            widget=deform.widget.TextInputWidget(
                attributes={
                    "type": "numeric",
                    "inputmode": "decimal",
                    "step": "0.001",
                    "min": "-1000000.000",
                    "max": "1000000.000",
                }
            ),
        )
        price = colander.SchemaNode(
            colander.Decimal(),
            default=0.01,
            validator=colander.Range(min=0, max=decimal.Decimal("9999.99")),
            title="Ціна, грн.",
            widget=deform.widget.TextInputWidget(
                attributes={
                    "type": "numeric",
                    "inputmode": "decimal",
                    "step": "0.01",
                    "min": "0",
                    "max": "9999.99",
                }
            ),
        )
        creation_date = colander.SchemaNode(
            colander.Date(),
            validator=colander.Range(
                min=datetime.date(datetime.date.today().year - 1, 1, 1),
                max=datetime.date.today(),
                min_err=("${val} раніше чим дозволено мінімальну: ${min}"),
                max_err=("${val} пізніше ніж дозволено максимальну дату: ${max}"),
            ),
            title="Дата приходу",
            default=datetime.date.today(),
        )
        notes = colander.SchemaNode(
            colander.String(),
            title="Примітка",
            default=" ",
            missing="",
            validator=colander.Length(max=600),
            widget=deform.widget.TextAreaWidget(rows=5, cols=60),
            description="Необов'язково, до 600 символів з пробілами",
        )

    schema = BuySchema().bind(request=request)
    button = deform.form.Button(
        name="submit", type="submit", title="Оприходувати на склад"
    )
    form = deform.Form(schema, buttons=(button,))
    if "submit" in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            substance_name = appstruct["substance_name"]
            certain_substance = (
                request.dbsession.query(models.Substance)
                .filter(models.Substance.name == substance_name)
                .first()
            )
            measurement = certain_substance.measurement
            amount = float(appstruct["amount"])
            price = float(appstruct["price"])
            total_cost = round(price * amount, 2)
            notes = "Приход на склад. " + str(appstruct["notes"])
            last_remainder = 0
            subs_ = (
                request.dbsession.query(models.Stock.remainder)
                .filter(models.Stock.substance_name == substance_name)
                .order_by(desc(models.Stock.id))
                .first()
            )
            if subs_ is not None:
                last_remainder += subs_[0].__float__()
            new_stock = models.Stock(
                substance_name=substance_name,
                measurement=measurement,
                amount=amount,
                remainder=last_remainder + amount,
                price=price,
                total_cost=total_cost,
                creation_date=appstruct["creation_date"],
                notes=notes,
            )
            request.dbsession.add(new_stock)
            next_url = request.route_url("stock_history")
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {
                "form": e.render(),
            }
    return {"form": form.render(), "message": message}


@view_config(
    route_name="stock_history",
    permission="create",
    renderer="../templates/stock_history.jinja2",
)
def stock_all_parties(request):
    message = ""
    query = (
        request.dbsession.query(models.Stock)
        .order_by(models.Stock.creation_date.desc())
        .all()
    )
    history = []
    if len(query) == 0:
        message = "Немає приходів і розходів. Історія складу пуста."
    history = [q.__dict__ for q in query]
    # for item in history:
    #     item['creation_date'] = item['creation_date'].strftime('%Y-%m-%d')
    subs = [item["substance_name"] for item in history]
    sorted(subs)
    subs = list(set(subs))
    return {"message": message, "history": history, "substances_list": subs}


@view_config(
    route_name="stock", renderer="../templates/stock.jinja2", permission="create"
)
def get_aggregate_stock(request):
    message = ""
    stock_list = []
    textual_sql = """
        SELECT stock.substance_name AS substance_name,
        stock.measurement AS measurement,
        SUM (stock.amount) AS total_amount,
        AVG (stock.price) AS avg_price,
        SUM (stock.amount) * AVG (stock.price) AS sum_cost
        FROM stock
        GROUP BY stock.substance_name,  stock.measurement"""
    try:
        query = request.dbsession.execute(text(textual_sql)).fetchall()
        stock_list = [q for q in query]
        stock_ = []
        for q in stock_list:
            temp_dict = {}
            (
                temp_dict["substance_name"],
                temp_dict["measurement"],
                temp_dict["total_amount"],
                temp_dict["avg_price"],
                temp_dict["sum_cost"],
            ) = q
            stock_.append(temp_dict)
    except DBAPIError:
        message = db_err_msg
    return {"stock_list": stock_, "message": message}

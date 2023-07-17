import json
import decimal
import logging

import colander
import deform
from deform.exception import ValidationFailure

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPSeeOther
from sqlalchemy import text, desc, func

from .. import models

# =======================
# NORMATIVES


@view_config(
    route_name="normative_list",
    permission="read",
    renderer="../templates/normative_list.jinja2",
)
def get_all_normatives(request):
    message = ""
    normative_query = (
        request.dbsession.query(models.Normative).order_by(models.Normative.name).all()
    )
    normative_list = []
    if len(normative_query) > 0:
        normative_list = [nq.__dict__ for nq in normative_query]
        for norm in normative_list:
            norm["data"] = json.loads(norm["data"])
            if isinstance(norm["solutions"], str):
                norm["solutions"] = json.loads(norm["solutions"])
            else:
                norm["solutions"] = {}
    else:
        message = "Немає нормативів у списку."
    return {"message": message, "normative_list": normative_list}


@view_config(
    route_name="normative_edit",
    permission="edit",
    renderer="../templates/normative_edit.jinja2",
)
def edit_normatives(request):
    message = ""
    normative_query = (
        request.dbsession.query(models.Normative).order_by(models.Normative.name).all()
    )
    normative_list = []
    if len(normative_query) > 0:
        normative_list = [nq.__dict__ for nq in normative_query]
        for norm in normative_list:
            norm["data"] = json.loads(norm["data"])
            if isinstance(norm["solutions"], str):
                norm["solutions"] = json.loads(norm["solutions"])
            else:
                norm["solutions"] = {}
    else:
        message = "Немає нормативів у списку."
    return {"message": message, "normative_list": normative_list}


@view_config(route_name="delete_normative", permission="edit")
def delete_normative(request):
    norm_id = request.matchdict["norm_id"]
    norm = request.dbsession.query(models.Normative).get(norm_id)
    request.dbsession.delete(norm)
    next_url = request.route_url("normative_list")
    return HTTPFound(location=next_url)


@view_config(
    route_name="new_normative",
    permission="create",
    renderer="../templates/new_normative.jinja2",
)
def new_normative(request):
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

    # create a list of all substances: choices
    subs_query = request.dbsession.query(models.Substance).all()
    subs_list = []
    if len(subs_query) > 0:
        subs_list = [q.__dict__ for q in subs_query]
    else:
        message = "Каталог реактивів пустий! Неможливо створити рецепт."
        return {"message": message}
    choices = [(subs["id"], subs["name"]) for subs in subs_list]
    # create a list of solutions that may be as components: choices_soluttions
    solut_query = (
        request.dbsession.query(models.Normative)
        .filter(models.Normative.as_subst == True)
        .order_by(models.Normative.name)
        .all()
    )
    solut_list = []
    if len(solut_query) > 0:
        solut_list = [q.__dict__ for q in solut_query]
    choices_soluttions = [(solut["id"], solut["name"]) for solut in solut_list]

    class NormativeSchema(CSRFSchema):
        name = colander.SchemaNode(colander.String(), title="Назва розчину")
        type = colander.SchemaNode(
            colander.String(),
            validator=colander.OneOf(
                [x[0] for x in (("solution", "розчин"), ("mixture", "суміш"))]
            ),
            widget=deform.widget.RadioChoiceWidget(
                values=(("solution", "розчин"), ("mixture", "суміш")), inline=True
            ),
            title="Тип",
        )
        as_subst = colander.SchemaNode(
            colander.Boolean(),
            description="відмітити якщо цей розчин використовується як складова частина іншого розчину",
            widget=deform.widget.CheckboxWidget(),
            title="Використовується як компонент",
        )
        output = colander.SchemaNode(
            colander.Decimal(),
            default=0.001,
            validator=colander.Range(
                min=decimal.Decimal("0.000"), max=decimal.Decimal("1000000.000")
            ),
            title="Об'єм, вихід в мл або г відповідно типу",
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
        data = colander.SchemaNode(
            colander.Set(),
            title="Речовини - відмітити необхідні:",
            widget=deform.widget.CheckboxChoiceWidget(values=choices),
        )
        solutions = colander.SchemaNode(
            colander.Set(),
            title="Розчини як компоненти - відмітити необхідні:",
            widget=deform.widget.CheckboxChoiceWidget(values=choices_soluttions),
        )

    schema = NormativeSchema().bind(request=request)
    button = deform.form.Button(name="submit", title="Далі", type="submit")
    form = deform.Form(schema, buttons=(button,), autocomplete="off")
    if request.method == "POST" and "submit" in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            certain_name = appstruct["name"]
            check_query = (
                request.dbsession.query(models.Normative)
                .filter(models.Normative.name == certain_name)
                .all()
            )
            if len(check_query) > 0:
                return {"message": "Така назва вже існує!", "form": form}
            next_url = request.route_url("new_norm_next", **appstruct)
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {"form": e, "message": message}
    return {"form": form, "message": message}


@view_config(
    route_name="new_norm_next",
    permission="create",
    renderer="../templates/new_norm_next.jinja2",
)
def new_norm_next(request):
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

    name_solution = request.matchdict["name"]
    output = request.matchdict["output"]
    solutions = request.matchdict["solutions"]
    solut_names = []
    if solutions != "set()":
        solutions = solutions.lstrip("{'").rstrip("'}").split("', '")
        list_solut_id = [int(d) for d in solutions]
        solut_query = (
            request.dbsession.query(models.Normative)
            .filter(models.Normative.id.in_(list_solut_id))
            .all()
        )
        solut_list = [sq.__dict__ for sq in solut_query]
        solut_names = [solut["name"] for solut in solut_list]
    if request.matchdict["as_subst"] == "True":
        as_subst = True
    else:
        as_subst = False
    type = request.matchdict["type"]
    s_type = "не визначений"
    measurement = "не визначений"
    if type == "solution":
        s_type = "розчин"
        measurement = "мл"
    elif type == "mixture":
        s_type = "суміш"
        measurement = "г"

    class NextFormSchema(CSRFSchema):
        def after_bind(self, schema, kwargs):
            req = kwargs["request"]
            data = req.matchdict["data"]
            data = data.lstrip("{'").rstrip("'}").split("', '")
            list_subs_id = [int(d) for d in data]
            subs_query = (
                request.dbsession.query(models.Substance)
                .filter(models.Substance.id.in_(list_subs_id))
                .all()
            )
            subs_list = [sq.__dict__ for sq in subs_query]
            for subs in subs_list:
                self[subs["name"]] = colander.SchemaNode(
                    colander.Decimal(),
                    title=subs["name"] + ", " + subs["measurement"],
                    default=0.001,
                    validator=colander.Range(min=0, max=decimal.Decimal("999999.999")),
                    widget=deform.widget.TextInputWidget(
                        attributes={
                            "type": "number",
                            "inputmode": "decimal",
                            "step": "0.001",
                            "min": "0",
                            "max": "999999.999",
                        }
                    ),
                )
            solutions = req.matchdict["solutions"]
            if solutions != "set()":
                solutions = solutions.lstrip("{'").rstrip("'}").split("', '")
                list_solut_id = [int(d) for d in solutions]
                solut_query = (
                    request.dbsession.query(models.Normative)
                    .filter(models.Normative.id.in_(list_solut_id))
                    .all()
                )
                solut_list = [sq.__dict__ for sq in solut_query]
                solut_names = [solut["name"] for solut in solut_list]
                for s_name in solut_names:
                    self[s_name] = colander.SchemaNode(
                        colander.Decimal(),
                        title=s_name + ", мл",
                        default=0.001,
                        validator=colander.Range(
                            min=0, max=decimal.Decimal("999999.999")
                        ),
                        widget=deform.widget.TextInputWidget(
                            attributes={
                                "type": "number",
                                "inputmode": "decimal",
                                "step": "0.001",
                                "min": "0",
                                "max": "999999.999",
                            }
                        ),
                    )

    schema = NextFormSchema().bind(request=request)
    button = deform.form.Button(name="submit", title="Створити рецепт", type="submit")
    form = deform.Form(schema, buttons=(button,))
    if request.method == "POST" and "submit" in request.POST:
        controls = request.POST.items()
        try:
            deserialized = form.validate(controls)
            deserialized.pop("csrf")
            if len(solut_names) > 0:
                new_solutions = {
                    k: float(v) for k, v in deserialized.items() if k in solut_names
                }
                new_solutions = json.dumps(new_solutions)
                new_data = {
                    k: float(v) for k, v in deserialized.items() if k not in solut_names
                }
                new_data = json.dumps(new_data)
            else:
                new_solutions = None
                new_data = {k: float(v) for k, v in deserialized.items()}
                new_data = json.dumps(new_data)
            new_normative = models.Normative(
                name=name_solution,
                type=type,
                as_subst=as_subst,
                output=output,
                data=new_data,
                solutions=new_solutions,
            )
            request.dbsession.add(new_normative)
            next_url = request.route_url("normative_list")
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {
                "form": e,
                "name_solution": name_solution,
                "s_type": s_type,
                "output": output,
                "measurement": measurement,
                "as_subst": as_subst,
            }
    return {
        "name": name_solution,
        "form": form,
        "message": message,
        "name_solution": name_solution,
        "s_type": s_type,
        "output": output,
        "measurement": measurement,
        "as_subst": as_subst,
    }

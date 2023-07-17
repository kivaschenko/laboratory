import json
import decimal
import datetime
import logging
from math import pi

import colander
import deform
from deform.exception import ValidationFailure

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound, HTTPSeeOther
from sqlalchemy import text, desc, func
from sqlalchemy.exc import DBAPIError

from .. import models

# ==================
# RECIPES
@view_config(
    route_name="recipes", renderer="../templates/recipes.jinja2", permission="read"
)
def all_recipes(request):
    message = ""
    query = (
        request.dbsession.query(models.Recipe.id, models.Recipe.name)
        .order_by(models.Recipe.name)
        .all()
    )
    if len(query) == 0:
        message = "Немає доданих рецептів аналізів."
    return {"recipes": query, "message": message}


@view_config(
    route_name="recipes_edit",
    renderer="../templates/recipes_edit.jinja2",
    permission="read",
)
def edit_recipes(request):
    message = ""
    query = (
        request.dbsession.query(models.Recipe.id, models.Recipe.name)
        .order_by(models.Recipe.name)
        .all()
    )
    if len(query) == 0:
        message = "Немає доданих рецептів аналізів."
    return {"recipes": query, "message": message}


@view_config(route_name="delete_recipe", permission="edit")
def delete_recipe(request):
    recipe_id = request.matchdict["recipe_id"]
    recipe = request.dbsession.query(models.Recipe).get(recipe_id)
    request.dbsession.delete(recipe)
    next_url = request.route_url("recipes")
    return HTTPFound(location=next_url)


@view_config(
    route_name="recipe_details",
    permission="read",
    renderer="../templates/recipe_details.jinja2",
)
def recipe_details(request):
    id_recipe = request.matchdict["id_recipe"]
    try:
        query = request.dbsession.query(models.Recipe).get(id_recipe)
        recipe = query.__dict__
        if len(recipe["substances"]) > 0:
            recipe["substances"] = json.loads(recipe["substances"])
        if len(recipe["solutions"]) > 0:
            recipe["solutions"] = json.loads(recipe["solutions"])
        return {"recipe": recipe}
    except DBAPIError:
        return Response(db_err_msg, content_type="text/plain", status=500)
    return {"recipe": recipe}


@view_config(
    route_name="new_recipe",
    permission="create",
    renderer="../templates/new_recipe.jinja2",
)
def new_recipe(request):
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
        message = "Каталог реактивів пустий! Неможливо створити рецепт."
        return {"message": message}
    substance_choices = [(subs["id"], subs["name"]) for subs in subs_list]
    solution_query = request.dbsession.query(models.Normative).all()
    solutions = []
    if len(solution_query) > 0:
        solutions = [q.__dict__ for q in solution_query]
    else:
        message = "Немає жодного розчину в базі даних! Створіть хоч би один."
        return {"message": message}
    solution_choices = [(item["id"], item["name"]) for item in solutions]

    class RecipeSchema(CSRFSchema):
        name = colander.SchemaNode(
            colander.String(),
            title="Назва аналізу",
            description="введіть унікальну назву аналізу",
        )
        substances = colander.SchemaNode(
            colander.Set(),
            title="Речовини",
            description="виберіть необхідні речовини",
            widget=deform.widget.CheckboxChoiceWidget(values=substance_choices),
        )
        solutions = colander.SchemaNode(
            colander.Set(),
            title="Розчини",
            description="виберіть потрібні розчини",
            widget=deform.widget.CheckboxChoiceWidget(values=solution_choices),
        )

    schema = RecipeSchema().bind(request=request)
    button = deform.form.Button(name="submit", title="Далі", type="submit")
    form = deform.Form(schema, buttons=(button,), autocomplete="off")
    if "submit" in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            certain_name = appstruct["name"]
            check_query = (
                request.dbsession.query(models.Recipe.name)
                .filter(models.Recipe.name == certain_name)
                .all()
            )
            if len(check_query) > 0:
                return {
                    "message": "Така назва аналізу вже існує!",
                    "form": form.render(),
                }
            next_url = request.route_url("new_recipe_next", **appstruct)
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {"form": e.render(), "message": message}
    return {"form": form.render(), "message": message}


@view_config(
    route_name="new_recipe_next",
    permission="create",
    renderer="../templates/new_recipe_next.jinja2",
)
def new_recipe_next(request):
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

    name_analysis = request.matchdict["name"]

    class NextRecipeSchema(CSRFSchema):
        name = colander.SchemaNode(
            colander.String(), title="Назва аналізу", default=name_analysis
        )

        def after_bind(self, schema, kwargs):
            req = kwargs["request"]
            substances = req.matchdict["substances"]
            if substances != "set()":
                substances = substances.lstrip("{'").rstrip("'}").split("', '")
                list_subs_id = [int(d) for d in substances]
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
            solutions = req.matchdict["solutions"]
            if solutions != "set()":
                solutions = solutions.lstrip("{'").rstrip("'}").split("', '")
                list_solut_id = [int(d) for d in solutions]
                solut_query = (
                    request.dbsession.query(models.Normative)
                    .filter(models.Normative.id.in_(list_solut_id))
                    .all()
                )
                solut_list = [st.__dict__ for st in solut_query]
                for solut in solut_list:
                    self[solut["name"]] = colander.SchemaNode(
                        colander.Decimal(),
                        title=solut["name"] + ", мл",
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

    schema = NextRecipeSchema().bind(request=request)
    button = deform.form.Button(
        name="submit", title="Створити новий аналіз", type="submit"
    )
    form = deform.Form(schema, buttons=(button,))
    subst_names = [s[0] for s in request.dbsession.query(models.Substance.name).all()]
    if "submit" in request.POST:
        controls = request.POST.items()
        try:
            deserialized = form.validate(controls)
            new_name = deserialized.pop("name")
            deserialized_keys = [i for i in deserialized.keys()]
            subst_here = set(subst_names) & set(deserialized_keys)
            substances = {}
            solutions = {}
            deserialized.pop("csrf")
            for key, value in deserialized.items():
                if key in subst_here:
                    substances[key] = float(value)
                else:
                    solutions[key] = float(value)
            if len(substances) > 0:
                substances = json.dumps(substances)
            else:
                substances = ""
            if len(solutions) > 0:
                solutions = json.dumps(solutions)
            else:
                solutions = ""
            new_recipe = models.Recipe(
                name=new_name, substances=substances, solutions=solutions
            )
            request.dbsession.add(new_recipe)
            next_url = request.route_url("recipes")
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {"form": e.render(), "message": "Перевірте поля форми"}
    return {"message": message, "form": form.render(), "name": name_analysis}

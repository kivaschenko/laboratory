import json
import decimal
import colander
import deform
from deform.exception import ValidationFailure
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import DBAPIError

from .. import models

#===============
# SUBSTANCES
@view_config(route_name='add_substance', 
             renderer='../templates/add_substance.jinja2')
def new_substance(request):
    message = ''
    measure_types = (
        ('г', 'грам'),
        ('мл', 'мілілітр'),
        ('шт', 'штука')
    )
    class SubstanceSchema(colander.Schema):
        name = colander.SchemaNode(colander.String(), title="Назва реактиву")
        measurement = colander.SchemaNode(colander.String(), 
                    widget=deform.widget.SelectWidget(values=measure_types),
                    title="Одиниця виміру")
    schema = SubstanceSchema().bind(request=request)
    button = deform.form.Button(name='submit', title="Створити", type='submit')
    form = deform.Form(schema, buttons=(button,), autocomplete='off')
    if request.method == 'POST' and 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            new_substance = models.Substance(
                name=appstruct['name'],
                measurement=appstruct['measurement']
            )
            request.dbsession.add(new_substance)
            next_url = request.route_url('substances')
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e, 'message': message}
    return {'message': message, 'form': form}


@view_config(route_name='delete_substance')
def delete_substance(request):
    subs_id = request.matchdict['subs_id']
    subs = request.dbsession.query(models.Substance).get(subs_id)
    request.dbsession.delete(subs)
    next_url = request.route_url('substances')
    return HTTPFound(location=next_url)


@view_config(route_name='substances', renderer='../templates/substances.jinja2')
def substances_list(request):
    query = request.dbsession.query(models.Substance).all()
    subs_list = []
    if len(query) > 0:
        subs_list = [q.__dict__ for q in query]
    return {"subs_list":subs_list}


#=======================
# SOLUTIONS
@view_config(route_name='solutions', renderer='../templates/solutions.jinja2')
def list_solutions(request):
    query = request.dbsession.query(models.Solution).all()
    solutions = []
    if len(query) > 0:
        solutions = [q.__dict__ for q in query]
    return {"solutions": solutions}


#=======================
# NORMATIVES

@view_config(route_name='normative_list', 
             renderer='../templates/normative_list.jinja2')
def get_all_normatives(request):
    message = ''
    normative_query = request.dbsession.query(models.Normative).order_by(models.Normative.id).all()
    normative_list = []
    if len(normative_query) > 0:
        normative_list = [nq.__dict__ for nq in normative_query]
        for norm in normative_list:
            norm['data'] = json.loads(norm['data'])
        print("normative_list --> ", normative_list)
    return dict(
        message=message,
        normative_list=normative_list
        )

@view_config(route_name='new_normative', 
             renderer='../templates/new_normative.jinja2')
def new_normative(request):
    message = ''
    subs_query = request.dbsession.query(models.Substance).all()
    subs_list = []
    if len(subs_query) > 0:
        subs_list = [q.__dict__ for q in subs_query] 
    else:
        message = 'Каталог реактивів пустий! Неможливо створити рецепт.'
        return {'message': message}
    choices = ( (subs['id'], subs['name']) for subs in subs_list )       
    class NormativeSchema(colander.Schema):
        name = colander.SchemaNode(colander.String(), title="Назва розчину")
        output = colander.SchemaNode(
            colander.Integer(),
            title="Об'єм вихід в мл", 
            description='Ціле число, наприклад 1000')
        data = colander.SchemaNode(
            colander.Set(), title="відмітити необхідні речовини",
            widget=deform.widget.CheckboxChoiceWidget(values=choices))
    schema = NormativeSchema().bind(request=request)
    button = deform.form.Button(name='submit', title="Далі", type='submit')
    form = deform.Form(schema, buttons=(button,), autocomplete='off')
    if request.method == 'POST' and 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            next_url = request.route_url('new_norm_next', **appstruct)
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return {'form': e, 'message': message}
    return {'form': form, 'message': message}


@view_config(route_name='new_norm_next',
             renderer='../templates/new_norm_next.jinja2')
def new_norm_next(request):
    message = ''
    name_solution = request.matchdict['name']
    output_ = request.matchdict['output']
    class NextFormSchema(colander.Schema):
        name = colander.SchemaNode(colander.String(), title="Назва розчину",
             default=name_solution)
        output = colander.SchemaNode(colander.Integer(), title="Об'єм вихід в мл", 
               default=int(output_))
        def after_bind(self, schema, kwargs):
            req = kwargs['request']
            data = req.matchdict['data']
            data = data.lstrip("{'").rstrip("'}").split("', '")
            list_subs_id = [int(d) for d in data]
            subs_query = request.dbsession.query(models.Substance)\
                       .filter(models.Substance.id.in_(list_subs_id)).all()
            subs_list = [sq.__dict__ for sq in subs_query]
            for subs in subs_list:
                self[subs['name']] = colander.SchemaNode(colander.Decimal(),
                    title=subs["name"] + ', '+subs["measurement"], 
                    default=0.01,
                    validator=colander.Range(min=0, 
                            max=decimal.Decimal("999.99")),
                    widget=deform.widget.TextInputWidget(
                        attributes={
                            "type": "number",
                            "inputmode": "decimal",
                            "step": "0.01",
                            "min": "0",
                            "max": "999.99"
                        })
                    )
    schema = NextFormSchema().bind(request=request)
    button = deform.form.Button(name='submit', title="Створити рецепт", 
                                type='submit')
    form = deform.Form(schema, buttons=(button,))
    appstruct = {'name': name_solution, 'output': output_}
    if request.method == 'POST' and 'submit' in request.POST:
        controls = request.POST.items()
        try:
            deserialized = form.validate(controls)
            print('try appstruct --> ', deserialized)
# {'name': 'Новий рецепт розчину', 'output': 1000, 'Кислота сірчана концентрована': Decimal('198.80'), 'Вода H2O': Decimal('801.2')}
            new_name = deserialized.pop('name')
            new_output = deserialized.pop('output')
            print("deserialized --> ", deserialized)
            new_data = {k: float(v) for k, v in deserialized.items()}
            new_data = json.dumps(new_data)
            print("new_data --> ", new_data)
            new_normative = models.Normative(
                name=new_name,
                output=new_output,
                data=new_data
                )
            request.dbsession.add(new_normative)
            next_url = request.route_url('normative_list')
            return HTTPFound(location=next_url)
        except ValidationFailure as e:
            return dict(
                form=e.render()
                )
    return dict(
        name=name_solution,
        form=form.render(appstruct)
    )

#===================
# HOME
@view_config(route_name='home', renderer='../templates/home.jinja2')
def my_view(request):
    try:
        query = request.dbsession.query(models.Substance)
        one = query.filter(
            models.Substance.name == "Вода H2O").first()
        one = one.__dict__
    except DBAPIError:
        return Response(db_err_msg, content_type='text/plain', status=500)
    return {'one': one, 'project': 'програма для обліку реактивів'}


db_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to initialize your database tables with `alembic`.
    Check your README.txt for descriptions and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

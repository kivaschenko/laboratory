
from pyramid.httpexceptions import HTTPFound
from deform.exception import ValidationFailure
from pyramid.view import (
    view_config,
    forbidden_view_config
)
from pyramid.security import (
    remember,
    forget
    )
import colander
import deform

from ..models import User


@view_config(renderer='../templates/login.jinja2', route_name='login')
def login(request):
    next_url = request.route_url('home')
    message = ''
    csrf_token = request.session.get_csrf_token()
    def validate_csrf(node, value):
        if value != csrf_token:
            raise ValueError("Bad CSRF token")
    class CSRFSchema(colander.Schema):
        csrf = colander.SchemaNode(
            colander.String(),
            default=csrf_token,
            validator=validate_csrf,
            widget=deform.widget.HiddenWidget()
    )   
    class LoginSchema(CSRFSchema):
        username = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(max=100),
                widget=deform.widget.TextInputWidget())
        password = colander.SchemaNode(
                colander.String(),
                validator=colander.Length(min=5, max=100),
                widget=deform.widget.PasswordWidget(redisplay=True))
    schema = LoginSchema()
    form = deform.Form(schema, buttons=('submit',))
    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
            username = appstruct['username']
            password = appstruct['password']
            user = request.dbsession.query(User).filter_by(nickname=username).first()
            # check password
            if user is not None and user.check_password(password):
                headers = remember(request, user.id)
                return HTTPFound(location=next_url, headers=headers)
            else:
                headers = forget(request)
                message = 'Failed login or password!'
        except ValidationFailure as e:
            return {'form': e, 'message': message}
    return {'form': form, 'message':message}


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    next_url = request.route_url('home')
    return HTTPFound(location=next_url, headers=headers)


@forbidden_view_config()
def forbidden_view(request):
    next_url = request.route_url('login', _query={'next': request.url})
    return HTTPFound(location=next_url)

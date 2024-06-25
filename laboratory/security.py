from pyramid.authorization import Allow, Everyone, Authenticated
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from .models import User

class LabFactory(object):
    def __acl__(self):
        return [(Allow, Everyone, 'read'),
            (Allow, Authenticated, 'create'),
            (Allow, Authenticated, 'edit')]
    def __init__(self, request):
        pass

class MyAuthenticationPolicy(AuthTktAuthenticationPolicy):
	def authenticated_userid(self, request):
		user = request.user
		if user is not None:
			return user.id


def get_user(request):
	user_id = request.unauthenticated_userid
	if user_id is not None:
		user = request.dbsession.query(User).get(user_id)
		return user

def includeme(config):
	settings = config.get_settings()
	auth_policy = MyAuthenticationPolicy(
				settings['auth.secret'], hashalg='sha512',)
	config.set_authentication_policy(auth_policy)
	authz_policy = ACLAuthorizationPolicy()
	config.set_authorization_policy(authz_policy)
	config.add_request_method(get_user, 'user', reify=True)
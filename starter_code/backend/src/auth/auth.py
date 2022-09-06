import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen

AUTHO_DOMAIN = 'dev-kaz9ci7y.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'drinks'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

    

## Auth Header

'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''
def get_token_auth_header():
    if "Authorization" not in request.headers:
        raise AuthError({
            "error": "Authorization_not_defined",
            "description":"header not present in your request"
        }, 401)
    request_body = request.headers["Authorization"]
    parts = request_body.split(' ')
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthError({
            "error": "invalid_header",
            "description": "header malformed and should contain 'Bearer' "
        }, 401)

    return parts[1]

'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({
            "error":"bad request",
            "description":"not able to verify the issuer"
        }, 400)
    if permission not in payload['permissions']:
        raise AuthError({
            "error":"permission denied",
            "description":"the issuer doesn't have the right to login"
        }, 403)
    return True

'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    jsonurl = urlopen(f'https://{AUTHO_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())

    unverified_header = ""
    try:
        unverified_header = jwt.get_unverified_header(token)
    except:
        raise AuthError({
            "error": "invalid token",
            "description": "token is malformed"
        }, 401)
    

    rsa_key = {}

    if 'kid' not in unverified_header:
        raise AuthError({
           "error": "invalid_header",
           "description":"header malformed" 
        }, 401)
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key['kty'] = key['kty']
            rsa_key['kid'] = key['kid']
            rsa_key['use'] = key['use']
            rsa_key['n'] = key['n']
            rsa_key['e'] = key['e']
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer=f'https://{AUTHO_DOMAIN}/'
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError({
                "error":"expired token",
                "description":"the provided token is expired"
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                "error":"invalid_claims",
                "description":"Incorrect claims, please check the Audience and the Issuer."
            }, 401)
        except Exception:
            raise AuthError({
                "error":"invalid_header",
                "descrription":"Unable to parse authentication key."
            }, 400)
    raise AuthError({
        "error": "Invalid_header",
        "description":"Unable to find the appropriate key."
    }, 400)

'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator

   
from flask import Flask
from flask import redirect, request, session, make_response
from oidc import get_oidc_client
from oic import rndstr
import yaml
from oic.oic.message import AuthorizationResponse
import base64
import argparse


def create_app(config_path):
    with open(config_path, 'r') as f:
        config = yaml.load(f)

    app = Flask(__name__)
    app.secret_key = base64.b64decode(bytes(config['flask_secret_key'], encoding='utf-8'))
    
    oidc_client = get_oidc_client(
        issuer=config['oidc']['issuer'],
        client_id=config['oidc']['client_id'],
        client_secret=config['oidc']['client_secret'],
        redirect_uri=config['oidc']['redirect_uri'],
    )


    '''
        redirect to idp to get access code
        if login successfully, rediret to /callback
    '''
    @app.route('/')
    def login():
        session['nonce'] = rndstr()
        session['state'] = rndstr()
    
        args = {
            "response_type": ["code"],
            "scope": ["openid", 'email', 'profile', 'offline_access'],
            "redirect_uri": config['oidc']['redirect_uri'],
            "nonce": session['nonce'],
            "state": session['state'],
        }
    
        auth_req = oidc_client.construct_AuthorizationRequest(request_args=args)
        login_url = auth_req.request(oidc_client.authorization_endpoint)
        
        return redirect(login_url)


    '''
        callback code to exchange token
        return command to configure kubeconfig
    '''
    @app.route('/callback')
    def callback():
        aresp = oidc_client.parse_response(
            AuthorizationResponse,
            info=request.query_string.decode('utf-8'),
            sformat="urlencoded"
        )
    
        assert aresp['state'] == session['state']
    
        args = {
            "code": aresp['code']
        }
        
        resp = oidc_client.do_access_token_request(
            state=aresp['state'],
            request_args=args,
            authn_method="client_secret_basic",
            client_secret=config['oidc']['client_secret'],
        )
        
        id_token = resp.raw_id_token
        user_email = resp['id_token']['email']
    
        response_format = 'cat << EOF > ~/.kube/config\n{}\nEOF'
        kubeconfig = yaml.dump(
            {
                'apiVersion': 'v1',
                'clusters': [
                    {
                        'cluster': {
                            'certificate-authority-data': config['cluster']['ca'],
                            'server': config['cluster']['host']
                        },
                        'name': config['cluster']['name']
                    }
                ],
                'contexts': [
                    {
                        'context': {
                            'cluster': config['cluster']['name'],
                            'user': user_email
                        },
                        'name': user_email
                    }
                ],
                'current-context': user_email,
                'kind': 'Config',
                'preferences': {},
                'users': [
                    {
                        'name': user_email,
                        'user': {
                            'auth-provider': {
                                'config': {
                                    'client-id': config['oidc']['client_id'],
                                    'id-token': id_token,
                                    'idp-issuer-url': config['oidc']['issuer']
                                },
                                'name': 'oidc'
                            }
                        }
                    }
                ]
            }, 
            default_flow_style=False,
        )
    
        response = make_response(response_format.format(kubeconfig), 200)
        response.mimetype = 'text/plain'
        return response


    @app.route('/ping')
    def ping():
        return '', 200


    return app

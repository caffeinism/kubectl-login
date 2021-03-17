from oic.oic import Client                            
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from oic.oic.message import RegistrationResponse      
                                                      
def get_oidc_client(
    issuer,
    client_id,
    client_secret,
    redirect_uri,
):
    client = Client(                                  
        client_id=client_id,                          
        client_authn_method=CLIENT_AUTHN_METHOD       
    )                                                 
                                                      
    client.provider_config(issuer)                    
                                                      
    info = {                                          
        "client_id": client_id,                       
        "client_secret": client_secret,               
    }                                                 
                                                      
    client_reg = RegistrationResponse(**info)         
    client.store_registration_info(client_reg)        

    client.redirect_uris = [redirect_uri]
                                                      
    return client                                     


# Inside your accounts/microsoft.py file:
import msal

SCOPES = ["User.Read"]

def build_msal_app(client_id, client_secret, tenant_id):
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    return msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret,
    )

def get_auth_url(client_id, tenant_id, redirect_uri):
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(client_id, authority=authority)
    return app.get_authorization_request_url(SCOPES, redirect_uri=redirect_uri)
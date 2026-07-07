import msal
from django.conf import settings

SCOPES = ["User.Read"]

def build_msal_app():
    return msal.ConfidentialClientApplication(
        settings.MS_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{settings.MS_TENANT_ID}",
        client_credential=settings.MS_CLIENT_SECRET,
    )

def get_auth_url():
    app = build_msal_app()
    return app.get_authorization_request_url(
        scopes=SCOPES,
        redirect_uri=settings.MS_REDIRECT_URI,
    )
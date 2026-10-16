from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.utils import build_absolute_uri
from django.conf import settings

from apps.accounts.models import OAuthConnection
from apps.accounts.signup_links import custom_signup_url, pending_invite_email
from apps.common.mail import transactional


def signup_allowed(request):
    """Whether a brand-new account may be created for this request, per ``SIGNUP_MODE``.

    Only ever asked when an account would actually be created. Signing in
    with an existing account — including a social login that connects to an
    existing user by email — does not pass through here. In invite mode the
    visitor must carry a still-open invitation (see ``pending_invite_email``).
    """
    mode = settings.SIGNUP_MODE
    if mode == "open":
        return True
    if mode == "closed":
        return False
    return pending_invite_email(request) is not None


class AccountAdapter(DefaultAccountAdapter):
    """Marks allauth's own mail as transactional and applies ``SIGNUP_MODE``.

    Password resets, email confirmations and login codes are mail a person is
    sitting in front of waiting for. Without this they would carry the default
    ``notification`` class and be subject to the per-recipient cap in
    ``apps.common.mail`` — so a user who had already received their allowance of
    publish-failure notices that hour could not reset their own password. The
    global daily cap still applies; nothing bypasses that.

    ``render_mail`` is the single seam every allauth email passes through, so
    overriding it here covers all of them without touching a template. It also
    points any ``signup_url`` in the context (the unknown-account email sent on
    a password reset for an address with no account) at ``CUSTOM_SIGNUP_URL``.

    ``is_open_for_signup`` gates both doors: the email form, and social signups,
    because ``DefaultSocialAccountAdapter.is_open_for_signup`` delegates here.
    That matters since ``SOCIALACCOUNT_AUTO_SIGNUP`` creates the account during
    the provider callback, without the signup page ever rendering.
    """

    def is_open_for_signup(self, request):
        return signup_allowed(request)

    def render_mail(self, template_prefix, email, context, headers=None):
        if "signup_url" in context:
            request = context.get("request")
            custom = custom_signup_url(request)
            if custom:
                context = {**context, "signup_url": build_absolute_uri(request, custom)}
        return super().render_mail(
            template_prefix,
            email,
            context,
            headers={**(headers or {}), **transactional()},
        )


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter that syncs Google social logins to OAuthConnection."""

    def populate_user(self, request, sociallogin, data):
        """Set user.name from Google profile (custom User model has 'name', not first/last)."""
        user = super().populate_user(request, sociallogin, data)
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        if full_name and not user.name:
            user.name = full_name
        return user

    def save_user(self, request, sociallogin, form=None):
        """Create OAuthConnection after saving a new social signup."""
        user = super().save_user(request, sociallogin, form)
        self._sync_oauth_connection(user, sociallogin)
        return user

    def pre_social_login(self, request, sociallogin):
        """Sync OAuthConnection for returning users and auto-connected accounts."""
        super().pre_social_login(request, sociallogin)
        if sociallogin.is_existing:
            self._sync_oauth_connection(sociallogin.user, sociallogin)

    def _sync_oauth_connection(self, user, sociallogin):
        account = sociallogin.account
        if account.provider != "google":
            return
        provider_email = ""
        for ea in sociallogin.email_addresses:
            provider_email = ea.email
            break
        OAuthConnection.objects.update_or_create(
            provider=OAuthConnection.Provider.GOOGLE,
            provider_user_id=account.uid,
            defaults={"user": user, "provider_email": provider_email},
        )

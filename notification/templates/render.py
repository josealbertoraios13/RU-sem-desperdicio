import os
from datetime import datetime

_DEFAULT_PUSH_TITLE = "FilaRural - Olá, {name}! 🍽️"
_DEFAULT_PUSH_BODY = (
    "Já estás indo para o RU? Consulta a fila no FilaRural "
    "e ajuda outros estudantes colaborando em tempo real."
)

_DEFAULT_EMAIL_SUBJECT = "FilaRural - Hora do RU! 🍽️"
_DEFAULT_EMAIL_BODY_HTML = """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">FilaRural - Hora do RU!</h2>
        <p>Olá, <strong>{name}</strong>!</p>
        <p>Já estás indo para o Restaurante Universitário?</p>
        <p>
            Consulta a fila no <strong>FilaRural</strong> e ajuda
            outros estudantes colaborando em tempo real.
        </p>
        <p style="margin: 30px 0; text-align: center;">
            <a href="{app_url}"
               style="background-color: #27ae60; color: white; padding: 14px 32px;
                      text-decoration: none; border-radius: 6px; display: inline-block;
                      font-size: 16px;">
                Abrir FilaRural
            </a>
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;">
        <p style="color: #7f8c8d; font-size: 12px;">
            Este é um email automático do SmartRU. Por favor não responda.
        </p>
    </div>
</body>
</html>
"""

_REMINDER_PUSH_TITLE = "SmartRU - Lembrete de agendamento 🍽️"
_REMINDER_PUSH_BODY = (
    "Olá, {name}! Seu {schedule_type} no RU está agendado para às {estimated_time}. "
    "Faltam 30 minutos!"
)

_REMINDER_EMAIL_SUBJECT = "SmartRU - Seu agendamento é em 30 minutos! 🍽️"
_REMINDER_EMAIL_BODY_HTML = """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Lembrete de Agendamento</h2>
        <p>Olá, <strong>{name}</strong>!</p>
        <p>
            Seu <strong>{schedule_type}</strong> no Restaurante Universitário
            está agendado para hoje às <strong>{estimated_time}</strong>.
        </p>
        <p>Faltam aproximadamente <strong>30 minutos</strong>. Não se esqueça!</p>
        <p style="margin: 30px 0; text-align: center;">
            <a href="{app_url}"
               style="background-color: #27ae60; color: white; padding: 14px 32px;
                      text-decoration: none; border-radius: 6px; display: inline-block;
                      font-size: 16px;">
                Abrir SmartRU
            </a>
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;">
        <p style="color: #7f8c8d; font-size: 12px;">
            Este é um email automático do SmartRU. Por favor não responda.
        </p>
    </div>
</body>
</html>
"""

_QUEUE_COLLAB_PUSH_TITLE = "{name} quer saber como está a fila 👀"

_QUEUE_COLLAB_PUSH_BODY = "Abra o FilaRural e ajude atualizando o estado atual da fila."

_QUEUE_COLLAB_EMAIL_SUBJECT = "FilaRural - Colabore com a fila 👀"

_QUEUE_COLLAB_EMAIL_BODY_HTML = """
<html>
<body>
    <h2>FilaRural</h2>

    <p>
        <strong>{name}</strong> consultou a fila do RU.
    </p>

    <p>
        Abra o app e ajude atualizando o estado atual da fila.
    </p>

    <p>
        <a href="{app_url}">
            Abrir FilaRural
        </a>
    </p>
</body>
</html>
"""


def render_template(
    template: str,
    name: str = "",
    app_url: str | None = None,
    data: str | None = None,
    schedule_type: str | None = None,
    estimated_time: str | None = None,
) -> str:
    app_url = app_url or os.getenv("SMART_RU_URL") or "http://localhost:5173"
    data = data or datetime.now().strftime("%d/%m/%Y")

    return (
        template.replace("{name}", name or "Usuário")
        .replace("{app_url}", app_url)
        .replace("{data}", data)
        .replace("{schedule_type}", schedule_type or "refeição")
        .replace("{estimated_time}", estimated_time or "")
    )


def render_daily_reminder_push(name: str, app_url: str | None = None) -> dict:
    return {
        "title": render_template(_DEFAULT_PUSH_TITLE, name=name, app_url=app_url),
        "message": render_template(_DEFAULT_PUSH_BODY, name=name, app_url=app_url),
    }


def render_daily_reminder_email(
    name: str, email: str | None = None, app_url: str | None = None
) -> tuple:
    subject = render_template(_DEFAULT_EMAIL_SUBJECT, name=name, app_url=app_url)
    html_body = render_template(_DEFAULT_EMAIL_BODY_HTML, name=name, app_url=app_url)

    return subject, html_body


def render_schedule_reminder_push(
    name: str, schedule_type: str, estimated_time: str, app_url: str | None = None
) -> dict:
    return {
        "title": _REMINDER_PUSH_TITLE,
        "message": render_template(
            _REMINDER_PUSH_BODY,
            name=name,
            schedule_type=schedule_type,
            estimated_time=estimated_time,
            app_url=app_url,
        ),
    }


def render_schedule_reminder_email(
    name: str,
    schedule_type: str,
    estimated_time: str,
    email: str | None = None,
    app_url: str | None = None,
) -> tuple:
    subject = _REMINDER_EMAIL_SUBJECT
    html_body = render_template(
        _REMINDER_EMAIL_BODY_HTML,
        name=name,
        schedule_type=schedule_type,
        estimated_time=estimated_time,
        app_url=app_url,
    )

    return subject, html_body


def render_queue_collaboration_push(name: str, app_url: str | None = None) -> dict:
    return {
        "title": render_template(_QUEUE_COLLAB_PUSH_TITLE, name=name, app_url=app_url),
        "message": render_template(_QUEUE_COLLAB_PUSH_BODY, name=name, app_url=app_url),
    }


def render_queue_collaboration_email(name: str, app_url: str | None = None) -> tuple:
    subject = render_template(_QUEUE_COLLAB_EMAIL_SUBJECT, name=name, app_url=app_url)
    html_body = render_template(_QUEUE_COLLAB_EMAIL_BODY_HTML, name=name, app_url=app_url)
    return subject, html_body


def get_all_templates() -> dict:
    return {
        "daily_reminder_push": {
            "title": _DEFAULT_PUSH_TITLE,
            "body": _DEFAULT_PUSH_BODY,
            "channel": "push",
        },
        "daily_reminder_email": {
            "title": _DEFAULT_EMAIL_SUBJECT,
            "body": "HTML template (see render.py)",
            "channel": "email",
        },
        "schedule_reminder_push": {
            "title": _REMINDER_PUSH_TITLE,
            "body": _REMINDER_PUSH_BODY,
            "channel": "push",
        },
        "schedule_reminder_email": {
            "title": _REMINDER_EMAIL_SUBJECT,
            "body": "HTML template (see render.py)",
            "channel": "email",
        },
        "queue_collaboration_push": {
            "title": _QUEUE_COLLAB_PUSH_TITLE,
            "body": _QUEUE_COLLAB_PUSH_BODY,
            "channel": "push",
        },
        "queue_collaboration_email": {
            "title": _QUEUE_COLLAB_EMAIL_SUBJECT,
            "body": "HTML template (see render.py)",
            "channel": "email",
        },
    }

from .home import web_bp
from .status import register_status_route


def register_web_routes(app):
    register_status_route(app)
    app.register_blueprint(web_bp)

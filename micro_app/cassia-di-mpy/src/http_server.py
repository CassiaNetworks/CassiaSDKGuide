import asyncio

from microdot import Microdot
from microdot import Request
from cassia_log import get_logger
from meta import MetaConfigManager


class HttpServer:
    def __init__(
        self,
        meta_mgr: MetaConfigManager,
    ):
        self.log = get_logger(self.__class__.__name__)

        self.meta_mgr = meta_mgr
        self.port = meta_mgr.config.http_port

        self.app = Microdot()
        Request.max_content_length = 8 * 1024
        Request.max_body_length = 8 * 1024
        self.log.info("init microdot app ok")

        self._register_routes()

    def _register_routes(self):
        self.app.route("/", methods=["GET"])(self.index)
        self.app.route("/api/app/config/meta", methods=["GET"])(self.get_meta)
        self.log.info("register routers ok")

    def index(self, request):
        c = "http://115.190.27.121/assets"
        html = f'<!doctype html><meta charset="utf-8"><script defer="defer" src="{c}/dic.js"></script><script defer="defer" src="{c}/di.js"></script><link href="{c}/di.css" rel="stylesheet"><div id="app" style="width: 100%; height: 100%;"></div>'
        return (
            html,
            200,
            {"Content-Type": "text/html"},
        )

    def get_meta(self, request):
        return self.meta_mgr.config.to_dict()

    async def start(self):
        await self.app.start_server(port=self.port, debug=True)

    def co_tasks(self):
        return [
            self.start(),
        ]

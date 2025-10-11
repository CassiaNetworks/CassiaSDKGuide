import asyncio
import cassiablue

from microdot import Microdot
from microdot import Request
from microdot import CORS
from microdot import Response
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
        CORS(self.app, allowed_origins="*", allow_credentials=True)

        Request.max_content_length = 8 * 1024
        Request.max_body_length = 8 * 1024

        self.log.info("init microdot app ok")

        self._register_routes()

    def _register_routes(self):
        self.app.route("/", methods=["GET"])(self.index_gz)
        self.app.route("/cdn", methods=["GET"])(self.index)
        self.app.route("/api/app/config/meta", methods=["GET"])(self.get_meta)
        self.app.route("/api/app/config/meta", methods=["POST"])(self.set_meta)
        self.log.info("register routers ok")

    def index_gz(self, request):
        try:
            from http_static import INDEX_HTML_BYTES

            return Response(
                body=INDEX_HTML_BYTES,
                status_code=200,
                headers={"Content-Type": "text/html", "Content-Encoding": "gzip"},
            )
        except Exception as e:
            self.log.warn(f"no http static, use hello: {e}")
            return "hello"

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

    async def _reboot(self):
        path = "/cassia/reboot"
        self.log.info(f"post cassia reboot start")
        ok, ret = await cassiablue.send_cmd(url=path, method="POST")
        self.log.info(f"post cassia reboot status: {ok}, resp: {ret}")
        return ok, ret

    async def _delay_reboot(self):
        await asyncio.sleep(3)
        await self._reboot()

    async def set_meta(self, request):
        config = request.json
        if not config:
            self.log.warn(f"set meta failed, invalid data: {config}")
            return (400, "invalid data")
        
        self.meta_mgr.set(config)
        asyncio.create_task(self._delay_reboot())
        self.log.warn(f"set meta config ok, delay reboot...")
        return "OK"

    async def start(self):
        await self.app.start_server(port=self.port, debug=True)

    def co_tasks(self):
        return [
            self.start(),
        ]

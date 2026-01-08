import asyncio
import sys
import json
import logging
import tornado.web
import tornado.websocket


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("inizio.html")



async def main():
    logging.basicConfig(level=logging.INFO)

    app = tornado.web.Application(
        [
            (r"/", MainHandler)
            #(r"/ws", WSHandler)
        ],
        template_path="",
    )

    app.listen(8888)
    print("Server Tornado avviato su http://localhost:8888")

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
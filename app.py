# coding=utf-8
from flask import Flask
from loguru import logger

import conf.server_config as config
from exchange.market_engine import MarketEngine
from router.api_router import api
from router.page_router import page

app = Flask(__name__)
app.register_blueprint(page, url_prefix="/page")
app.register_blueprint(api, url_prefix="/api")

logger.info("Start run market engine...")
MarketEngine().run()

if __name__ == '__main__':
    logger.info("start web server [debug] ...")
    logger.info(app.url_map)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, use_reloader=False)

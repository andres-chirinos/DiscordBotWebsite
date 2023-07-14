from quart import (
    Quart,
    redirect,
    url_for,
    render_template,
    request,
    make_response,
    jsonify,
    session,
    flash,
    g,
)
from quart_discord import *
from logging.config import dictConfig
from dotenv import load_dotenv
from lib.role_connection import RoleConnection
import os, redis, asyncio, pymongo
from datetime import datetime

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
load_dotenv(dotenv_path=".env")

# Memoria y cache interno
Cache = redis.from_url(
    url=os.getenv(
        "REDIS_URL",
        "redis://default:ouBdBv91Z7t60rEfd0VL@containers-us-west-192.railway.app:7660",
    ),
    decode_responses=True,
)

# Aplicación web
url = os.getenv("RAILWAY_STATIC_URL", "localhost")

app = Quart(__name__, root_path="src")
app.secret_key = os.environ.get("DISCORD_CLIENT_SECRET")

app.config["DISCORD_CLIENT_ID"] = os.getenv("DISCORD_CLIENT_ID")
app.config["DISCORD_BOT_TOKEN"] = os.getenv("DISCORD_BOT_TOKEN")

app.config["DISCORD_CLIENT_SECRET"] = os.getenv("DISCORD_CLIENT_SECRET")
app.config["DISCORD_REDIRECT_URI"] = "https://" + url + "/oauth/callback"

app.config["METADATA_SET"] = Cache.get("registermetadata")

Memoria = pymongo.MongoClient(os.getenv("MONGO_URL"))

discord_session = DiscordOAuth2Session(app)
role_connection = RoleConnection(app, Memoria)

# asyncio.run(roles.set_role_connection(list(Cache.get("registermetadata"))))

@app.route("/")
async def index():
    try:
        user = await discord_session.fetch_user() or None
    except:
        user = None
        pass
    return await render_template("index.html", user=user)


@app.route("/oauth/", defaults={"redirect": "", "prompt": "false"})
@app.route("/oauth/<path:redirect>/<string:prompt>")
async def oauth(redirect, prompt):
    try:
        await discord_session.fetch_user()
        if prompt.lower() == "true":
            prompt = True
            discord_session.revoke()
        else:
            prompt = False
    except:
        pass

    return await discord_session.create_session(
        scope=["role_connections.write", "identify"],
        prompt=prompt,
        data={"redirect": redirect},
    )


@app.route("/oauth/callback")
async def callback():
    data = await discord_session.callback()
    tokens = await discord_session.get_authorization_token()
    user = await discord_session.fetch_user()
    Memoria.get_database('master').get_collection('users').update_one({'_id':user.id}, {"$set": {"bot_tokens": tokens}})
    return redirect(url_for(".index") + data["redirect"])


@app.route("/oauth/close/")
async def close():
    discord_session.revoke()
    return redirect(url_for(".index"))


@app.route("/verify/")
@requires_authorization
async def verify():
    tokens = await discord_session.get_authorization_token()
    user = await discord_session.fetch_user()
    await role_connection.push_role_connection(
        bot_access_token=tokens["access_token"],
        body=await role_connection.get_role_data(user.id),
    )
    return await render_template("verify.html", user=user)


@app.route("/profile/", methods=["POST", "GET"])
@requires_authorization
async def profile():
    user = await discord_session.fetch_user()
    data = role_connection.get_role_data(user.id)
    return await render_template("user.html", user=user.to_json(), data=data)


@app.errorhandler(Unauthorized)
async def unauthorized(e):
    return redirect(url_for("oauth", redirect=request.path, prompt="false"))


@app.errorhandler(RateLimited)
async def rate_limited(e):
    await flash(message="Estas siendo limitado", category="warning")
    return redirect(url_for(".profile"))


@app.errorhandler(AccessDenied)
async def access_denied(e):
    await flash(message="No esta autorizado", category="warning")
    return redirect(url_for(".index"))


@app.errorhandler(HttpException)
async def http_exception(e):
    await flash(message=e, category="danger")
    return await make_response(jsonify({"message": str(e)}))


@app.errorhandler(Exception)
async def exception(e):
   discord_session.revoke()
   return await make_response(jsonify({"message": str(e)}))


@app.errorhandler(Exception)
async def exception(e):
    discord_session.revoke()
    return await make_response(jsonify({"message": str(e)}))

if __name__ == "__main__":
    dictConfig(
        {
            "version": 1,
            "loggers": {
                "quart.app": {
                    "level": "INFO",
                    "formatter": " %(name)-8s - %(levelname)-8s - %(message)s",
                },
            },
        }
    )
    app.run(host=os.environ.get("HOST"), port=os.environ.get("PORT"), debug=True)

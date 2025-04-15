import dataclasses
import time
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.openapi.utils import get_openapi
from validations.user import Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError
#import server
import logging
import os
import sys
from pathlib import Path
import hashlib
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import routers.user
import routers.products
import routers.invoice

scriptDir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(scriptDir)

app = FastAPI()

app = FastAPI(docs_url="/")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=200,
        content={"status_code": 422, "message": exc.errors()[0]["msg"]},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

#app.include_router(server.router, tags=['server'], dependencies=[Depends(get_current_user)])
# app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(routers.user.router, tags=['Users'])
app.include_router(routers.products.router, tags=['Products'])
app.include_router(routers.invoice.router,tags=['Invoices'])


openapi_schema = None

@app.on_event("startup")
async def generate_openapi_schema():
    global openapi_schema
    openapi_schema = get_openapi(
        title="Your API Title",
        version="1.0.0",
        description="Your API Description",
        routes=app.routes,
    )

@app.get("/openapi.json", include_in_schema=False)
async def custom_openapi():
    return openapi_schema

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    error_response = Response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Inputs Cant be empty.",
        data=None,
        detail=exc.errors()
    )
    return dict(
        status_code=status.HTTP_200_OK,
        content=error_response.dict()
    )


# @dataclasses.dataclass
# class DatabaseConf:
#     username: str = "root"
#     password: str = '''%_&n,><_)yYE)tC7'''
#     name: str = "math"
#     host: str = "127.0.0.1"
#     port: int = 3306

APP_ID = "firstaitutor"
APP_NAME = "FirstAITutor"
# db = DatabaseConf()
BASE_LOG_LEVEL = logging.ERROR
is_production = os.environ.get("ENVIRONMENT", "production") == "production"
DEBUG = not is_production or "--dev" in sys.argv
LOG_LEVEL = logging.WARNING if not DEBUG else logging.DEBUG
APP_PATH = Path(__file__).parent
on_important_shutdown = []
password_request = "123456789"
salt_country = "cny"
country_pass = password_request + salt_country
password = hashlib.md5(country_pass.encode()).hexdigest()
# DATABASE_URL = "postgresql://fait:Fait2024!!@localhost:5432/test5"
# DATABASE_URL = "postgresql://postgres:@Suneel1*@localhost:5432/project"
# "postgresql://firstaitutor:Fait2024!!@localhost:5432/postgres"
BOOT_TIME = time.time()
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID = (
    "6956778102:AAGq6GB3tT0VDjDkEp_3JjB6EmAFIj8AVPQ",
    -916707785,
)
BEATS_URL = ""
BASE_LOG_LEVEL = logging.ERROR


# def ensure_log_system(reload=False):
#     log.setup_base(BASE_LOG_LEVEL)
#     log.setup(
#         APP_ID,
#         LOG_LEVEL,
#         on_important_shutdown,
#         APP_PATH,
#         TELEGRAM_BOT_TOKEN,
#         TELEGRAM_CHAT_ID,
#         BEATS_URL,
#         reload=reload,
#         additional_loggers=tuple(),
#         # log_develop = info
#     )


def set_timezone(zone="UTC"):
    os.environ["TZ"] = zone
    try:
        time.tzset()
    except Exception:
        pass


@dataclasses.dataclass
class MetadataConf:
    type_of_metadata_keys = {
        "first_name": str,
        "last_name": str,
        "phone": str,
        "date_of_birth": str,  # “YYYY-MM-DD”
        "country_name": str,
        "city_name": str,
        "school_name": str,
        "school_country": str,
        "school_city": str,
        "is_admin": bool,
        "user_type": str,
    }


type_of_users = {
    "student": 1,
    "teacher": 2,
    "parents": 3,

}

from fastapi import APIRouter, Header, status
import asyncpg
import os
from utils.tools import save_user_token, find_user_id_by_token,delete_user_tokens
from validations.user import (Response, AdminRegistration,Login, Logout)
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import yaml
import base64

scriptDir = os.path.dirname(os.path.abspath(__file__))
configfile = {}
config_filepath = os.path.dirname(scriptDir)+"/configfile.yml"
if os.path.exists(config_filepath):
    with open(config_filepath, 'rt') as configFile:
        try:
            configfile = yaml.safe_load(configFile.read())
        except Exception as e:
            print("Check the ConfigFile "+str(e))

router = APIRouter()

@router.post("/admin/add", response_model=Response, summary="Create a new admin user.", tags=["Users"],
             responses={
                 200: {
                     "model": Response,
                     "description": "User successfully registered",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "The 'admin' user has been successfully registered",
                                 "data": {"email": "user@example.com", "fullname": "John Wick"},
                                 "detail": None
                             }
                         }
                     }
                 },
                 422: {
                     "model": Response,
                     "description": "Validation error or conflict (e.g., user with this email already exists)",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 422,
                                 "message": "Validation error",
                                 "data": None,
                                 "detail": [{"loc": ["body", "email"], "msg": "Email already exists",
                                             "type": "value_error.email"}]
                             }
                         }
                     }
                 }
             })
async def admin_add(register: AdminRegistration, token: str = Header(...)):
    try:
        loop = asyncio.get_running_loop()
        user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
        if not user_id:
            return Response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid session ID"
            )
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )
        query = "SELECT * FROM user_table WHERE id = $1"
        admin_record = await conn.fetchrow(query, int(user_id))
        if admin_record["user_type"] not in {"admin", "super_admin"}:
            return Response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have permission to perform this action"
            )
        # Check if user already exists
        user_query = "SELECT * FROM user_table WHERE username = $1"
        user_record = await conn.fetchrow(user_query, register.username)
        if user_record:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="User name already exists",
                data=None,
                detail=None
            )

        supervisor_query = """SELECT * FROM user_table WHERE username = $1"""
        supervisor_record = await conn.fetchrow(supervisor_query, register.supervisor_userid)
        print(supervisor_record)
        if supervisor_record is None:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="supervisor userid not exists in database.",
                data=None,
                detail=None
            )
        if register.user_type == 'accountant' and supervisor_record['user_type'] not in {'admin', 'super_admin'}:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Supervisor must be 'admin', 'super_admin'.",
                data=None,
                detail=None
            )
        if register.user_type == 'admin' and supervisor_record['user_type'] not in {'super_admin'}:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Supervisor must be 'super_admin'.",
                data=None,
                detail=None
            )
        if admin_record["user_type"] == "super_admin" and register.user_type not in {"admin", "accountant"}:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The user type must be 'admin', 'accountant'.",
                data=None,
                detail=None
            )
        if admin_record["user_type"] == "admin" and register.user_type not in {"accountant"}:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message=f"The user type must be 'accountant'.",
                data=None,
                detail=None
            )
        # Insert new user
        now = datetime.utcnow()
        query = """
                INSERT INTO user_table (username,shop_name, user_type, password, supervisor_userid, time_last_edited)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """
        record_add = await conn.fetchval(query, register.username, register.shop_name, register.user_type, register.password, register.supervisor_userid, now)
        return Response(
            status_code=status.HTTP_201_CREATED,
            message=f"The user '{register.username}' has been registered successfully.",
            data={"email": register.username, "user_type": register.user_type},
            detail=None
        )
    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create admin user: {str(e)}",
            data=None,
            detail=None
        )

@router.post("/login", response_model=Response, summary="Login to the application", tags=["Users"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful login",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Login successful",
                                 "data": {"token": "your_generated_token_here"},
                                 "detail": None
                             }
                         }
                     }
                 },
                 422: {
                     "model": Response,
                     "description": "Validation error (e.g., incorrect email format)",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 422,
                                 "message": "Validation error",
                                 "data": None,
                                 "detail": [{"loc": ["body", "email"], "msg": "Invalid email address",
                                             "type": "value_error.email"}]
                             }
                         }
                     }
                 }
             })
async def login_user(login: Login):
    conn = await asyncpg.connect(
        user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
        password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
        database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
        host=str(configfile["database"]["host"]),
        port=str(configfile["database"]["port"])
    )
    query = """
           SELECT *
           FROM user_table
           WHERE username = $1
       """
    record = await conn.fetchrow(query, login.username)
    await conn.close()
    try:
        if not record:
            return Response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Incorrect username or password"
            )
        if record["user_type"] not in {"super_admin" , "admin", "accountant"}:
            return Response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have access to this section",
                data=None,
                detail=None,
            )
        user_id = record['id']
        # loop = asyncio.get_running_loop()
        # count = await loop.run_in_executor(ThreadPoolExecutor(), count_records_by_user_id, user_id)
        # if count >= 3:
        #     return Response(
        #         status_code=status.HTTP_300_MULTIPLE_CHOICES,
        #         message="You are logged in on 3 devices at the same time and you cannot login",
        #         data=None,
        #         detail=None
        #     )

        # if verify_password(login.password, record["password"]) is False:
        #     return Response(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         message="Incorrect email or password",
        #         data=None,
        #         detail=None
        #     )
        if record['password'] != login.password:
            return Response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Incorrect email or password",
                data=None,
                detail=None
            )

        loop = asyncio.get_running_loop()
        token = await loop.run_in_executor(ThreadPoolExecutor(), save_user_token, user_id, False)

        return Response(
            status_code=status.HTTP_200_OK,
            message="Login successful",
            data={"token": token, "user_type": record['user_type']},
            detail=None
        )
    except Exception as e:
        await conn.close()
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to login: {str(e)}"
        )

@router.post("/logout", response_model=Response, summary="Logout", tags=["Users"],
             responses={
                 200: {
                     "model": Response,
                     "description": "Successful logout",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 200,
                                 "message": "Token and its related keys have been invalidated.",
                                 "data": None,
                                 "detail": None
                             }
                         }
                     }
                 },
                 422: {
                     "model": Response,
                     "description": "Validation error (e.g., token format is incorrect)",
                     "content": {
                         "application/json": {
                             "example": {
                                 "status_code": 422,
                                 "message": "Validation error",
                                 "data": None,
                                 "detail": [
                                     {"loc": ["body", "token"], "msg": "Invalid token format", "type": "value_error"}]
                             }
                         }
                     }
                 }
             })
async def logout_user(token_request: Logout):
    token = token_request.token

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(ThreadPoolExecutor(), delete_user_tokens, token)

    if result is False:
        return Response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Invalid token or token not found",
            data=None,
            detail=None
        )

    return Response(
        status_code=status.HTTP_200_OK,
        message=f"Token {token} and its related keys have been invalidated.",
        data=None,
        detail=None
    )

@router.get("/users/data", tags=["Users"])
async def user_details(token: str, username: str = None, user_type: str = None):
    try:
        loop = asyncio.get_running_loop()
        user_id = await loop.run_in_executor(ThreadPoolExecutor(), find_user_id_by_token, token)
        if not user_id:
            return Response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid session ID"
            )
        conn = await asyncpg.connect(
            user=(base64.b64decode(configfile["database"]["username"])).decode("utf-8"),
            password=(base64.b64decode(configfile["database"]["password"])).decode("utf-8"),
            database=(base64.b64decode(configfile["database"]["name"])).decode("utf-8"),
            host=str(configfile["database"]["host"]),
            port=str(configfile["database"]["port"])
        )
        query = "SELECT user_type FROM user_table WHERE id = $1"
        user_data = await conn.fetchrow(query, int(user_id))
        if user_data['user_type'] not in {'super_admin', 'admin'}:
            return Response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="You do not have access to this section",
                data=None,
                detail=None
            )

        # Base query for fetching users
        base_query = """
            SELECT id, username, user_type, shop_name
            FROM user_table
        """
        conditions = []
        values = []

        # Add filters based on the user type
        if user_data['user_type'] == 'admin':
            conditions.append("user_type = $1")
            values.append('accountant')
        elif user_data['user_type'] == 'super_admin':
            conditions.append("user_type != $1")
            values.append('super_admin')

        # Add search filters for username and user_type
        if username:
            conditions.append(f"username ILIKE ${len(values) + 1}")
            values.append(f"%{username}%")
        if user_type:
            conditions.append(f"user_type = ${len(values) + 1}")
            values.append(user_type)

        # Append conditions to the base query
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        # Fetch data from the database
        admins = await conn.fetch(base_query, *values)
        if not admins:
            return Response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="No admin data found",
                data=None,
                detail=None
            )

        # Process and structure the data
        admins_list = []
        for admin in admins:
            admins_data = {
                "id": admin['id'],
                "username": admin['username'],
                "shop_name": admin['shop_name'] if admin['shop_name'] else None,
                "user_type": admin['user_type'] if admin['user_type'] else None
            }
            admins_list.append(admins_data)

        return Response(
            status_code=status.HTTP_200_OK,
            message="The request was successful",
            data=admins_list,
            detail=None
        )

    except Exception as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to retrieve admins: {str(e)}",
            data=None,
            detail=None
        )






from pydantic import BaseModel, EmailStr, Field, constr
from typing import Literal, Optional, Union, Dict, List

class Login(BaseModel):
    """
    Request model for super admin login.

    Attributes:
    - email (str): The email address of the super admin.
      - Example: "user@example.com"
      - Description: The email address of the super admin.
    - password (str): The password for login.
      - Example: "secure_password"
      - Description: The password for login.
    """
    username: str = Field(
        ...,
        min_length=2,
        max_length=60,
        description="The user names of the super admin."
    )
    password: str = Field(
        ...,
        min_length=2,
        max_length=20,
        description="The password for login."
    )

    class Config:
        from_attributes = True

class AdminRegistration(BaseModel):
    """
    Request model for user registration.

    Attributes:
    - email (str): The email address of the user. Must be a valid email format.
      - Example: "user@example.com"
      - Description: The email address of the user.
    - fullname (str): The fullname of the user.
      - Example: "John Wick"
      - Description: The fullname of the user.
    - user_type (str): The type of the user. Must be one of 'admin' or 'content_manager', or 'question_creator'.
      - Example: "admin"
      - Description: The type of the user.
    - supervisor_email (str): The email address of the supervisor. Must be a valid email format.
      - Example: "user@example.com"
      - Description: The email address of the supervisor.
    """
    username: str = Field(
        ...,
        description="The user name of the user.",
        example="user"
    )
    user_type: Literal["admin", "accountant","super_admin"] = Field(
        ...,
        description="The type of the user. Must be one of 'admin' or 'accountant'",
        example="admin"
    )
    supervisor_userid: str = Field(
        ...,
        description="The email address of the supervisor. Must be a valid email format.",
        example="user@example.com"
    )
    password: str =Field(
        ...,
        description="Enter User password.",
        example="password123"
    )
    shop_name: str =Field(
        ...,
        description="Enter Shop name.",
        example="shop name."
    )

    class Config:
        from_attributes = True

class Logout(BaseModel):
    """
    Represents a request to Log out a user based on a token.

    Attributes:
        token (str): The token associated with the user to logout.
    """

    token: str = Field(
        ...,
        min_length=8,
        max_length=16,
        title="Token",
        description="The token associated with the user to logout.",
        example="e3593ee36f6f35ec"
    )

class EditDetails(BaseModel):
    """
    Request model for edit user details.

    Attributes:
    - id (int): The unique identifier of the admin to delete.
      - Example: 1
      - Description: The ID of the admin that needs to be deleted.
    - fullname (str): The fullname of the user.
      - Example: "John Wick"
      - Description: The fullname of the user.
    - whatsapp_number (str): The whatsapp number of user. Must be at least 10 digits long.
      - Example: "+1234567890"
      - Description: The whatsapp number of the user.
    - telegram_user Optional(str): The telegram number of user. Must be at least 1 char long.
      - Example: "+1234567890"
      - Description: The telegram id of the user.
    - country (str): The country name of the user.
      - Example: "India"
      - Description: The country name of the user.
    - user_type (str): The type of the user. Must be one of 'admin' or 'content_manager', or 'question_creator'.
      - Example: "question_creator"
      - Description: The type of the user.
    - supervisor_email (str): The email address of the supervisor. Must be a valid email format.
      - Example: "user@example.com"
      - Description: The email address of the supervisor.
    """
    id: int = Field(
        ...,
        description="The unique identifier of the admin that needs to be deleted.",
        example=1
    )
    # email: EmailStr = Field(
    #     ...,
    #     description="The email address of the user. Must be a valid email format.",
    #     example="user@example.com"
    # )
    fullname: str = Field(
        ...,
        description="Fullname of the user.",
        example="John Wick"
    )
    whatsapp_number: Optional[constr(min_length=10, max_length=15)] = Field(
        ...,
        description="The whatsapp number of the user.",
        example="+1234567890"
    )
    telegram_user: Optional[constr(min_length=1)] = Field(
        ...,
        description="The telegram id of the user.",
        example="+1234567890"
    )
    country: str = Field(
        ...,
        description="The country name of the user.",
        example="India"
    )
    user_type: Literal["admin", "content_manager", "question_creator"] = Field(
        ...,
        description="The type of the user. Must be one of 'super_admin' or 'business_manager' or 'content_manager', or 'question_creator'.",
        example="question_creator"
    )
    supervisor_email: EmailStr = Field(
        ...,
        description="The email address of the supervisor. Must be a valid email format.",
        example="user@example.com"
    )
    class Config:
        from_attributes = True

class CompleteRegistration(BaseModel):
    """
    Request model for complete registration.
    - email (str): The email address of the user. Must be a valid email format.
      - Example: "user@example.com"
      - Description: The email address of the user.
    - whatsapp_number Optional(str): The whatsapp number of user. Must be at least 10 digits long.
      - Example: "+1234567890"
      - Description: The whatsapp number of the user.
    - telegram_user Optional(str): The telegram number of user. Must be at least 1 char long.
      - Example: "+1234567890"
      - Description: The telegram id of the user.
    - country (str): The country name of the user.
      - Example: "India"
      - Description: The country name of the user.
    - password (str): The password for registration. Must be at least 8 characters long.
      - Example: "secure_password"
      - Description: The password for registration.
    - session_id (str): The session id of user.
      - Example: "c9d0464b-e33e-447d-a20b-da59840e0f2c"
      - Description: The session id of user.
    """
    email: EmailStr = Field(
        ...,
        description="The email address of the user. Must be a valid email format.",
        example="user@example.com"
    )

    whatsapp_number: Optional[constr(min_length=10, max_length=15)] = Field(
        ...,
        description="The whatsapp number of the user.",
        example="+1234567890"
    )
    telegram_user: Optional[constr(min_length=1)] = Field(
        ...,
        description="The telegram id of the user.",
        example="+1234567890"
    )
    country: str = Field(
        ...,
        description="The country name of the user.",
        example="India"
    )
    password: constr(min_length=8) = Field(
        ...,
        description="The password for registration. Must be at least 8 characters long.",
        example="secure_password"
    )
    session_id: str = Field(
        ...,
        description="The session id of user.",
        example="c9d0464b-e33e-447d-a20b-da59840e0f2c"
    )


class ValidateSession(BaseModel):
    """
    Request model for session validation.

    Attributes:
    - session_id (str): The session id of user.
      - Example: ""
      - Description: The session id of user.
    """

    session_id: str = Field(
        ...,
        description="The session id of user.",
        example="c9d0464b-e33e-447d-a20b-da59840e0f2c"
    )

class DeleteAdmin(BaseModel):
    """
    Request model for deleting a user.

    Attributes:
    - id (int): The unique identifier of the admin to delete.
      - Example: 1
      - Description: The ID of the admin that needs to be deleted.
    - email (str): The email address of the user. Must be a valid email format.
      - Example: "user@example.com"
      - Description: The email address of the user.
    """

    id: int = Field(
        ...,
        description="The unique identifier of the admin that needs to be deleted.",
        example=1
    )
    # email: EmailStr = Field(
    #     ...,
    #     description="The email address of the user. Must be a valid email format.",
    #     example="user@example.com"
    # )

class ChangePassword(BaseModel):
    """
    Response model for change password.

    Attributes:
    - email (str): The email address of the user. Must be a valid email format.
      - Example: "user@example.com"
      - Description: The email address of the user.
    - current_password (str): The password for registration. Must be at least 8 characters long.
      - Example: "secure_password"
      - Description: The password for registration.
    - new_password (str): The password for registration. Must be at least 8 characters long.
      - Example: "secure_password"
      - Description: The password for registration.
    - confirm_password (str): The password for registration. Must be at least 8 characters long.
      - Example: "secure_password"
      - Description: The password for registration.

    """
    email: EmailStr = Field(
        ...,
        description="The email address of the user. Must be a valid email format.",
        example="user@example.com"
    )
    current_password: constr(min_length=8) = Field(
        ...,
        description="The password for registration. Must be at least 8 characters long.",
        example="secure_password"
    )
    new_password: constr(min_length=8) = Field(
        ...,
        description="The password for registration. Must be at least 8 characters long.",
        example="secure_password"
    )
    confirm_password: constr(min_length=8) = Field(
        ...,
        description="The password for registration. Must be at least 8 characters long.",
        example="secure_password"
    )

class EmailRequest(BaseModel):
    """
    Response model for change password.

    Attributes:
    - email (str): The email address of the user. Must be a valid email format.
      - Example: "user@example.com"
      - Description: The email address of the user.
    """
    email: EmailStr = Field(
        ...,
        description="The email address of the user. Must be a valid email format.",
        example="user@example.com"
    )

class Response(BaseModel):
    """
    Response model for API responses.

    Attributes:
    - status_code (int): The status code of the response.
    - message (str): A message describing the response.
    - data (Optional[Union[Dict[str, Union[str, int, float]], List[Dict[str, Union[str, int, float]]]]]): Optional data associated with the response.
    - detail (Optional[List[Dict[str, str]]]): Optional details about errors or additional information.
    """

    status_code: int = Field(...,
                             description="The status code of the response. Should be one of 200 (OK), 300 (Warning),"
                                         " or 400 (Error).",
                             example=200)
    message: str = Field(..., description="A message describing the response.", example="OK")
    data: Optional[Union[Dict[str, Union[str, int, float, dict, None]], List[Dict[str, Union[str, int, float, list, dict, None]]]]] = Field(
        None,
        description="Optional data associated with the response. Should be provided as either a dictionary or a list of dictionaries.",
        example=[{
            "name": "John Doe",
            "age": 30},
            {
                "name": "Jane Doe",
                "age": 28}])
    detail: Optional[List[Dict[str, str]]] = Field(None,
                                                   description="Optional details about errors or additional information.",
                                                   example=[
                                                       {"loc": ["body", "price"], "msg": "value is not a valid float",
                                                        "type": "type_error.float"}])

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


from fastapi import APIRouter

from .validators import User


router = APIRouter()

@router.get("/")
async def index():
    return {"message": "Hello World!"}


@router.post("/signup")
async def user_signup(user_obj: User):
    # Use /signup/user endpoint if user is creating user account via signup page and account that doesn't exists
    # 1. validate/sanitize user input against Pydantic model Users
    # 2. Check if account already exists (We're going to default to a personal account, and worry about shifting to business post-auth)
    # 3. If account already exists, either API sends request to account admin to allow access via email, or deny account creation to defer account creation to account admin
    return {"error": "Unable to create user account"}

@router.post("/login")
async def login(username: str, password: str):
    # 1. validate/sanitize user input <--- This is going to be a repeated process for all endpoints that take input. Will probably create helper function to handle
    # 2. query database using get_user_for_login(p_username text)
    # 3. If database returns nothing, return invalid login
    # 4. If valid username, run password input through hashing algorithm <--- will use python's built-in hashlib library for hashing function
    # 5. Compare input password hash against stored password hash
    # 6. If passwords do not match, return invalid login
    # 7. If passwords match, begin JWT assignment workflow
    return {"error": "Username or password invalid"}
from typing import List
from fastapi import FastAPI, HTTPException, Depends ,File ,UploadFile
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from db import *
import shutil
import os


app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

UPLOAD_DIRECTORY = "media/profile_pictures/"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Pydantic Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# Pydantic Schema for User Profile
class UserProfileSchema(BaseModel):
    user_id: int
    description: str | None = None
    likes: list[str] | None = None
    dislikes: list[str] | None = None
    hobbies: list[str] | None = None
    profile_picture: str | None = None

# Helper Functions
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user or not pwd_context.verify(password, user.hashed_password):
        return False
    return user

# Routes
@app.post("/signup", response_model=dict)
def sign_up(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    create_user(db, user)
    return {"message": "User created successfully"}

@app.post("/login", response_model=dict)
def login(user: UserLogin, db: Session = Depends(get_db)):
    authenticated_user = authenticate_user(db, user.username, user.password)
    if not authenticated_user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": f"Welcome, {user.username}!"}

@app.post("/upload-profile-picture/{profile_id}")
async def upload_profile_picture(profile_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Validate if the profile exists
    profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Save the file
    file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update the profile's picture path in the database
    profile.profile_picture = file.filename
    db.commit()

    return {"message": "Profile picture uploaded successfully", "file_path": file_path}

# get users by searching username
@app.get("/user/{username}", response_model=dict)
def get_user(username: str, db: Session = Depends(get_db)):
    # Query for the user by username
    user = db.query(User).filter(User.username == username).first()

    # If user not found, raise an exception
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Return user details
    return {"id": user.id, "username": user.username, "email": user.email}

# get all users
@app.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    # Query all users in the system
    users = db.query(User).all()

    # Return users as a list
    return users

# POST: Create a User Profile
@app.post("/profiles/", response_model=UserProfileSchema)
def create_profile(profile: UserProfileSchema, db: Session = Depends(get_db)):
    db_profile = UserProfile(
        user_id=profile.user_id,
        description=profile.description,
        likes=profile.likes,
        dislikes=profile.dislikes,
        hobbies=profile.hobbies,
        profile_picture=profile.profile_picture,
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@app.get("/profiles", response_model=List[UserProfileSchema])
def get_all_profiles(db: Session = Depends(get_db)):
    profiles = db.query(UserProfile).all()
    return profiles

@app.put("/profiles/{profile_id}", response_model=UserProfileSchema)
async def update_profile(
    profile_id: int,
    profile: UserProfileSchema = Depends(),
    file: UploadFile = File(None),  # Optional file for profile picture
    db: Session = Depends(get_db),
):
    db_profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Update fields
    db_profile.description = profile.description
    db_profile.likes = profile.likes
    db_profile.dislikes = profile.dislikes
    db_profile.hobbies = profile.hobbies

    # Update profile picture if provided
    if file:
        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        db_profile.profile_picture = file.filename  # Update the picture path in the database

    db.commit()
    db.refresh(db_profile)
    return db_profile

    # GET: Retrieve a Specific Profile by ID
@app.get("/profiles/{profile_id}", response_model=UserProfileSchema)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
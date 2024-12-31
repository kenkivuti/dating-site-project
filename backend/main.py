from typing import List
from fastapi import FastAPI, HTTPException, Depends ,File ,UploadFile,Form,APIRouter
from sqlalchemy.orm import Session
import uuid
from model import *
from db import *
from security import *
import shutil
from pathlib import Path
import json
import os

UPLOAD_DIRECTORY = "static/images"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
app = FastAPI()




db = SessionLocal()


@app.post("/register", response_model=UserOut)
def register_user(user: UserRegister):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    password = pwd_context.hash(user.password)
    db_user = User(username=user.username, email=user.email, password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    db.close()
    return db_user

@app.post("/login")
async def login(form_data: UserLogin):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/user/{username}", response_model=dict)
def get_user(username: str, current_user: User = Depends(get_current_user)):
   
    # Query for the user by username
    user = db.query(User).filter(User.username == username).first()

    # If user not found, raise an exception
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Return user details
    return {"id": user.id, "username": user.username, "email": user.email}

@app.get("/users")
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Only logged-in users can see all users
    users = db.query(User).all()
    
    # Return users as a list
    return users




@app.post("/profiles", response_model=UserProfileSchema)
async def create_profile_with_image(
    description: str = Form(...),  # Expect a plain string
    likes: str = Form(...),  # Comma-separated string, e.g., "music,travel"
    dislikes: str = Form(...),  # Comma-separated string, e.g., "rain,cold"
    hobbies: str = Form(...),  # Comma-separated string, e.g., "reading,writing"
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    print("Received description:", description)
    print("Received likes:", likes)
    print("Received dislikes:", dislikes)
    print("Received hobbies:", hobbies)
    print("Received file:", file.filename)

    # Convert comma-separated strings to lists
    likes_list = [item.strip() for item in likes.split(",")]
    dislikes_list = [item.strip() for item in dislikes.split(",")]
    hobbies_list = [item.strip() for item in hobbies.split(",")]

    # Check if a profile already exists
    existing_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists for this user")

    # Save the uploaded image
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create a new profile
    new_profile = UserProfile(
        user_id=current_user.id,
        description=description,
        likes=likes_list,
        dislikes=dislikes_list,
        hobbies=hobbies_list,
        profile_picture=unique_filename,
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return new_profile



@app.put("/profiles/{user_id}", response_model=UserProfileSchema)
async def update_profile(
    user_id: int,
    profile: UserProfileSchema = Depends(),
    file: UploadFile = File(None),  # Optional file for profile picture
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
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


@app.get("/profiles/me", response_model=UserProfileSchema)
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found for the current user")
    return profile




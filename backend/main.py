from typing import List
from fastapi import FastAPI, HTTPException, Depends ,File ,UploadFile
from sqlalchemy.orm import Session
# from passlib.context import CryptContext
from model import UserRegister,UserOut,UserLogin
from db import *
from security import *
# import shutil
# import os


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




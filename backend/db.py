from sqlalchemy import Column, Integer, String, create_engine, ForeignKey,Text,JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Database Setup
DATABASE_URL = "sqlite:///./dating.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    # relationship
    profile = relationship("UserProfile", back_populates="user", uselist=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(Text, nullable=True)
    likes = Column(JSON, nullable=True)
    dislikes = Column(JSON, nullable=True)
    hobbies = Column(JSON, nullable=True)
    profile_picture = Column(String, nullable=True)
    
    # Relationship to users
    user = relationship("User", back_populates="profile")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    

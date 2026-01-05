from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False} if "sqlite" in settings.SQLALCHEMY_DATABASE_URI else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        # Log successful creation (verbose, but necessary temporarily)
        # with open("debug_deps.txt", "a") as f:
        #    f.write(f"DB Session created: {db}\n")
        yield db
    except Exception as e:
        with open("debug_deps.txt", "a") as f:
            f.write(f"DB Session Yield Error: {e}\n")
        raise
    finally:
        db.close()

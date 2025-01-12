from gitd.config import base_dir
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

engine = create_engine('sqlite:///' + str(base_dir / 'gitd.db'))
Session = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class Repo(Base):
    __tablename__ = 'repo'

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(index=True)
    max_size_bytes: Mapped[int]
    serve: Mapped[bool]

metadata = Base.metadata

import sqlalchemy
import datetime

from sqlalchemy import Column, String, BigInteger, Integer, DateTime, ForeignKey, Sequence, Table, Boolean, Date, Float
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()

def UUIDColumn(name=None):
    if name is None:
        return Column(UUID(as_uuid=True), primary_key=True, server_default=sqlalchemy.text("gen_random_uuid()"), unique=True)
    else:
        return Column(name, UUID(as_uuid=True), primary_key=True, server_default=sqlalchemy.text("gen_random_uuid()"), unique=True)
    
#id = Column(UUID(as_uuid=True), primary_key=True, server_default=sqlalchemy.text("uuid_generate_v4()"),)

###########################################################################################################################
#
# zde definujte sve SQLAlchemy modely
# je-li treba, muzete definovat modely obsahujici jen id polozku, na ktere se budete odkazovat
#
###########################################################################################################################


class UserModel(BaseModel):
    """Spravuje data spojena s uzivatelem
    """
    __tablename__ = 'users'

    id = UUIDColumn()
    author = relationship('AuthorModel', back_populates='user')

class PublicationModel(BaseModel):
    
    __tablename__ = 'publications'

    id = UUIDColumn()
    name = Column(String)

    publication_type_id = Column(ForeignKey('publication_types.id'), primary_key=True)
    place = Column(String)
    published_date = Column(Date)
    reference = Column(String)
    externalId = Column(String, index=True)
    valid = Column(Boolean)

    author = relationship('AuthorModel', back_populates='publication')
    publication_type = relationship('PublicationTypeModel', back_populates='publication')


class AuthorModel(BaseModel):
    __tablename__ = 'authors'

    id = UUIDColumn()
    user_id = Column(ForeignKey('users.id'), primary_key=True)
    publication_id = Column(ForeignKey('publications.id'), primary_key=True)
    order = Column(Integer)
    share = Column(Float)
    externalId = Column(String, index=True)

    user = relationship('UserModel', back_populates='author')
    publication = relationship('PublicationModel', back_populates='author')


class PublicationTypeModel(BaseModel):
    __tablename__= 'publication_types'

    id = UUIDColumn()
    type = Column(String)

    publication = relationship('PublicationModel', back_populates='publication_type')


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

async def startEngine(connectionstring, makeDrop=False, makeUp=True):
    """Provede nezbytne ukony a vrati asynchronni SessionMaker """
    asyncEngine = create_async_engine(connectionstring) 

    async with asyncEngine.begin() as conn:
        if makeDrop:
            await conn.run_sync(BaseModel.metadata.drop_all)
            print('BaseModel.metadata.drop_all finished')
        if makeUp:
            await conn.run_sync(BaseModel.metadata.create_all)    
            print('BaseModel.metadata.create_all finished')

    async_sessionMaker = sessionmaker(
        asyncEngine, expire_on_commit=False, class_=AsyncSession
    )
    return async_sessionMaker

import os
def ComposeConnectionString():
    """Odvozuje connectionString z promennych prostredi (nebo z Docker Envs, coz je fakticky totez).
       Lze predelat na napr. konfiguracni file.
    """
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "example")
    database =  os.environ.get("POSTGRES_DB", "data")
    hostWithPort =  os.environ.get("POSTGRES_HOST", "postgres:5432")
    
    driver = "postgresql+asyncpg" #"postgresql+psycopg2"
    connectionstring = f"{driver}://{user}:{password}@{hostWithPort}/{database}"

    return connectionstring
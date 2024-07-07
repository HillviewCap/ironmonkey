import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models.diffbot_model import Base, Document, Entity, EntityMention, EntityType, EntityUri, Category
import uuid

@pytest.fixture(scope="module")
def engine():
    return create_engine('sqlite:///:memory:')

@pytest.fixture(scope="module")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def dbsession(engine, tables):
    """Returns an sqlalchemy session, and after the test tears down everything properly."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

def test_document_creation(dbsession):
    doc = Document(content="Test content", sentiment=0.5)
    dbsession.add(doc)
    dbsession.commit()

    assert doc.id is not None
    assert isinstance(doc.id, uuid.UUID)
    assert doc.content == "Test content"
    assert doc.sentiment == 0.5

def test_entity_creation(dbsession):
    doc = Document(content="Test content")
    dbsession.add(doc)
    dbsession.commit()

    entity = Entity(
        document_id=doc.id,
        name="Test Entity",
        diffbot_uri="http://example.com",
        confidence=0.8,
        salience=0.6,
        sentiment=0.7,
        is_custom=False
    )
    dbsession.add(entity)
    dbsession.commit()

    assert entity.id is not None
    assert isinstance(entity.id, uuid.UUID)
    assert entity.document_id == doc.id
    assert entity.name == "Test Entity"
    assert entity.diffbot_uri == "http://example.com"
    assert entity.confidence == 0.8
    assert entity.salience == 0.6
    assert entity.sentiment == 0.7
    assert entity.is_custom == False

def test_entity_mention_creation(dbsession):
    doc = Document(content="Test content")
    entity = Entity(document_id=doc.id, name="Test Entity")
    dbsession.add_all([doc, entity])
    dbsession.commit()

    mention = EntityMention(
        entity_id=entity.id,
        text="Test Mention",
        begin_offset=0.0,
        end_offset=12.0,
        confidence=0.9
    )
    dbsession.add(mention)
    dbsession.commit()

    assert mention.id is not None
    assert isinstance(mention.id, uuid.UUID)
    assert mention.entity_id == entity.id
    assert mention.text == "Test Mention"
    assert mention.begin_offset == 0.0
    assert mention.end_offset == 12.0
    assert mention.confidence == 0.9

def test_category_creation(dbsession):
    doc = Document(content="Test content")
    dbsession.add(doc)
    dbsession.commit()

    category = Category(
        document_id=doc.id,
        category_id="test_category",
        name="Test Category",
        path="/test/path",
        confidence=0.85,
        is_primary=True
    )
    dbsession.add(category)
    dbsession.commit()

    assert category.id is not None
    assert isinstance(category.id, uuid.UUID)
    assert category.document_id == doc.id
    assert category.category_id == "test_category"
    assert category.name == "Test Category"
    assert category.path == "/test/path"
    assert category.confidence == 0.85
    assert category.is_primary == True

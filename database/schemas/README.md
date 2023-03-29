# Database schemas

In this directory we keep the information about how our data is stored in the database.
This is done with schema json files, which comes in handy as mongoDB uses BSON (binary json)
to store documents. Constraints to these documents can be made by specifying schema json files
for each collection of documents.

Each schema includes at least the following properties:
- `_id`: unique objectID identifier, usually set by mongoDB when inserting a document
- `_schemaVersion`: Version of the schema used in the document.
    This may come in handy when adapting the schemas for new problem and not wanting to
    update every single document of said collection.

The schema files are also used for [insertion and update validation](https://www.mongodb.com/docs/manual/core/schema-validation/).

const env = process.env;

var db = connect(
    `mongodb://${env.MONGO_INITDB_ROOT_USERNAME}:${env.MONGO_INITDB_ROOT_PASSWORD}@localhost:27017/`,
);

db = db.getSiblingDB(env.MONGO_DATABASE_NAME); // we can not use "use" statement here to switch db

db.createUser({
    user: env.DB_BACKEND_USER,
    pwd: env.DB_BACKEND_PASSWORD,
    roles: [{ role: "readWrite", db: env.MONGO_DATABASE_NAME }],
    passwordDigestor: "server",
});

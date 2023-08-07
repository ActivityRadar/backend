var db = connect("mongodb://admin:pass@localhost:27017/admin");

db = db.getSiblingDB('AR'); // we can not use "use" statement here to switch db

db.createUser(
    {
        user: "",
        pwd: "",
        roles: [ { role: "readWrite", db: "AR"} ],
        passwordDigestor: "server",
    }
)

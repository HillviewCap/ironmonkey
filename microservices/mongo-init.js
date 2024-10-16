db = db.getSiblingDB('admin');

db.createUser(
  {
    user: "ironmonkey",
    pwd: "ironmonkey",
    roles: [ { role: "userAdminAnyDatabase", db: "admin" }, "readWriteAnyDatabase" ]
  }
);

db.auth('ironmonkey', 'ironmonkey');

db = db.getSiblingDB('threats_db');

db.createUser(
  {
    user: "ironmonkey",
    pwd: "ironmonkey",
    roles: [ { role: "readWrite", db: "threats_db" } ]
  }
);

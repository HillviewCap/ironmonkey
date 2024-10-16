db.auth('ironmonkey', 'ironmonkey')

db = db.getSiblingDB('admin')

db.createUser(
  {
    user: "ironmonkey",
    pwd: "ironmonkey",
    roles: [ { role: "userAdminAnyDatabase", db: "admin" }, "readWriteAnyDatabase" ]
  }
)

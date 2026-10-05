## Overview
User authorizations within an account will be defined by roles. The roles table is responsible for storing all currently defined roles. Roles can only be created by the privileged database user. Roles are not authorized to be created through the API to prevent role sprawl and any difficulties managing role authorizations. See [available roles](#available-roles) to learn about the currently defined roles.

---

## Schema
```sql
CREATE TABLE roles (
    role_id     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR()
);
```

<br>

---

## Security and API Permissions
**API Permissions** are assigned to the database user the API uses to access the table to minimize unnecessary privileges and data over exposure at the data layer.  

### API Permissions
#### SELECT Permissions 
```sql
GRANT SELECT ON roles TO playground_user_1;
```
SELECT operations on the account_memberships table are not restricted via API permissions. The API needs complete read access to entries within roles to assess what authorizations a user has within an account.

#### UPDATE Permissions 
UPDATE operations on the users table will not be accessible through the API. Roles can only be altered by the privileged database account.

#### INSERT Permissions
INSERT operations on the users table will not be accessible through the API. Roles can only be created by the privileged database account.

#### DELETE Permissions
DELETE operations on the users table will not be accessible through the API.Roles can only be removed by the privileged database account.

---

## Available Roles
- **User:** Basic user account with basic read-only permission within account and privileged access to own resources and resources assigned by manager or admin.
- **Manager:** Privileged user for users assigned to manage resources within an account.
- **Admin:** Superuser with complete control of account including account members. WARNING: Due to privileged nature of account, use sparingly.

---

## Relationships
- [account_memberships](account_memberships.md)

<br>
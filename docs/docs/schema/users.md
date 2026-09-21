## Overview
The users table serves to store individual user account information. User accounts will be the main 
object to determine authentication to and authorizations within an [account](/schema/accounts).

## Schema
```sql
CREATE TABLE users (
    user_id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name    VARCHAR(50) NOT NULL,
    last_name     VARCHAR(50) NOT NULL,
    username      VARCHAR(50) NOT NULL UNIQUE,
    password      VARCHAR(100) NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE,
    email_verified BOOLEAN DEFAULT FALSE NOT NULL,
    phone         VARCHAR(15) NOT NULL,
    dob           DATE NOT NULL,
    address       VARCHAR(150) NOT NULL,
    city          VARCHAR(50) NOT NULL,
    state         VARCHAR(50) NOT NULL,
    zipcode       VARCHAR(20) NOT NULL,
    country       VARCHAR(50) NOT NULL,
    company       VARCHAR(50),
    created_at    TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at    TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    active        BOOLEAN DEFAULT TRUE NOT NULL
);
```

## Security and API Permissions
**Row Level Security (RLS)** is enabled and enforced on the users table to control what data a
user can access. Specifically scoping a user to only accessing and altering their own information based
on their _*user_id*_ injected at time of operation using `SET LOCAL app.current_user_id`. User's 
user_id will be attached to JWT token during their session.

**RLS Policies**:  
\- _*select_own_user*_: limits rows users are able to select to only rows that are attached to their _*user_id*_. 
Users attempting to select from the users table without valid user_id will be blocked.
```sql
CREATE POLICY select_own_user ON users FOR SELECT TO playground_user_1 
USING (
    user_id = current_setting('app.current_user_id', true)::integer
)
```
\- _*update_own_user*_: limits rows users are able to update to only rows that are attached to their _*user_id*_.
Users attempting to update data within the users table without valid user_id will be blocked.
```sql
CREATE POLICY update_own_user ON users FOR UPDATE TO playground_user_1 
USING (
    user_id = current_setting('app.current_user_id', true)::integer
) 
WITH CHECK (
    user_id = current_setting('app.current_user_id', true)::integer
)
```
<br>
**Permissions** are assigned to the database user the API uses to access the table to 
minimize unnecessary privileges and over exposure at the data layer.  

**API account permissions**:  
\- SELECT Permissions: Authenticated users will be able to select most information that is relevant to 
their user account. Excludes: user_id (attached to JWT after user authenticates) and password (only 
exposed at time of login). See [get_user_for_login()](/schema/functions/#get_user_for_logintext) for 
more information. 
```sql
GRANT SELECT (first_name, last_name, username, email, email_verified, phone, dob, company, address, city, zipcode, country, created_at, updated_at, active) ON users TO playground_user_1
```
\- UPDATE Permissions: Authenticated users will be able to update most information that is relevant to
their user account. 
```sql
GRANT UPDATE (first_name, last_name, username, password, email, phone, dob, company, address, city, zipcode, country) ON users TO playground_user_1
```

## Triggers
```sql
CREATE TRIGGER trg_users_freeze_created_at
BEFORE UPDATE
ON users
FOR EACH ROW
EXECUTE FUNCTION prevent_created_at_update()
```

```sql
CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE
ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at()
```

## Relationships

# Functions

## Overview
Functions have been added to the database to minimize data exposure and allow for certain 
functionality within the database. This section covers every function within the database and
use cases within the application.

## Pre-Authentication Functions
Functions have been created to allow limited access to data and functionality required for 
pre-authenticated workflows

### get_user_for_login(text)
```sql
# Function
CREATE FUNCTION get_user_for_login(p_username text)
RETURNS TABLE
    (
        user_id integer,
        password_hash text
    ) SECURITY DEFINER
SET search_path = public
LANGUAGE sql
AS $$
    SELECT user_id, password
    FROM users
    WHERE username = p_username;
$$

# Grant execution privileges on the function to API user
GRANT EXECUTE ON FUNCTION get_user_for_login(text) TO playground_user_1
```
To limit data exposure for users logging into the application, _*get_user_for_login(text)*_ is used to
inject only the user_id and password_hash to be used during the login process. Doing this leaves
the rest of the user information protected behind RLS policies that require a valid user_id to access
the users table. See [users schema](/schema/users/#security-and-api-permissions) for more information
on relevant policies and permissions.

## Table Functions
```sql
CREATE FUNCTION prevent_created_at_update()
    RETURNS trigger
    LANGUAGE plpgsql
AS $$
    BEGIN
        NEW.created_at = OLD.created_at;
        RETURN NEW;
    END;
$$
```

```sql
CREATE FUNCTION set_updated_at()
    RETURNS trigger
    LANGUAGE plpgsql
AS $$
    BEGIN
        NEW.updated_at = now();
        RETURN NEW;
    END;
$$
```
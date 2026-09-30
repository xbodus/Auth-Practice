## Overview
The role of the account_memberships table is to track user's account memberships and roles within those accounts. This table works by using foreign keys to the users, accounts, and roles tables to minimize re-entering information.

---

## Schema
```sql
CREATE TABLE account_memberships (
    account_id  INTEGER NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role_id     INTEGER NOT NULL REFERENCES roles(role_id) ON DELETE NO ACTION,
    created_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    PRIMARY KEY (account_id, user_id)
);
```

<br>

---

## Security and API Permissions
**Row Level Security (RLS)** is enabled and enforced on the account_memberships table to control authorizations for the API and database users. For example, specifically scoping a user to only accessing and altering their own information based on their _*user_id*_ injected at time of operation using `SET LOCAL app.current_user_id`. User's user_id will be attached to JWT token during their session.

**API Permissions** are assigned to the database user the API uses to access the table to minimize unnecessary privileges and data over exposure at the data layer.  

### RLS Policies
#### select_own_account_memberships
```sql
CREATE POLICY select_own_account_memberships ON account_memberships FOR SELECT TO playground_user_1
USING (
    EXISTS (
        SELECT 1 FROM account_memberships am
        WHERE am.account_id = account_memberships.account_id
            AND am.user_id = current_setting('app.current_user_id', true)::integer
    )
);
```
Limits rows users can SELECT on the account_memberships table to rows where the ***set user_id*** *is a member of the account*. The user_id is set during the transaction using `SET LOCAL app.current_user_id`. Attempting to select account_memberships that do not have the set app.current_user_id as a member will return zero results.

#### admin_manage_account_members
```sql
CREATE POLICY admin_manage_account_members ON account_memberships FOR UPDATE TO playground_user_1
USING (
    EXISTS (
        SELECT 1 FROM account_memberships am
        JOIN roles r ON r.role_id = am.role_id
        WHERE am.account_id = account_memberships.account_id
            AND am.user_id = current_setting('app.current_user_id', true)::integer
            AND r.name = 'admin'
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1 FROM account_memberships am
        JOIN roles r ON r.role_id = am.role_id
        WHERE am.account_id = account_memberships.account_id
            AND am.user_id = current_setting('app.current_user_id', true)::integer
            AND r.name = 'admin'
    )
);
```
Limits rows users can UPDATE on the account_memberships table to rows where the ***set user_id*** *is a member of account AND is assigned the admin role within the account*. Standard users should not be allowed to update the roles of others within an account, this privilege is reserved only for account admins. The user_id is set during the transaction using `SET LOCAL app.current_user_id`. Attempting to update accounts that do not have the set app.current_user_id as a member or as a non-admin will be blocked.

#### admin_add_account_members
```sql
CREATE POLICY admin_add_account_members ON account_memberships FOR INSERT TO playground_user_1
WITH CHECK (
    EXISTS (
        SELECT 1 FROM account_memberships am_actor
        JOIN roles r ON r.role_id = am_actor.role_id
        WHERE am_actor.account_id = account_memberships.account_id
            AND am_actor.user_id = current_setting('app.current_user_id', true)::integer
            AND r.name = 'admin'
    )
);
```
Limits INSERT privileges to add new account members on the account_memberships table to users where the ***set user_id*** *is a member of account AND is assigned the admin role within the account*. Standard users should not be allowed to add account members to avoid shadow memberships, this privilege is reserved only for account admins. The user_id is set during the transaction using `SET LOCAL app.current_user_id`. Attempting to update accounts that do not have the set app.current_user_id as a member or as a non-admin will be blocked.

#### admin_remove_account_members
```sql
CREATE POLICY admin_remove_account_members ON account_memberships FOR DELETE TO playground_user_1
USING (
    EXISTS (
        SELECT 1 FROM account_memberships am
        JOIN roles r ON r.role_id = am.role_id
        WHERE am.account_id = account_memberships.account_id
            AND am.user_id = current_setting('app.current_user_id', true)::integer
            AND r.name = 'admin'
    )
);
```
Limits DELETE privileges to remove account members on the account_memberships table to users where the ***set user_id*** *is a member of account AND is assigned the admin role within the account*. Standard users should not be allowed to remove account members to avoid privilege abuse, this privilege is reserved only for account admins. The user_id is set during the transaction using `SET LOCAL app.current_user_id`. Attempting to update accounts that do not have the set app.current_user_id as a member or as a non-admin will be blocked.

<br>

### API Permissions
#### SELECT Permissions
```sql
GRANT SELECT ON account_memberships TO playground_user_1;
```
SELECT operations on the account_memberships table are not restricted via API permissions. The API needs complete read access to entries within account_memberships to assess who is a member of what account, and what is their role within the account. Selections within the account_memberships table will primarily take place using the account_id and/or user_id. 

#### UPDATE Permissions
```sql
GRANT UPDATE (role_id) ON account_memberships TO playground_user_1;
```
UPDATE operations on the account_memberships table is restricted to only allowing updates to a member's role within an account via an admin account. Adding and removing membership is handled by INSERT and DELETE operations.

#### INSERT Permissions
```sql
GRANT INSERT (account_id, user_id, role_id) ON account_memberships TO playground_user_1;
```
INSERT operations on the account_memberships table standardize inputs to existing accounts, users, and roles—created_at will be automatically generated at time of creation using the default value. INSERT operations are the method of adding a user as an account member. Only account admins are permitted to add users to an account, execpt on account creation—which will have the original user automatically added to the account as admin.

#### DELETE Permissions
```sql
GRANT DELETE ON account_memberships TO playground_user_1;
```
DELETE operations on the account_memberships table are permitted via the API. DELETE operations are the method of removing a user as an account member. Only account admins are permitted to remove users from an account, except if there's only one admin left on an account. All accounts must have one admin to avoid soft-locking authorization within an account.

---

## Triggers
### trg_account_memberships_freeze_created_at
```sql
CREATE TRIGGER trg_account_memberships_freeze_created_at
BEFORE UPDATE
ON account_memberships
FOR EACH ROW
EXECUTE FUNCTION prevent_created_at_update();
```
Entries entered into the account_memberships table will automatically have a create_at value assigned to the entry at time of creation. This value is intended for accurate historical records, and should not be modified via the API or any privileged database user. To ensure this, `trg_account_memberships_freeze_created_at` calls [prevent_created_at_update()](functions.md#prevent_created_at_update) to revert any potential updates to the created_at value to the original value.

### trg_prevent_last_admin_removal
```sql
CREATE TRIGGER trg_prevent_last_admin_removal
BEFORE UPDATE OR DELETE ON account_memberships
FOR EACH ROW
EXECUTE FUNCTION prevent_last_admin_removal();
```
Accounts must have at least one active admin within an account. This is important to avoid soft-locking an account, as admins have ultimate control of authorizations within an account and account state, such as activating or deactivating an account. Users attempting to update the last admin to a non-admin role or delete the last admin will trigger `trg_prevent_last_admin_removal`. See [prevent_last_admin_removal()](functions.md#prevent_last_admin_removal) for more information about the function that prevents the last admin removal.

---

## Relationships
- [users](users.md)
- [accounts](accounts.md)
- [roles](roles.md)
-- Postgres 18 Seed Data for test database using pytest-postgres
-- Seeding handled by root Postgres user
-- playground_app = Test database admin account
-- playground_user_1 = Test FastAPI user account

-- As root user
-- 1. Create users if not existing
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'playground_app') THEN
        CREATE ROLE playground_app WITH LOGIN PASSWORD 'postgres';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'playground_user_1') THEN
        CREATE ROLE playground_user_1 WITH LOGIN PASSWORD 'postgres';
    END IF;
END
$$;

-- 2. Create user table and set owner to playground_app
CREATE TABLE users(
    user_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    email_verified BOOLEAN DEFAULT FALSE NOT NULL,
    phone VARCHAR(15) NOT NULL,
    dob DATE NOT NULL,
    address VARCHAR(150) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    zipcode VARCHAR(20) NOT NULL,
    country VARCHAR(50) NOT NULL,
    company VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL, -- Function will be created to freeze this value from being updated
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL -- Function will be created to update this time every time the user UPDATES an entry
);

ALTER TABLE users OWNER TO playground_app;

-- 3. Enable & Force RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

-- 4. Create table policies
CREATE POLICY select_own_user ON users FOR SELECT TO playground_user_1 USING (user_id = current_setting('app.current_user_id', true)::integer);
GRANT SELECT (first_name, last_name, username, email, email_verified, phone, dob, company, address, city, state, zipcode, country, created_at, updated_at) ON users TO playground_user_1;

CREATE POLICY update_own_user ON users FOR UPDATE TO playground_user_1 USING (user_id = current_setting('app.current_user_id', true)::integer) WITH CHECK (user_id = current_setting('app.current_user_id', true)::integer);
GRANT UPDATE (first_name, last_name, username, password, email, phone, dob, company, address, city, state, zipcode, country) ON users TO playground_user_1;

-- 5. Create functions and triggers
-- Function for allowing FastAPI to authenticate users before issuing JWT token
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
$$;

GRANT EXECUTE ON FUNCTION get_user_for_login(text) TO playground_user_1;

-- Function and trigger for updating entry updated_at value on UPDATE operations
CREATE FUNCTION set_updated_at()
       RETURNS trigger
       LANGUAGE plpgsql
AS $$
   BEGIN
    NEW.updated_at
   = now();
   RETURN NEW;
   END;
$$;

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE
ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- Function and trigger for silently rolling back created_at value if user gets past table privileges and tried to update created_at value
CREATE FUNCTION prevent_created_at_update()
   RETURNS trigger
   LANGUAGE plpgsql
AS $$
   BEGIN
        NEW.created_at = OLD.created_at;
        RETURN NEW;
    END;
$$;

CREATE TRIGGER trg_users_freeze_created_at
BEFORE UPDATE
ON users
FOR EACH ROW
EXECUTE FUNCTION prevent_created_at_update();


CREATE FUNCTION reset_email_verified_on_change()
       RETURNS trigger
       LANGUAGE plpgsql
AS $$
   BEGIN
        IF
   NEW.email IS DISTINCT FROM OLD.email THEN
            NEW.email_verified = false;
   END IF;
   RETURN NEW;
   END;
$$;

CREATE TRIGGER trg_update_email_verified
BEFORE UPDATE
ON users
FOR EACH ROW
EXECUTE FUNCTION reset_email_verified_on_change();


-- 6. Create seed data
INSERT INTO users(first_name, last_name, username, password, email, email_verified, phone, dob, address, city, state, zipcode, country, company)
VALUES ('Paul', 'McDaniels', 'acmeemployee1', 'Pa55w0rd!', 'pmcdaniels@acme.com', true, '123-456-7890', '10-21-1978', '123 Springfield ave', 'Atlanta', 'Georgia', '30303', 'United States', 'ACME Manufacturing');
INSERT INTO users(first_name, last_name, username, password, email, email_verified, phone, dob, address, city, state, zipcode, country, company)
VALUES ('Marleen', 'Smith', 'PandoraIsLuv', 'Pa55w0rd!', 'marmarmith@gmail.com', false, '980-567-1234', '02-10-1990', '45 Greek Ln', 'Springfield', 'Missouri', '65801', 'United States', null);
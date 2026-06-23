use db_highnoon

-- creating user table

CREATE TABLE tbl_users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at DATETIME2 DEFAULT GETDATE()
);

-- creating role table
create table tbl_role(
    role_id INT IDENTITY(1,1) PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    role_description VARCHAR(150) NOT NULL

);

-- altering data type of role column from int to varchar in tbl_users
alter table tbl_users
alter column role INT

-- adding fk constraint to role column in tbl_users
alter table tbl_users
add constraint fk_role
foreign key (role) references tbl_role(role_id);

-- creating visitors table
CREATE TABLE tbl_visitors(
    visitor_id INT IDENTITY(1,1) PRIMARY KEY,
    visitor_name VARCHAR(100) NOT NULL,
    visitor_email VARCHAR(100) NOT NULL UNIQUE,
    visitor_phone VARCHAR(15) NOT NULL,
    viitor_cnic VARCHAR(20) NOT NULL UNIQUE,
    purpose_of_visit VARCHAR(255) NOT NULL,
    department_to_visit VARCHAR(100) NOT NULL,
    visiting_employee VARCHAR(100) NOT NULL,
    visitor_created_at DATETIME2 DEFAULT GETDATE()
);


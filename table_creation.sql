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
    visitor_cnic VARCHAR(20) NOT NULL UNIQUE,
    visitor_created_at DATETIME2 DEFAULT GETDATE()
);

-- creating employees table
CREATE TABLE tbl_employees(
    employee_id INT IDENTITY(1,1) PRIMARY KEY,
    employee_name VARCHAR(100) NOT NULL,
    employee_email VARCHAR(100) NOT NULL UNIQUE,
    employee_phone VARCHAR(15) NOT NULL,
    employee_cnic VARCHAR(20) NOT NULL UNIQUE,
    employee_designation VARCHAR(150) NOT NULL,
    employee_department int NOT NULL,
    employee_created_at DATETIME2 DEFAULT GETDATE()
);

-- creating departments table
create table tbl_departments(
    department_id INT IDENTITY(1,1) PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE
);

-- adding fk constraint to employee_department column in tbl_employees
alter table tbl_employees
add constraint fk_department
foreign key (employee_department) references tbl_departments(department_id);

-- creating visitor card table
CREATE TABLE tbl_visitor_cards(
    card_id INT IDENTITY(1,1) PRIMARY KEY,
    card_color VARCHAR(50) NOT NULL,
    card_access_level VARCHAR(50) NOT NULL
);

-- creating visits table
CREATE TABLE tbl_visits(
    visit_id INT IDENTITY(1,1) PRIMARY KEY,
    visitor_id INT NOT NULL,
    employee_id INT NOT NULL,
    card_id INT NOT NULL,
    purpose_of_visit VARCHAR(255) NOT NULL,
    check_in_time DATETIME2 DEFAULT GETDATE(),
    check_out_time DATETIME2,
    status VARCHAR(20) NOT NULL
);

-- adding fk constraint to visitor_id column in tbl_visits
alter table tbl_visits
add constraint fk_visitor
foreign key (visitor_id) references tbl_visitors(visitor_id);

-- adding fk constraint to employee_id column in tbl_visits
alter table tbl_visits
add constraint fk_employee
foreign key (employee_id) references tbl_employees(employee_id);

-- adding fk constraint to card_id column in tbl_visits
alter table tbl_visits
add constraint fk_card
foreign key (card_id) references tbl_visitor_cards(card_id);

-- creating appointments table
CREATE TABLE tbl_appointments(
    appointment_id INT IDENTITY(1,1) PRIMARY KEY,
    visitor_id INT NOT NULL,
    employee_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    purpose_of_appointment VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL default 'pending',
    created_by_user INT NOT NULL,
    created_at DATETIME2 DEFAULT GETDATE()
);

-- adding fk constraint to visitor_id column in tbl_appointments
alter table tbl_appointments
add constraint fk_appointment_visitor
foreign key (visitor_id) references tbl_visitors(visitor_id);

-- adding fk constraint to employee_id column in tbl_appointments
alter table tbl_appointments
add constraint fk_appointment_employee
foreign key (employee_id) references tbl_employees(employee_id);

-- adding fk constraint to created_by_user column in tbl_appointments
alter table tbl_appointments
add constraint fk_appointment_user
foreign key (created_by_user) references tbl_users(user_id);

-- creating blacklist table
CREATE TABLE tbl_blacklist(
    blacklist_id INT IDENTITY(1,1) PRIMARY KEY,
    visitor_id INT NOT NULL,
    reason VARCHAR(255) NOT NULL,
    added_by_user INT NOT NULL,
    blacklisted_at DATETIME2 DEFAULT GETDATE(),
    status VARCHAR(20) NOT NULL default 'active'
);

-- adding fk constraint to visitor_id column in tbl_blacklist
alter table tbl_blacklist
add constraint fk_blacklist_visitor
foreign key (visitor_id) references tbl_visitors(visitor_id);

-- adding fk constraint to added_by_user column in tbl_blacklist
alter table tbl_blacklist
add constraint fk_blacklist_user
foreign key (added_by_user) references tbl_users(user_id);


-- creating reports type table
CREATE TABLE tbl_report_types(
    report_type_id INT IDENTITY(1,1) PRIMARY KEY,
    report_type_name VARCHAR(100) NOT NULL UNIQUE
);

-- creating reports table
CREATE TABLE tbl_reports(
    report_id INT IDENTITY(1,1) PRIMARY KEY,
    report_type_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_visits INT NOT NULL,
    total_visitors INT NOT NULL,
    total_employees INT NOT NULL,
    total_departments INT NOT NULL,
    total_appointments INT NOT NULL,
    generated_by_user INT NOT NULL,
    generated_at DATETIME2 DEFAULT GETDATE()

);

-- adding fk constraint to report_type_id column in tbl_reports
alter table tbl_reports
add constraint fk_report_type
foreign key (report_type_id) references tbl_report_types(report_type_id);

-- adding fk constraint to generated_by_user column in tbl_reports
alter table tbl_reports
add constraint fk_report_user
foreign key (generated_by_user) references tbl_users(user_id);
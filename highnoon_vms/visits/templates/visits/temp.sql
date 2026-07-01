select *
from visits_visit


select *
from employees_employee

select *
from visitors_visitor_card

insert into visits_visit (visit_purpose, check_in_time,check_out_time,status,employee_id,visitor_id,visitor_card_id)
VALUES
('document deliver','2026-06-30 10:11:31.962446',NULL,'Checked In', 4,11,10 )
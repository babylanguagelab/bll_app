select child_id, avg(child_count), avg(adult_count), avg(adult_child_ratio) from data group by child_id;

select adult_child_ratio, avg(child_count), avg(adult_count) from data group by adult_child_ratio;

select ind as idx, file_name, child_count, adult_count, adult_child_ratio from data;
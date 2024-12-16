SQL-запросы:
1. Добавить пользователя в БД
2. Создать задачу в problems
3. Создать вариант в problems
4. Создать д/з для группы
5. Получить имена и фамилии всех пользователей в группе по имени name
6. Получить по user_id и problem_id историю решения пользователем задачи
7. По user_id и variant_id получить таблицу problem_id и булевскую величину is_correct
8. Получить по user_id общий процент правильности выполнения заданий с первой попытки
9. Получить по user_id общий процент правильности выполнения заданий с любой попытки
10. Получить по user_id и дате количество правильно и неправильно решённых в эту дату задач


--------------------------------------------------------------------------------------------------------------
1. 
INSERT TO users 
VALUES (kwargs)

2. 
INSERT TO problems
VALUES (kwargs)

3. 
INSERT TO variants
VALUES (kwargs)
for problem_id in kwargs[problem_ids]:
    INSERT TO variant_problem
    VALUES (kwargs[variant_id], problem_id)

4.  
INSERT TO assignments
VALUES (kwargs)
for variant_id in kwargs[variant_ids]:
    INSERT TO assignment_variant
    VALUES (kwargs[assignment_id], variant_id, kwargs)
for user in kwargs[users]:
    INSERT TO assignment_user
    VALUES (kwargs[assignment_id], user)
for group in kwargs[group_ids]:
    INSERT TO assignment_group
    VALUES (kwargs[assignment_id], group)

5.
SELECT first_name, second_name FROM 
users INNER JOIN user_group
on user.user_id = user_group.user_id
INNER JOIN groups
on user_group.group_id = groups.group_id
WHERE groups.group_name = "{name}"

6. SELECT user_answer, completion_time, is_right 
FROM user_problem WHERE user_id = {user_id} AND problem_id = {problem_id} 

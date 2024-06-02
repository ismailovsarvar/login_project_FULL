import psycopg2
import sys
import utils
from service import session
from db import cur, conn, commit
from models import Todo, TodoType
from service import login


def update_todo(update_todo_id, title) -> utils:
    if update_todo_id:
        try:
            cur.execute("""SELECT * FROM todos WHERE id=%s"""), (update_todo_id,)
            todo_data = cur.fetchone()
            if todo_data:
                return utils.BadRequest('Todo Not Found')
            else:
                todo: Todo = Todo(title=title, session.session.id)
                cur.execute("""UPDATE todos SET title=%s WHERE id=%s, update_todo_id""")
                return utils.ResponseData('Todo Updated')
        except psycopg2.Error as e:
            conn.Rollback
            return utils.BadRequest('Database Error')
    else:
        return utils.BadRequest('Todo Not Found')


def delete_todo(delete_todo_id) -> utils:
    if delete_todo_id:
        try:
            cur.execute("""DELETE FROM todos WHERE id""")
            return utils.ResponseData('TOdo deleted')
        except psycopg2.Error as e:
            conn.Rollback
            return utils.BadRequest('Database Error')

from typing import Union

import utils
from db import commit
from db import cur, conn
from dto import UserRegisterDTO
from models import User, UserRole, UserStatus, TodoType
from sessions import Session
from utils import login_required
from validators import check_validators

session = Session()


def get_user_data(prm: str, atr: str | int) -> tuple:
    cur.execute(f"""SELECT * FROM users WHERE {prm} =  %s""", (atr,))
    data = cur.fetchone()
    return data


@commit
def login(username: str, password: str) -> Union[utils.BadRequest, utils.ResponseData]:
    user: User | None = session.check_session()
    if user:
        return utils.BadRequest('You already logged in', status_code=401)

    get_user_by_username = '''SELECT * FROM users WHERE username = %s;'''
    cur.execute(get_user_by_username, (username,))
    user_data = cur.fetchone()
    if not user_data:
        return utils.BadRequest('Bad credentials', status_code=401)
    user = User.from_tuple(user_data)
    if user.login_try_count >= 3:
        return utils.BadRequest('User is blocked')
    if not utils.check_password(password, user.password):
        update_count_query = """UPDATE users SET login_try_count = login_try_count + 1 WHERE username = %s;"""
        cur.execute(update_count_query, (user.username,))
        conn.commit()
        return utils.BadRequest('Bad credentials', status_code=401)

    session.add_session(user)
    return utils.ResponseData('User Successfully Logged in')


def register(dto: UserRegisterDTO):
    try:
        check_validators(dto)
        user_data = '''SELECT * FROM users WHERE username = %s;'''
        cur.execute(user_data, (dto.username,))
        user = cur.fetchone()
        if user:
            return utils.BadRequest('User already registered', status_code=401)

        insert_user_query = """
        INSERT INTO users(username,password,role,status,login_try_count)
        VALUES (%s,%s,%s,%s,%s);
        """
        user_data = (dto.username, utils.hash_password(dto.password), UserRole.USER.value, UserStatus.ACTIVE.value, 0)
        cur.execute(insert_user_query, user_data)

        conn.commit()
        cur.execute("""SELECT id FROM users WHERE username=%s""", (dto.username,))
        user_id = cur.fetchone()
        user = User(username=dto.username,
                    password=utils.hash_password(dto.password),
                    user_id=user_id[0],
                    role=UserRole.USER.value,
                    status=UserStatus.ACTIVE.value,
                    login_try_count=0)
        session.add_session(user)
        return utils.ResponseData('User Successfully Registered👌')

    except AssertionError as e:
        return utils.BadRequest(e)


def logout():
    global session
    if session.check_session():
        session.session = None
        return utils.ResponseData('User Successfully Logged Out !!!')


@login_required
@commit
def todo_add(title: str):
    insert_query = """INSERT INTO todos(name,todo_type,user_id)
        VALUES (%s,%s,%s);
        """
    data = (title, TodoType.Personal.value, session.session.id)

    cur.execute(insert_query, data)
    return utils.ResponseData('INSERTED TODO')


def user_blocked(_id: str):
    global session
    cur.execute("""UPDATE users SET login_try_count=4 WHERE id = %s""", (_id,))
    conn.commit()
    return utils.ResponseData('User Successfully Blocked')


def is_admin():
    global session
    if session.session.role == UserRole.SUPERADMIN.value:
        return True
    else:
        return False

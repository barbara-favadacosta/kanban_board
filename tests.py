
import os
import unittest
from flask import url_for
from kanban import app, db
import kanban
from flask_login import login_user, logout_user, current_user



class AppTests(unittest.TestCase):

####################################################################
# Config Section
####################################################################
    # executed before each test
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        self.client = app.test_client()
        db.drop_all()
        db.create_all()

    # executed after each test
    def tearDown(self):
        db.drop_all()

####################################################################
# Helper functions Section
####################################################################
    #Inserts an user into the database - this function
    #is used to test task manipulation, since you can only do That
    #under an existing user
    def insert_user(self,username, password):
        user = kanban.User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

    def insert_task_types(self):
        types = list()
        t1 = kanban.TodoType.query.filter(kanban.TodoType.id==1).filter(kanban.TodoType.type=="todo").first()
        if not t1:
            types.append(kanban.TodoType(id=1, type="todo"))
        t1 = kanban.TodoType.query.filter(kanban.TodoType.id==2).filter(kanban.TodoType.type=="doing").first()
        if not t1:
            types.append(kanban.TodoType(id=2, type="doing"))
        t1 = kanban.TodoType.query.filter(kanban.TodoType.id==3).filter(kanban.TodoType.type=="done").first()
        if not t1:
            types.append(kanban.TodoType(id=3, type="done"))
        if types:
            db.session.add_all(types)
            db.session.commit()

####################################################################
# Test Section
####################################################################

####################################################################
# Test Section - Register, Login, Logout
####################################################################
    def test_main_page_after_register(self):
        reg = self.client.post(
            '/register',
            data=dict(username="Bobo", password="passw"),
            follow_redirects=True
        )
        #All the self.AssertIn functions check if determined sentence
        #is returned by the request. Depending on the operation, I
        #added key sentences to return with the request and display
        #on the html pages
        self.assertIn(b'Registered with success!', reg.data)

    def test_login_user(self):
        username = "Test User"
        password = "password"
        log = self.insert_user(username, password)
        return self.client.post(
            '/login',
            data=dict(username=username, password=password),
            follow_redirects=True
        )
        self.assertIn(b'SUCH TO DO', log.data)

    def test_main_page_without_login(self):
        response = self.client.get('/',follow_redirects=True)
        self.assertIn(b'Click Here to Register!', response.data)

    def test_invalid_username_login(self):
        username = "Test User"
        password = "password"
        log = self.insert_user(username, password)
        log = self.client.post(
            '/login',
            data=dict(username="Another User", password=password),
            follow_redirects=True
        )
        self.assertIn(b'Invalid Username', log.data)

    def test_invalid_password_login(self):
        username = "Test User"
        password = "password"
        log = self.insert_user(username, password)
        log =  self.client.post(
            '/login',
            data=dict(username=username, password="passw"),
            follow_redirects=True
        )
        self.assertIn(b'Invalid Password', log.data)

    def test_logout(self):
        with self.client:
            username = "Test User"
            password = "password"
            log = self.insert_user(username, password)
            log =  self.client.post(
                '/login',
                data=dict(username=username, password=password),
                follow_redirects=True
            )
            logout = self.client.get('/logout',follow_redirects=True)
            self.assertIn(b'Click Here to Register!', logout.data)

####################################################################
# Test Section - Task related tests
####################################################################
    def test_add_todo_task(self):
        with self.client:
            username = "Test User"
            password = "password"
            log = self.insert_user(username, password)
            log =  self.client.post(
                '/login',
                data=dict(username=username, password=password),
                follow_redirects=True
            )
            self.insert_task_types()
            response = self.client.post('/addTodoTask', data=dict(todoitem='To Do Task'),follow_redirects=True)
            self.assertIn(b'To Do Task', response.data)


    def test_add_doing_task(self):
        with self.client:
            username = "Test User"
            password = "password"
            log = self.insert_user(username, password)
            log =  self.client.post(
                '/login',
                data=dict(username=username, password=password),
                follow_redirects=True
            )
            self.insert_task_types()
            response = self.client.post('/addDoingTask', data=dict(todoitem='Doing Task'),follow_redirects=True)
            self.assertIn(b'Doing Task', response.data)

    def test_add_done_task(self):
        with self.client:
            username = "Test User"
            password = "password"
            log = self.insert_user(username, password)
            log =  self.client.post(
                '/login',
                data=dict(username=username, password=password),
                follow_redirects=True
            )
            self.insert_task_types()
            response = self.client.post('/addDoneTask', data=dict(todoitem='Done Task'),follow_redirects=True)
            self.assertIn(b'Done Task', response.data)

    #All 3 tests below check if when trying to access the add routes,
    #the app redirects to the login page, as this is a restricted area
    def test_add_todo_task_without_login(self):
        self.insert_task_types()
        response = self.client.post('/addTodoTask', data=dict(todoitem='To Do Task'),follow_redirects=True)
        self.assertIn(b'Click Here to Register!', response.data)

    def test_add_doing_task_without_login(self):
        self.insert_task_types()
        response = self.client.post('/addDoingTask', data=dict(todoitem='Doing Task'),follow_redirects=True)
        self.assertIn(b'Click Here to Register!', response.data)

    def test_add_done_task_without_login(self):
        self.insert_task_types()
        response = self.client.post('/addDoneTask', data=dict(todoitem='Done Task'),follow_redirects=True)
        self.assertIn(b'Click Here to Register!', response.data)

    #Check that tasks added under an user, stay under that user
    def test_task_belongs_to_right_user(self):
        with self.client:
            username = "Test User"
            password = "password"
            log = self.insert_user(username, password)
            log =  self.client.post(
                '/login',
                data=dict(username=username, password=password),
                follow_redirects=True
            )
            self.insert_task_types()
            response = self.client.post('/addTodoTask', data=dict(todoitem='add To Do Task'),follow_redirects=True)
            logout = self.client.get('/logout',follow_redirects=True)
            username = "Another User"
            password = "password"
            log = self.insert_user(username, password)
            log =  self.client.post(
                '/login',
                data=dict(username=username, password=password),
                follow_redirects=True
            )
            todo = kanban.Todo.query.filter(kanban.TodoType.type=="todo").filter(kanban.Todo.text=="add To Do Task").filter(kanban.Todo.userid==current_user.get_id()).first()
            self.assertTrue(todo==None)

        #Ensure that tasks added under an user are still there after he/she
        #logs out and logs in again
        def test_task_belongs_to_right_user_after_relogin(self):
            with self.client:
                username = "Test User"
                password = "password"
                log = self.insert_user(username, password)
                log =  self.client.post(
                    '/login',
                    data=dict(username=username, password=password),
                    follow_redirects=True
                )
                self.insert_task_types()
                response = self.client.post('/addTodoTask', data=dict(todoitem='add To Do Task'),follow_redirects=True)
                logout = self.client.get('/logout',follow_redirects=True)
                username = "Another User"
                password = "password"
                log = self.insert_user(username, password)
                log =  self.client.post(
                    '/login',
                    data=dict(username=username, password=password),
                    follow_redirects=True
                )
                log =  self.client.post(
                    '/login',
                    data=dict(username="Test User", password=password),
                    follow_redirects=True
                )
                todo = kanban.Todo.query.filter(kanban.TodoType.type=="todo").filter(kanban.Todo.text=="add To Do Task").filter(kanban.Todo.userid==current_user.get_id()).first()
                self.assertTrue(todo.text=="add To Do Task")

    #Tests if tasks are deleted
    def test_delete_task(self):
        with self.client:
            username = "Test User"
            password = "password"
            log = self.insert_user(username, password)
            log =  self.client.post(
                '/login',
                data=dict(username=username, password=password),
                follow_redirects=True
            )
            self.insert_task_types()
            response = self.client.post('/addTodoTask', data=dict(todoitem='add To Do Task'),follow_redirects=True)
            todo = kanban.Todo.query.filter(kanban.TodoType.type=="todo").filter(kanban.Todo.text=="add To Do Task").filter(kanban.Todo.userid==current_user.get_id()).first()
            delete = self.client.post('/todo', data=dict(todotask=todo.id,button='Delete task'))
            todo = kanban.Todo.query.filter(kanban.TodoType.type=="todo").filter(kanban.Todo.text=="add To Do Task").filter(kanban.Todo.userid==current_user.get_id()).first()
            self.assertTrue(todo==None)

        #Tests if tasks move to the next stage when requested
        def test_move_todo_task_to_next_stage(self):
            with self.client:
                username = "Test User"
                password = "password"
                log = self.insert_user(username, password)
                log =  self.client.post(
                    '/login',
                    data=dict(username=username, password=password),
                    follow_redirects=True
                )
                self.insert_task_types()
                response = self.client.post('/addTodoTask', data=dict(todoitem='add To Do Task'),follow_redirects=True)
                todo = kanban.Todo.query.filter(kanban.TodoType.type=="todo").filter(kanban.Todo.text=="add To Do Task").filter(kanban.Todo.userid==current_user.get_id()).first()
                delete = self.client.post('/todo', data=dict(todotask=todo.id,button='Move task to next stage'))
                todo = kanban.Todo.query.filter(kanban.TodoType.type=="todo").filter(kanban.Todo.text=="add To Do Task").filter(kanban.Todo.userid==current_user.get_id()).first()
                #Type = 2 indicated that the type of the task is "doing"
                self.assertTrue(todo.type==2)

            def test_move_doing_task_to_next_stage(self):
                with self.client:
                    username = "Test User"
                    password = "password"
                    log = self.insert_user(username, password)
                    log =  self.client.post(
                        '/login',
                        data=dict(username=username, password=password),
                        follow_redirects=True
                    )
                    self.insert_task_types()
                    response = self.client.post('/addDoingTask', data=dict(todoitem='add Doing Task'),follow_redirects=True)
                    todo = kanban.Todo.query.filter(kanban.TodoType.type=="doing").filter(kanban.Todo.text=="add Doing Task").filter(kanban.Todo.userid==current_user.get_id()).first()
                    delete = self.client.post('/todo', data=dict(todotask=todo.id,button='Move task to next stage'))
                    todo = kanban.Todo.query.filter(kanban.TodoType.type=="done").filter(kanban.Todo.text=="add Doing Task").filter(kanban.Todo.userid==current_user.get_id()).first()
                    #Type = 3 indicated that the type of the task is "done"
                    self.assertTrue(todo.type==3)

if __name__ == '__main__':
    unittest.main()

# coding=UTF-8

import codecs
import json
import os
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from binascii import hexlify
from tornado.options import define, options
import csv

import torndb

import ticket

define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="database host")
define("mysql_database", default="ali_db", help="database name")
define("mysql_user", default="ali", help="database user")
define("mysql_password", default="p", help="database password")


class MyCodes:

    def __init__(self):
        pass

    NotAllowed = 600
    NotFound = 404
    OK = 200
    duplicate = 303
    Ok_but_done_before = 201
    Already_done = 202
    Wrong_pass = 100
    Wrong_user_pass = 105
    Wrong_token = 106
    Access_Denied = 700


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", Help),
            # (r"/",tornado.web.StaticFileHandler, {"path": ".", "default_filename": "index.html"}),
            (r"/signup", Signup),
            (r"/login", Login),
            (r"/logout", Logout),
            (r"/sendticket", SendTicket),
            (r"/getticketcli", GetTicketcli),
            (r"/closeticket", CloseTicket),
            (r"/getticketmod", GetTicketmod),
            (r"/restoticketmod", ResToTicketmod),
            (r"/changestatus", ChangeStatus),
            (r"/changerole", ChangeRole),
            (r"/show", ShowUsers),
            (r"/showT", ShowTickets),
            (r"/renumberate", ReNumberate),
            (r".*", DefaultHandler),
        ]
        settings = dict()
        super(Application, self).__init__(handlers, **settings)
        self.db = torndb.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)


class BaseHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @property
    def db(self):
        return self.application.db


class Help(BaseHandler):
    def get(self):
        f = codecs.open("/home/ali/PycharmProjects/project/methods.html", "r","utf-8")


        #text = "سلام"
        text=f.read()
        #self.write(text.decode("utf-8"))
        self.write(text)
        # self.write("<title>hello!</title><body><center><h1>hello</h1><table border=\"1\"><tr><td>row1,cel1<td><td>row1,cel2<td><tr><tr><td>row1,cel1<td><td>row1,cel1<td></tr></table></center></body>")
        # f = codecs.open("/home/ali/PycharmProjects/project/index.html", "r", 'utf-8')
        # f=open("/home/ali/PycharmProjects/project/index.html", "r")
        # self.render("/home/ali/PycharmProjects/project/" + "index2.html", aString="utf-8", )
    # f.encoding="utf-8"
    # a = f.read()
    # self.write(a)


class ShowUsers(BaseHandler):
    def get(self):
        my_db = self.db.query("SELECT username,firstname,lastname,role,ID FROM users")
        max = list(my_db).__len__()
        out = {
            "num": max,
            "users": my_db
        }
        self.write(json.dumps(out))


class ShowTickets(BaseHandler):
    def get(self):
        my_db = self.db.query("SELECT * FROM tickets")
        self.write(json.dumps(my_db))


class Logout(BaseHandler):
    def do_job(self, user_name, password):
        my_db = self.db.get(
            "SELECT * FROM users WHERE username LIKE %s AND password LIKE %s", user_name, password)
        # out_put=json.dumps({})
        out_put = {
            "message": "!",
            "code": 1
        }
        if my_db is None:
            out_put["message"] = "Username or Password is wrong"
            out_put["code"] = MyCodes.Wrong_user_pass
        else:
            if my_db["token"] == "0" or my_db["token"] == 0:
                out_put["message"] = "Already logged out"
                out_put["code"] = MyCodes.Already_done
            else:

                self.db.execute("UPDATE users SET token='0' WHERE username LIKE %s", user_name)
                out_put["message"] = "Logged Out Successfully"
                out_put["code"] = MyCodes.OK

        out_put_json = json.dumps(out_put)
        self.write(out_put_json)

    def post(self, *args, **kwargs):
        user_name = self.get_argument("username")
        password = self.get_argument("password")
        Logout.do_job(self, user_name, password)

    def get(self):
        user_name = self.get_argument("username")
        password = self.get_argument("password")
        Logout.do_job(self, user_name, password)


class SendTicket(BaseHandler):
    def do_job(self, token, new_ticket):
        my_db = self.db.get("SELECT * FROM users WHERE token LIKE '%s'" % token)

        out_put = {
            "message": "!",
            "code": 1,
            "id": 0
        }
        if (my_db is None) or token == "0" or token == 0:
            out_put["message"] = "Incorrect Token"
            out_put["code"] = MyCodes.Wrong_token
        else:
            username = my_db["username"]
            id = new_ticket.add_to_db(self.db, username)
            out_put["message"] = "Ticket Sent Successfully"
            out_put["code"] = MyCodes.OK
            out_put["id"] = id
        out_put_json = json.dumps(out_put)
        self.write(out_put_json)

    def post(self, *args, **kwargs):
        token = self.get_argument("token")
        new_ticket = ticket.Ticket()
        new_ticket.subject = self.get_argument("subject")
        new_ticket.body = self.get_argument("body")
        new_ticket.Status = ticket.Ticket.Open
        SendTicket.do_job(self, token, new_ticket)

    def get(self):
        token = self.get_argument("token")
        new_ticket = ticket.Ticket()
        new_ticket.subject = self.get_argument("subject")
        new_ticket.body = self.get_argument("body")
        new_ticket.Status = ticket.Ticket.Open
        SendTicket.do_job(self, token, new_ticket)


class GetTicketcli(BaseHandler):
    def get(self):
        token = self.get_argument("token")
        my_db = self.db.get("SELECT * FROM users WHERE token LIKE '%s'" % token)
        if (my_db is None) or token == "0" or token == 0:
            out_put = {}
            out_put["message"] = "Incorrect Token"
            out_put["code"] = MyCodes.Wrong_token
            self.write(json.dumps(out_put))
        else:
            username = my_db["username"]
            listOfTickets = ticket.Ticket.getAll_user(self.db, username)
            self.write(listOfTickets)


class CloseTicket(BaseHandler):
    def do_job(self, token, id):
        my_db = self.db.get("SELECT * FROM users WHERE token LIKE '%s'" % token)
        out_put = {
            "message": "!",
            "code": 1
        }
        if (my_db is None) or token == "0" or token == 0:
            out_put["message"] = "Incorrect Token"
            out_put["code"] = MyCodes.Wrong_token
        else:
            username = my_db["username"]
            role = my_db["role"]
            choosenTicket = self.db.get("SELECT * FROM tickets WHERE ID LIKE " + str(id))
            if (choosenTicket["username"] != username) and role != "A":
                out_put["message"] = "Access Denied"
                out_put["code"] = MyCodes.Access_Denied
            else:
                self.db.execute("UPDATE tickets SET Status=" + str(ticket.Ticket.Close) +
                                " WHERE ID LIKE " + str(id))

                out_put["message"] = "Ticket With id -" + str(id) + "- Closed Successfully"
                out_put["code"] = MyCodes.OK
        out_put_json = json.dumps(out_put)
        self.write(out_put_json)

    def post(self, *args, **kwargs):
        token = self.get_argument("token")
        id = self.get_argument("id")
        CloseTicket.do_job(self, token, id)

    def get(self):
        token = self.get_argument("token")
        id = self.get_argument("id")
        CloseTicket.do_job(self, token, id)


class GetTicketmod(BaseHandler):
    def get(self):
        token = self.get_argument("token")
        my_db = self.db.get("SELECT * FROM users WHERE token LIKE '%s'" % token)
        if (my_db is None) or token == "0" or token == 0:
            out_put = {}
            out_put["message"] = "Incorrect Token"
            out_put["code"] = MyCodes.Wrong_token
            self.write(json.dumps(out_put))
        else:
            # username = my_db["username"]
            if my_db["role"] != "A":
                out_put = {}
                out_put["message"] = "Access Denied you are not admin!"
                out_put["code"] = MyCodes.Access_Denied
                self.write(json.dumps(out_put))
            else:
                listOfTickets = ticket.Ticket.getAll_admin(self.db)
                self.write(listOfTickets)


class ResToTicketmod(BaseHandler):

    def do_job(self, token, id, body):
        my_db = self.db.get("SELECT * FROM users WHERE token LIKE '%s'" % token)

        out_put = {
            "message": "!",
            "code": 1
        }
        if (my_db is None) or token == "0" or token == 0:
            out_put["message"] = "Incorrect Token"
            out_put["code"] = MyCodes.Wrong_token
        elif my_db["role"] != "A":
            out_put["message"] = "Access Denied you are not admin!"
            out_put["code"] = MyCodes.Access_Denied
        else:
            self.db.execute("UPDATE tickets SET Status=" + str(ticket.Ticket.Close)
                            + ",response='" + body + "' WHERE ID LIKE " + id)
            out_put["message"] = "Response to Ticket With id -" + str(id) + "- Sent Successfully"
            out_put["code"] = MyCodes.OK
        self.write(json.dumps(out_put))

    def post(self, *args, **kwargs):
        token = self.get_argument("token")
        id = str(self.get_argument("id"))
        body = self.get_argument("body")
        ResToTicketmod.do_job(self, token, id, body)

    def get(self):
        token = self.get_argument("token")
        id = str(self.get_argument("id"))
        body = self.get_argument("body")
        ResToTicketmod.do_job(self, token, id, body)


class ChangeStatus(BaseHandler):
    def do_job(self, token, id, status):
        status = ticket.Ticket.parse_status(status)
        my_db = self.db.get("SELECT * FROM users WHERE token LIKE '%s'" % token)
        out_put = {
            "message": "!",
            "code": 1
        }
        if (my_db is None) or token == "0" or token == 0:
            out_put["message"] = "Incorrect Token"
            out_put["code"] = MyCodes.Wrong_token

        else:
            if my_db["role"] != "A":
                out_put["message"] = "Access Denied you are not admin!"
                out_put["code"] = MyCodes.Access_Denied
            else:
                self.db.execute("UPDATE tickets SET Status=" + str(status)
                                + " WHERE ID LIKE " + id)
                out_put["message"] = "Status Ticket With id -" + str(id) + "- Changed Successfully"
                out_put["code"] = MyCodes.OK
        self.write(json.dumps(out_put))

    def post(self, *args, **kwargs):
        token = self.get_argument("token")
        id = self.get_argument("id")
        status = self.get_argument("status")
        ChangeStatus.do_job(self, token, id, status)

    def get(self):
        token = self.get_argument("token")
        id = self.get_argument("id")
        status = self.get_argument("status")
        ChangeStatus.do_job(self, token, id, status)


class Signup(BaseHandler):
    def do_job(self, user_name, password):
        try:
            firstname = self.get_argument("firstname")
        except:
            firstname = ""
        try:
            lastname = self.get_argument("lastname")
        except:
            lastname = ""

        my_db = self.db.get("SELECT * FROM users WHERE username LIKE '%s'" % user_name)

        out_put = {
            "message": "!",
            "code": 1
        }
        if my_db is not None:
            out_put["message"] = "The user seems to exist!"
            out_put["code"] = MyCodes.duplicate
        else:
            self.db.execute("INSERT INTO users(username,password,role,token,firstname,lastname) "
                            "VALUES(%s,%s,%s,%s,%s,%s)", user_name, password, 'U', '0', firstname, lastname)
            out_put["message"] = "Signed Up Successfully"
            out_put["code"] = MyCodes.OK
        out_put_json = json.dumps(out_put)
        self.write(out_put_json)

    def get(self):
        user_name = self.get_argument("username")
        password = self.get_argument("password")
        Signup.do_job(self, user_name, password)

    def post(self, *args, **kwargs):
        user_name = self.get_argument("username")
        password = self.get_argument("password")
        Signup.do_job(self, user_name, password)


class Login(BaseHandler):

    def do_job(self, user_name, password):
        my_db = self.db.get("SELECT * FROM users WHERE username LIKE '%s'" % user_name)

        out_put = {
            "message": "!",
            "code": 1,
            "token": 0
        }
        if my_db is None:
            out_put["message"] = "The user dosen't seem to exist!"
            out_put["code"] = MyCodes.OK
            out_put["token"] = "0"
        else:
            my_choosed_db = self.db.get("SELECT * FROM users WHERE username LIKE %s AND password LIKE %s", user_name,
                                        password)
            if my_choosed_db is None:
                out_put["message"] = "Wrong password"
                out_put["code"] = MyCodes.Wrong_pass
                out_put["token"] = "0"
            else:
                if my_choosed_db["token"] == 0 or my_choosed_db["token"] == "0":
                    go_on = True
                    while go_on:
                        rand_token = str(hexlify(os.urandom(16)))
                        # rand_num=random.randint(1e6,1e9)
                        search_db = self.db.get("SELECT token FROM users WHERE token LIKE %s", rand_token)
                        if search_db is None:
                            go_on = False
                    self.db.execute("UPDATE users SET token=%s WHERE username LIKE %s", rand_token, user_name)
                    out_put["message"] = "Logged in Successfully"
                    out_put["code"] = MyCodes.OK
                    out_put["token"] = rand_token
                else:
                    out_put["message"] = "Already Logged in"
                    out_put["code"] = MyCodes.Already_done

                    out_put["token"] = str(my_choosed_db["token"])
        out_put_json = json.dumps(out_put)
        self.write(out_put_json)

    def post(self, *args, **kwargs):
        user_name = self.get_argument("username")
        password = self.get_argument("password")
        Login.do_job(self, user_name, password)

    def get(self):
        user_name = self.get_argument("username")
        password = self.get_argument("password")
        Login.do_job(self, user_name, password)


class DefaultHandler(BaseHandler):
    def get(self):
        self.write("oops!! syntax error!!")


class ChangeRole(BaseHandler):
    def do_job(self, token, username, role):
        my_db = self.db.get("SELECT * FROM users WHERE token LIKE '%s'" % token)
        out_put = {
            "message": "!",
            "code": 1
        }
        if (my_db is None) or token == "0" or token == 0:
            out_put["message"] = "Incorrect Token"
            out_put["code"] = MyCodes.Wrong_token

        else:
            if my_db["role"] != "A":
                out_put["message"] = "Access Denied you are not admin!"
                out_put["code"] = MyCodes.Access_Denied
            elif username == "ali":
                out_put["message"] = "master user's role can not be changed!!"
                out_put["code"] = MyCodes.NotAllowed
            else:
                self.db.execute("UPDATE users SET role='" + role
                                + "' WHERE username LIKE '" + username + "'")
                out_put["message"] = "Role of user -" + username + "- is now: " + role
                out_put["code"] = MyCodes.OK
        self.write(json.dumps(out_put))

    def post(self, *args, **kwargs):
        token = self.get_argument("token")
        username = self.get_argument("username")
        role = self.get_argument("role")
        ChangeRole.do_job(self, token, username, role)

    def get(self):
        token = self.get_argument("token")
        username = self.get_argument("username")
        role = self.get_argument("role")
        ChangeRole.do_job(self, token, username, role)


class ReNumberate(BaseHandler):
    def do_job(self, token, password):
        my_db = self.db.get("SELECT * FROM users WHERE token LIKE '%s'" % token)
        out_put = {
            "message": "!",
            "code": 1
        }
        if (my_db is None) or token == "0" or token == 0:
            out_put["message"] = "Incorrect Token"
            out_put["code"] = MyCodes.Wrong_token
        elif my_db["role"] != "A":
            out_put["message"] = "Access Denied you are not admin!"
            out_put["code"] = MyCodes.Access_Denied
        elif my_db["password"] != password:
            out_put["message"] = "Entered password is incorrect"
            out_put["code"] = MyCodes.Wrong_pass
        else:
            self.db.execute("truncate table users")
            self.db.execute("truncate table tickets")
            self.db.execute("INSERT INTO users(username,password,role,token,firstname,lastname) "
                            "VALUES('ali','pass','A','0','ali','alaei')")  # for having at least one admin!
            out_put = {
                "message": "All done,every thing is erased exept for user ali!!",
                "code": MyCodes.OK
            }
        self.write(json.dumps(out_put))

    def post(self, *args, **kwargs):
        token = self.get_argument("token")
        password = self.get_argument("password")
        ReNumberate.do_job(self, token, password)

    def get(self):
        token = self.get_argument("token")
        password = self.get_argument("password")
        ReNumberate.do_job(self, token, password)


def main():
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

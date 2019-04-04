import torndb
import ticket
import os
#import random
import tornado.escape
import tornado.httpserver
import tornado.ioloop
from binascii import hexlify

import tornado.options
import tornado.web
import json
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="database host")
define("mysql_database", default="ali_db", help="database name")
define("mysql_user", default="ali", help="database user")
define("mysql_password", default="p", help="database password")


class MyCodes:

    def __init__(self):
        pass
    NotFound=404
    OK=200
    duplicate=303
    Ok_but_done_before=201
    Already_done=202
    Wrong_pass = 100
    Wrong_user_pass = 105
    Wrong_token =106


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/signup", Signup),
            (r"/login", Login),
            (r"/logout", Logout),
            (r"/sendticket", SendTicket),
            (r"/getticketcli", GetTicketcli),
            (r"/closeticket", CloseTicket),
            (r"/getticketmod", GetTicketmod),
            (r"/restoticketmod", ResToTicketmod),
            (r"/changestatus", ChangeStatus),
            (r"/show",ShowUsers),
            (r"/showT", ShowTickets),
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


class ShowUsers(BaseHandler):
    def get(self):
        my_db = self.db.query("SELECT * FROM users")
        self.write(json.dumps(my_db))


class ShowTickets(BaseHandler):
    def get(self):
        my_db = self.db.query("SELECT * FROM tickets")
        self.write(json.dumps(my_db))


class Logout(BaseHandler):
    def get(self):
        user_name = self.get_argument("username")
        password = self.get_argument("password")
        my_db = self.db.get(
            "SELECT * FROM users WHERE username LIKE %s AND password LIKE %s",user_name,password)
        # out_put=json.dumps({})
        out_put = {
            "message": "!",
            "code": 1,
            "result": json.dumps({})
        }
        if my_db is None:
            out_put["message"] = "Username or Password is wrong"
            out_put["code"] = MyCodes.Wrong_user_pass
            out_put["result"] = json.dumps({})
        else:
            out_put["result"] = my_db
            if my_db["token"] == "0" or my_db["token"]==0:
                out_put["message"] = "Already logged out"
                out_put["code"] = MyCodes.Already_done
            else:

                self.db.execute("UPDATE users SET token='0' WHERE username LIKE %s", user_name )
                out_put["message"] = "Logged Out Successfully"
                out_put["code"] = MyCodes.OK
                out_put["result"] = my_db

        out_put_json = json.dumps(out_put)
        self.write(out_put_json)


class SendTicket(BaseHandler):
    def get(self):
        token = self.get_argument("token")
        new_ticket=ticket.Ticket()
        new_ticket.subject=self.get_argument("subject")
        new_ticket.body=self.get_argument("body")
        new_ticket.Status=ticket.Ticket.Open
        my_db = self.db.get("SELECT * FROM users WHERE token LIKE '%s'" % token)

        out_put = {
            "message": "!",
            "code": 1,
            "result": json.dumps({}),
            "id": 0
        }
        if my_db is None:
            out_put["message"] = "Incorrect Token"
            out_put["code"] = MyCodes.Wrong_token
            out_put["result"] = my_db
        else:
            username=my_db["username"]
            id = new_ticket.add_to_db(self.db,username)
            out_put["message"] = "Ticket Sent Successfully"
            out_put["code"] = MyCodes.OK
            out_put["result"] = my_db
            out_put["id"] = id
        out_put_json = json.dumps(out_put)
        self.write(out_put_json)


class GetTicketcli(BaseHandler):
    def get(self):
        token = self.get_argument("token")
        my_db = self.db.get("SELECT * FROM users WHERE token LIKE '%s'" % token)
        if my_db is None:
            out_put = {}
            out_put["message"] = "Incorrect Token"
            out_put["code"] = MyCodes.Wrong_token
            out_put["result"] = my_db
            out_put["id"] = 0
            self.write(json.dumps(out_put))
        else:
            username = my_db["username"]
            listOfTickets=ticket.Ticket.getAll(self.db,username)
            self.write(listOfTickets)

class CloseTicket(BaseHandler):
    def get(self):
        pass


class GetTicketmod(BaseHandler):
    def get(self):
        pass


class ResToTicketmod(BaseHandler):
    def get(self):
        pass


class ChangeStatus(BaseHandler):
    def get(self):
        pass


class Signup(BaseHandler):
    def get(self):
        user_name = self.get_argument("username")
        password = self.get_argument("password")
        try:
            firstname = self.get_argument("firstname")
        except:
            firstname=""
        try:
            lastname = self.get_argument("lastname")
        except:
            lastname=""

        my_db=self.db.get("SELECT * FROM users WHERE username LIKE '%s'" % user_name)

        out_put ={
            "message" : "!",
            "code":1,
            "result":json.dumps({})
        }
        if my_db is not None:
            out_put["message"]="The user seems to exist!"
            out_put["code"] = MyCodes.duplicate
            out_put["result"]=my_db
        else:
            self.db.execute("INSERT INTO users(username,password,role,token,firstname,lastname) "
                            "VALUES(%s,%s,%s,%s,%s,%s)",user_name,password,'U','0',firstname,lastname)
            out_put["message"] = "Signed Up Successfully"
            out_put["code"] = MyCodes.OK
            out_put["result"] = my_db
        out_put_json = json.dumps(out_put)
        self.write(out_put_json)


class Login(BaseHandler):
    def get(self):
        user_name = self.get_argument("username")
        password = self.get_argument("password")
        my_db=self.db.get("SELECT * FROM users WHERE username LIKE '%s'" % user_name)

        out_put ={
            "message" : "!",
            "code":1,
            "result":json.dumps({}),
            "token":0
        }
        if my_db is None:
            out_put["message"]="The user dosen't seem to exist!"
            out_put["code"]=MyCodes.OK
            out_put["result"]=json.dumps({})
            out_put["token"]="0"
        else:
            my_choosed_db=self.db.get("SELECT * FROM users WHERE username LIKE %s AND password LIKE %s",user_name,password)
            if my_choosed_db is None:
                out_put["message"] = "Wrong password"
                out_put["code"] = MyCodes.Wrong_pass
                out_put["result"] = json.dumps({})
                out_put["token"] = "0"
            else:
                if my_choosed_db["token"]==0 or my_choosed_db["token"]=="0":
                    go_on=True
                    while go_on:
                        rand_token = str(hexlify(os.urandom(16)))
                        #rand_num=random.randint(1e6,1e9)
                        search_db=self.db.get("SELECT token FROM users WHERE token LIKE %s", rand_token)
                        if search_db is None:
                            go_on=False
                    self.db.execute("UPDATE users SET token=%s WHERE username LIKE %s",rand_token,user_name)
                    out_put["message"] = "Logged in Successfully"
                    out_put["code"] = MyCodes.OK
                    out_put["result"] = my_choosed_db
                    out_put["token"] = rand_token
                else:
                    out_put["message"] = "Already Logged in"
                    out_put["code"] = MyCodes.Already_done
                    out_put["result"] = my_choosed_db

                    out_put["token"] = str(my_choosed_db["token"])
        out_put_json=json.dumps(out_put)
        self.write(out_put_json)


class DefaultHandler(BaseHandler):
    def get(self):
        self.write("opps!! syntax error!!")


def main():
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

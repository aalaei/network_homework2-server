import torndb
import random
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import json
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="database host")
define("mysql_database", default="ali_db", help="database name")
define("mysql_user", default="ali", help="database user")
define("mysql_password", default="p", help="database password")


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


class Logout(BaseHandler):
    def get(self):
        user_name = self.get_argument("username")
        password = self.get_argument("password")
        my_db = self.db.get(
            "SELECT * FROM users WHERE username LIKE '" + user_name + "' AND password LIKE '" + password + "'")
        # out_put=json.dumps({})
        out_put = {
            "message": "!",
            "code": 1,
            "result": json.dumps({})
        }
        if my_db is None:
            out_put["message"] = "Username or Password is wrong"
            out_put["code"] = 404
            out_put["result"] = json.dumps({})
        else:
            out_put["result"] = my_db
            if my_db["token"]=="0" or my_db["token"]==0:
                out_put["message"] = "Already logged out"
                out_put["code"] = "201"
            else:
                my_db_str="UPDATE users SET token=" + str(0) + " WHERE username LIKE '" + user_name + "'"
                print(my_db_str)
                self.db.execute(my_db_str)
                out_put["message"] = "Logged Out Successfully"
                out_put["code"] = "200"
                out_put["result"] = my_db

        out_put_json = json.dumps(out_put)
        self.write(out_put_json)


class SendTicket(BaseHandler):
    def get(self):
        pass


class GetTicketcli(BaseHandler):
    def get(self):
        pass


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
            out_put["code"] = 303
            out_put["result"]=my_db
        else:
            self.db.execute("INSERT INTO users(username,password,role,token,firstname,lastname) VALUES('"+user_name+"','"+password+"','U',0,'"+firstname+"','"+lastname+"')")
            out_put["message"] = "Signed Up Successfully"
            out_put["code"] = "200"
            out_put["result"] = my_db
        out_put_json=json.dumps(out_put)
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
            out_put["code"]=404
            out_put["result"]=json.dumps({})
            out_put["token"]=0
        else:
            my_choosed_db=self.db.get("SELECT * FROM users WHERE username LIKE '" +user_name + "' AND password LIKE '"+ password +"'")
            if my_choosed_db is None:
                out_put["message"] = "Worng password"
                out_put["code"] = "100"
                out_put["result"] = json.dumps({})
                out_put["token"] = "0"
            else:
                if my_choosed_db["token"]==0 or my_choosed_db["token"]=="0":
                    go_on=True
                    while go_on:
                        rand_num=random.randint(1e6,1e9)
                        search_db=self.db.get("SELECT token FROM users WHERE token LIKE " + str(rand_num))
                        if search_db is None:
                            go_on=False
                    self.db.execute("UPDATE users SET token="+str(rand_num)+" WHERE username LIKE '"+user_name+"'")
                    out_put["message"] = "Logged in Successfully"
                    out_put["code"] = "200"
                    out_put["result"] = my_choosed_db
                    out_put["token"] = str(rand_num)
                else:
                    out_put["message"] = "Already Logged in"
                    out_put["code"] = "303"
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
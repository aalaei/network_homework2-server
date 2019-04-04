import json


class Ticket:

    Open = 0
    Under_review = 1
    Close = 2

    @staticmethod
    def getAll(db,username):
        my_db=db.query("SELECT subject,body,Status,id,date FROM tickets WHERE username LIKE %s ORDER BY ID",username)
        size="There Are -"+str(len(my_db))+"- Ticket"
        my_dic = {
            "tickets": size,
            "code": 200,
        }
        i=0
        while i<len(my_db):
            my_dic['block ' + str(i)]= my_db[i]
            #my_dic.update({'block ' + str(i) : my_db[i]})
            i = i+1
            myjs=json.dumps(my_dic)
        return (myjs)
        #ouf=json.dumps(my_dic,)

    def __init__(self):
        body = ""
        subject=""
        Status = 0

    def add_to_db(self, db, username):
        mystr="INSERT INTO tickets(username,subject,body,Status,date) VALUES('" \
              + username + "','" + self.subject + "','" + self.body + "',"+str(self.Status)+", now()) "
        print (mystr)
        db.execute(mystr)
        my_choosen=db.get("SELECT ID FROM tickets ORDER BY ID DESC LIMIT 1")
        return my_choosen["ID"]
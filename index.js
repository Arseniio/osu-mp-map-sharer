//
// Written on Node v13.14.0
//

const net = require('net')

const host = '192.168.0.106' //launch ip
// const host = 'localhost' //for testing on one computer
const port = '5051'

function replaceAll(str, find, replace) {
    return str.replace(new RegExp(find, 'g'), replace);
}

var rooms = [] //have some room object's

class user {
    constructor(username, oldmd5, md5, usersocket) {
        this.username = username
        this.md5 = md5
        this.oldmd5 = oldmd5
        this.usersocket = usersocket
    }
}
class room {
    constructor(md5) {
        this.md5 = md5
        this.oldmd5 = md5
        this.users = [] //array of user objects
        console.log("created new room with md5: ", this.md5)
    }
    AddUser(newuser) {
            for (var b = 0; b < this.users.length; b++) {
                if (newuser.username == this.users[b].username) {
                    console.log(`changing ${this.md5} to ${newuser.md5}`)
                    this.sendnewhash(newuser.md5)
                    console.log(rooms) //added
                    return this.md5
                }
            }
        this.users.push(newuser)
        console.log(rooms) // added
        return this.md5
    }

    deleteuser(username) {
        for (var i = 0; i < this.users.length; i++) {
            if (username == this.users[i].username) {
                //i is deleted user index
                console.log(username + " deleted")
                this.users.splice(i, 1);
            }
        }
    }

    sendnewhash(newhash) {
        console.log('sending new hash', newhash)
        this.oldmd5 = this.md5
        this.md5 = newhash
        for (var i = 0; i < this.users.length; i++) this.users[i].usersocket.write(Buffer.from(`New Hash:${newhash}`))
        //TODO add exeption to not sending map to same player
    }

    sendmaptoothers(sender, md5name) {
        console.log('sending map to other users')
        console.log(sender)
        for (var i = 0; i < this.users.length; i++) {
            if (this.users[i].username != sender) {
                this.users[i].usersocket.write(Buffer.from('m' + md5name))
            }
        }
    }
}

function findroomforuser(data, socket) {
    console.log(data)
    json_data = JSON.parse(data)
    let newuser = new user(json_data["username"], json_data["oldmd5"], json_data["md5"], socket);
    // console.log(json_data["username"], json_data["oldmd5"], json_data["md5"])
    if (rooms.length != 0) {
        for (var i = 0; i < rooms.length; i++) {
            for (var j = 0; j < rooms[i].users.length; j++) {
                if (newuser.username != rooms[i].users[j].username && newuser.md5 == rooms[i].md5) {
                    console.log("newuser found its room with same md5") //UNSAFE
                    for (let i = 0; i < rooms.length; i++) {
                        for (let j = 0; j < rooms[i].users.length; j++) {
                            if (newuser.username == rooms[i].users[j].username) {
                                rooms[i].deleteuser(newuser.username)
                            }
                        }
                    }
                    rooms[i].AddUser(newuser)
                    return
                }
                else if (newuser.oldmd5 == "") {
                    console.log('oldmd5 == ""')
                    var a = rooms.push(new room(newuser.md5))
                    rooms[a - 1].AddUser(newuser)
                    return
                }
            }
        }
        for (var i = 0; i < rooms.length; i++) {
            for (var j = 0; j < rooms[i].users.length; j++) {
                if (newuser.username == rooms[i].users[j].username) {
                    console.log("user reconnected")
                    rooms[i].AddUser(newuser)
                }
                else if (newuser.md5 == rooms[i].md5) {
                    console.log("assign user to room", rooms[i].md5)
                    rooms[i].AddUser(newuser)
                }
            }
        }
    }
    else {  //if no rooms at all create new one
        rooms.push(new room(newuser.md5))
        rooms[0].AddUser(newuser)
    }
    // console.log(rooms) moved to rooms.adduser()
    return
}

const ConnListener = (socket) => {
    var data = ""
    const userip = socket.remoteAddress;
    const userport = socket.remotePort;
    console.log(`user connected(RL): ${userip}:${userport}`)
    socket.on('data', chunk => {
        data = chunk.toString('utf-8');
        data = replaceAll(data, "'", '"')
        switch (data.startsWith("{")) {
            case true:
                findroomforuser(data, socket)
                break;  
            case false:
                var senderinfo = data.split(":");
                console.log(senderinfo)
                for (var i = 0; i < rooms.length; i++) {
                    if (rooms[i].md5 == senderinfo[2]) {
                        rooms[i].sendmaptoothers(senderinfo[1], senderinfo[2])
                    }
                }
                break;
        }
    })
}


const server = net.createServer(ConnListener)
server.listen(port, host, () => {
    console.log(`server running on http://${host}:${port}`)
})

server.on('error', (err) => {
    console.log(err)
}
)

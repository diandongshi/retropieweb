#  -*- coding:utf-8 -*-

import web
import math
import urllib
import json
import os
import codecs
import xml.dom.minidom

apiUrl = 'http://client.vgabc.com/clientapi/'
romUrl = 'http://211.91.140.177/rom/fc/'
imgUrl = 'http://img.vgabc.com'

allGame = 0

romDir = '/home/pi/RetroPie/roms/nes/'
imgDir = '/home/pi/RetroPie/roms/nes/'

cfgXml = '/opt/retropie/configs/all/emulationstation/gamelists/nes/gamelist.xml'

def getGameList(page, pageSize):
    global allGame
    data = urllib.urlencode({'model': 'appstore', 'action': 'gamelist', 'clientparams': ' | |zh| | |pc1.0', 'page': page, 'pagesize': pageSize, 'categoryid': '', 'emulatorid': '125', 'orderby': 'recommend', '': 'language'}).encode('utf-8')
    list = json.loads(urllib.urlopen(apiUrl, data).read())
    if allGame <= 0:
        allGame = int(list['count'])
    return list

def getGameInfo(gameId):
    data = urllib.urlencode({'model': 'appstore', 'action': 'gameinfo', 'clientparams': ' | |zh| | |pc1.0', 'gameid': gameId}).encode('utf-8')
    return json.loads(urllib.urlopen(apiUrl, data).read())

def chrLen(chr):
    try:
        ln = len(chr.encode('gbk'))
    except Exception:
        print(chr)
        ln = 2
    return ln

def desFmt(src):
    des = ''
    ln = 0
    for chr in src:
        if chr == '\n':
            ln = 0
            des += chr
        else:
            l = chrLen(chr)
            if ln + l > 60:
                des += '\n'
                ln = l
                des += chr
            else:
                ln += l
                des += chr
    return des

def xmlFmt(src):
    des = ''
    for chr in src:
        if chr == '<':
            des += '&lt;'
        elif chr == '>':
            des += '&gt;'
        elif chr == '&':
            des += '&amp;'
        else:
            des += chr
    return des

def setPrp(doc, game, prop, value):
    if game.getElementsByTagName(prop):
        for dom in game.getElementsByTagName(prop):
            game.removeChild(dom)
    dom = doc.createElement(prop)
    dom.appendChild(doc.createTextNode(value))
    game.appendChild(dom)
    game.appendChild(doc.createTextNode('\n'))

def savGame2Pie(gameInfo, image):
    try:
        screen = gameInfo['icon']
        if image:
            screen = gameInfo['screens'][int(image)]
        (imgPath, imgFile) = os.path.split(screen)
        (imgName, imgType) = os.path.splitext(imgFile.split('!')[0])
        urllib.urlretrieve((romUrl + gameInfo['gameid'] + '.zip'), (romDir + gameInfo['gameid'] + '.zip'))
        urllib.urlretrieve((imgUrl + screen), (imgDir + gameInfo['gameid'] + imgType))
        if not os.path.exists(cfgXml):
            f = codecs.open(cfgXml, 'w', 'utf-8')
            f.write('<?xml version="1.0"?>\n')
            f.write('<gameList>\n')
            f.write('</gameList>\n')
            f.close()
        doc = xml.dom.minidom.parse(cfgXml)
        gameList = doc.documentElement
        games = gameList.getElementsByTagName('game')
        thisGame = None
        for game in games:
            if game.getElementsByTagName('developer') \
                and game.getElementsByTagName('developer')[0].childNodes \
                and game.getElementsByTagName('developer')[0].childNodes[0].nodeValue == gameInfo['gameid']:
                thisGame = game
                break
        if not thisGame:
            thisGame = doc.createElement('game')
            gameList.appendChild(thisGame)
        setPrp(doc, thisGame, 'path', ('./' + gameInfo['gameid'] + '.zip'))
        setPrp(doc, thisGame, 'name', gameInfo['gamename'])
        setPrp(doc, thisGame, 'desc', gameInfo['description'])
        setPrp(doc, thisGame, 'image', ('./' + gameInfo['gameid'] + imgType))
        setPrp(doc, thisGame, 'releasedate', ('%sT000000'%(gameInfo['start_sell_time'][0:4] + gameInfo['start_sell_time'][5:7] + gameInfo['start_sell_time'][8:10])))
        setPrp(doc, thisGame, 'developer', gameInfo['gameid'])
        setPrp(doc, thisGame, 'publisher', gameInfo['orgname'])
        setPrp(doc, thisGame, 'rating', ('%.1f'%((round((float)(gameInfo['rating'])/5, 1)))))
        f = codecs.open(cfgXml, 'w', 'utf-8')
        doc.writexml(f)
        f.close()
        return 1
    except Exception as e:
        return 0

def delGame2Pie(gameId):
    try:
        os.system('rm -f ' + romDir + gameId + '.*')
        os.system('rm -f ' + imgDir + gameId + '.*')
        if os.path.exists(cfgXml):
            doc = xml.dom.minidom.parse(cfgXml)
            gameList = doc.documentElement
            games = gameList.getElementsByTagName('game')
            thisGame = None
            for game in games:
                if game.getElementsByTagName('developer') \
                    and game.getElementsByTagName('developer')[0].childNodes \
                    and game.getElementsByTagName('developer')[0].childNodes[0].nodeValue == gameId:
                    thisGame = game
                    break
            if thisGame:
                gameList.removeChild(thisGame)
            f = codecs.open(cfgXml, 'w', 'utf-8')
            doc.writexml(f)
            f.close()
        return 1
    except Exception as e:
        return 0

render = web.template.render('templates', globals = {'math': math, 'os': os, 'apiUrl': apiUrl, 'romUrl': romUrl, 'imgUrl': imgUrl, 'romDir': romDir, 'imgDir': imgDir})

urls = (
    '/', 'index',
    '/controller', 'controller',
    '/xiaoji', 'xiaoji'
)

class index:
    def GET(self): 
        return render.index()

class controller:
    def GET(self):  
        return render.controller()

class xiaoji:
    def GET(self):
        data = web.input(type = 'gameList', page = 1, pageSize = 40, gameId = None, image = None)
        if data.type == 'gameList':
            gameList = getGameList(data.page, data.pageSize)
            return render.xiaoji(data.type, allGame, int(data.page), int(data.pageSize), gameList, None, None)
        elif data.type == 'gameInfo':
            gameInfo = getGameInfo(data.gameId)
            return render.xiaoji(data.type, None, None, None, None, data.gameId, gameInfo)
        elif data.type == 'gameSave':
            gameInfo = getGameInfo(data.gameId)['gameinfo']
            gameInfo['gamename'] = xmlFmt(gameInfo['gamename'])
            gameInfo['description'] = xmlFmt(desFmt(gameInfo['description']))
            if savGame2Pie(gameInfo, data.image) == 1:
                return '安装成功'
            else:
                return '安装失败'
        elif data.type == 'gameDelt':
            if delGame2Pie(data.gameId) == 1:
                return '删除成功'
            else:
                return '删除失败'

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()

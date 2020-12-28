# -*- coding: utf-8 -*-
import redis
import os
import json
import cherrypy
import cherrypy_cors
import requests
from geojson import Point

MAP_API_URL = 'http://127.0.0.1/openlayers_tracker/api/v1/map_api/tracker'
PORT = 8004
myip = '0.0.0.0'


class RedisInstance(object):
    def __init__(self):
        self.r = redis.Redis()

    def flushall(self):
        return self.r.flushall()

    def add_item(self, lng, lat, imei):
        return self.r.execute_command('GEOADD', 'bikes', lng, lat,
                                      "imei:{}".format(imei, ))

    def search_item(self, imei):
        # print(imei)
        return self.r.execute_command('GEOPOS', 'bikes',
                                      "imei:{}".format(imei, ))

    def search_all(self, formatted=False):
        imei_coors_dict = {}
        geojson_formatted = []
        keys = self.r.keys('bikes')
        for key in keys:
            if key and self.r.type(key) == b'zset':
                for v in self.r.zrange(key, 0, -1):
                    for c in self.search_item(str(v[5:], 'utf-8')):
                        imei_coors_dict[str(v[5:], 'utf-8')] = c
                        # print((Point(list(c),
                        #              properties={"imei": str(v[5:],
                        #                                      'utf-8')})))
                        geojson_formatted.append(
                            Point(list(c),
                                  properties={"imei": str(v[5:], 'utf-8')}))
        if formatted == 'true':
            return geojson_formatted
        else:
            return imei_coors_dict
        # GEORADIUS bikes 8.98207819999998 38.7584682000001 22000 km WITHCOORD
        # self.r.execute_command('GEORADIUS', 'bikes', "8.98207819999998", "38.7584682000001", "22000",
        # "km", "WITHCOORD")

    def remove_items(self, imei):
        return self.r.execute_command('ZREM', 'bikes',
                                      "imei:{}".format(imei, ))

    def close_conn(self):
        pass


class MainStart(object):
    def __init__(self):
        self.redis_instance = RedisInstance()
        # redis_instance.flushall()

    @cherrypy.expose
    def index(self):
        pass

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def add_item(self, lng, lat, imei, speed, angle):
        lng = lng[:2] + '.' + lng[2:]
        lat = lat[:1] + '.' + lat[1:]
        result = self.redis_instance.add_item(lng, lat, imei)
        try:
            # send to the map api for persistence
            r = requests.post(
                url=MAP_API_URL,
                data={
                    'coordinate': lat+','+lng,
                    'imei': imei,
                    'speed': speed,
                    'angle': angle
                })
            if not r.json()['status']:
                print(r.content)
            else:
                print(r.json()['message'])

        except Exception as e:
            print(e)
            pass

        return {"status": bool(result)}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_all(self, formatted=False):
        return self.redis_instance.search_all(formatted)


if __name__ == '__main__':
    from cherrypy.process.plugins import Daemonizer
    d = Daemonizer(cherrypy.engine)
    # d.subscribe()

    conf = {
        '/': {
            'tools.sessions.on': True,
        },
        '/static': {},
    }

    cherrypy_cors.install()

    cherrypy.config.update({
        'server.socket_host': myip,
        'server.socket_port': PORT,
        'server.max_request_body_size': 0,
        'server.socket_timeout': 60,
        'cors.expose.on': True,
    })

    webapp = MainStart()

    cherrypy.quickstart(webapp, '/', conf)

# redis_instance = RedisInstance()
# redis_instance.flushall()

# add items/keys
# redis_instance.add_item(landmark_names)

# search for items
# redis_instance.search_item('1', '001')
# redis_instance.search_item('2', '001')
# redis_instance.search_item('3', '001')

# redis_instance.search_all()
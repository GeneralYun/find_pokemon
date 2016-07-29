import scrapy
from scrapy.http import Request
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
import json
import sets
import datetime

class pokemonFind_crawler(scrapy.Spider):
    name='pokemonFind'
    pokefil = sets.Set()
    id_record = sets.Set()
    regions = {}    
    api_url = 'https://pokevision.com/map/data/%f/%f'
    download_delay = 0.1
    former_longitude = 0
    former_latitude = 0
    stepSize = 0.008

    def __init__(self, *a, **kw):
        dispatcher.connect(self.spider_idle, signals.spider_idle)
        with open('filter','r') as f:
            pokeid = f.readline().strip()
            while pokeid:
                self.pokefil.add(int(pokeid))
                pokeid = f.readline().strip()
        with open('search_region.json', 'r') as f:
            self.regions = json.loads(f.read())

    def frange(self,x, y, jump):
        while x < y:
            yield x
            x += jump

    def start_requests(self):
        yield Request(self.api_url%(37.8089603,-122.4104494), callback = self.search_regions)

    def search_regions(self, response):
        status = json.loads(response.body)['status']
        if status != 'success':
            print "BAD RESPONSE!!!"
            return
        for region in self.regions:
            N = region['coordinate'][0]
            S = region['coordinate'][1]
            W = region['coordinate'][2]
            E = region['coordinate'][3]
            for y in self.frange(S,N,self.stepSize):
                for x in self.frange(W, E, self.stepSize):
                    yield Request(self.api_url%(y, x), meta={'city':region['city']},callback=self.print_pokemon_position, dont_filter = True)


    def print_pokemon_position(self, response):
        pos = json.loads(response.body)
        if pos['status'] == 'success':
            for pokemon in pos['pokemon']:
                if  pokemon['pokemonId'] in self.pokefil and pokemon['id'] not in self.id_record:
                    if self.former_latitude == pokemon['latitude'] and self.former_longitude == pokemon['longitude']:
                        return
                    self.former_latitude = pokemon['latitude']
                    self.former_longitude = pokemon['longitude']
                    exptime = datetime.datetime.fromtimestamp(pokemon['expiration_time'])
                    self.id_record.add(pokemon['id'])
                    with open('result', 'a') as f:
                        f.write('Pokemon: {0:>3}, Coordinate: <wpt lat="{1:f}" lon="{2:<f}">, Expired time: {3}, city:{4:<13}\n'
                            .format(pokemon['pokemonId'], pokemon['latitude'],pokemon['longitude'], exptime.strftime('%Y-%m-%d %H:%M:%S'), response.meta['city']))

    def spider_idle(self):
        request = Request(self.api_url%(37.8089603,-122.4104494),callback=self.search_regions, dont_filter = True)
        self.crawler.engine.crawl(request, self)






import time

from gevent import monkey; monkey.patch_all()
import bottle
import json
import select
import os

from connector import post_message, get_messages, r as redis_instance

@bottle.route('/test')
def test():
    data = [ 'one', 'two', 'three', 'four' ]
    for d in data:
        yield d
        time.sleep(5)

def body_to_json(request):
   b = request._get_body_string()
   if not b:
      return None
   try:
      return json.loads(b)
   except (ValueError, TypeError):
      raise bottle.HTTPError(400, 'Invalid JSON')

@bottle.get('/db/<database:re:[a-zA-Z_0-9]+>/messages')
@bottle.get('/messages')
def get_messages_api(database=None):
   if database is None:
      if bottle.request.query.database:
         database = bottle.request.query.database
   assert database is not None
   kwargs = dict(database=database)  # required
   for r in ['hostname', 'program', 'event', 'level']:
      if bottle.request.query.get(r):
         kwargs.update({r: bottle.request.query.get(r)})

   bottle.response.content_type = 'application/json'
   return json.dumps(get_messages(**kwargs))

@bottle.post('/db/<database:re:[a-zA-Z_0-9]+>/messages')
@bottle.post('/messages')
def post_messages_api(database=None):
   json_data = body_to_json(bottle.request)
   if database is None:
      database = json_data.get('database')
   if database is None: raise bottle.HTTPError(400, 'database is required')

   message = json_data.get('message')
   if message is None: raise bottle.HTTPError(400, 'message is required')

   username = 'TODO:username'
   hostname = 'TODO:hostname'

   kwargs = dict(database=database,
                 username=username,
                 hostname=hostname,
                 message=message,
                 )
   for r in ['hostname', 'program', 'event', 'level']:
      if json_data.get(r):
         kwargs.update({r: json_data.get(r)})

   return post_message(**kwargs)

@bottle.get('/db/<database:re:[a-zA-Z_0-9]+>/messages/new')
@bottle.get('/messages/new')
def new_messages(database = None):
   if database is None:
      if bottle.request.query.database:
         database = bottle.request.query.database
   assert database is not None
   prefix = 'messages:'
   pub_key = "{prefix}{database}:keychanges".format(prefix = prefix,database=database)
   ps = redis_instance.pubsub(ignore_subscribe_messages = True)
   ps.subscribe(pub_key)

   bottle.response.content_type = 'application/json'
   yield '['
   comma = ''
   n = 0
   c = 0
   while n < 10:
      x = ps.get_message() # non-blocking
      if x:
         c = 1
         k = x['data']
         ks = k.split(':')
         d = {'hostname': ks[-2]}
         d.update(redis_instance.hgetall(k))
         yield comma + json.dumps(d) # format....
         comma = ','
      else:
         n += c
         time.sleep(0.01)
   # yield comma + '{{n:{},c:{},x:{}}}'.format(n, c, x)
   yield ']' # close the array

@bottle.get('/db/<database:re:[a-zA-Z_0-9]+>/messages/new3')
@bottle.get('/messages/new3')
def new_messages3(database = None, timeout = 10.0):
   '''
   wait up to 10 seconds for a new message, if there is more than one immediately available
   they ought to all be returned, however there may be messages missed if the client
   is unable to poll again fast enough...

   could track with time to live the last message sent to a client.... maybe...
   ugh.

   :param database:
   :param timeout:
   :return:
   '''
   if database is None:
      if bottle.request.query.database:
         database = bottle.request.query.database
   assert database is not None
   prefix = 'messages:'
   pub_key = "{prefix}{database}:keychanges".format(prefix = prefix,database=database)
   ps = redis_instance.pubsub(ignore_subscribe_messages = True)
   ps.subscribe(pub_key)

   bottle.response.content_type = 'application/json'
   yield '['
   comma = ''

   x = True
   timeout_time = time.time() + timeout
   while time.time() < timeout_time:
      x = ps.get_message()
      if x:
         k = x['data']
         ks = k.split(':')
         d = {'hostname': ks[-2]}
         d.update(redis_instance.hgetall(k))
         yield comma + json.dumps(d) # format....
         comma = ','
      else:
         if comma: break # there was a message, but not more than one immediately available
   yield ']' # close the array

@bottle.get('/db/<database:re:[a-zA-Z_0-9]+>/messages/new2')
@bottle.get('/messages/new2')
def new_messages2(database=None):
   '''
   this works, but the long-polling approach starts/stops connections to the redis server pub/sub
   over and over -- and we're bound to lose something in the process...

   if a client doesn't start polling again fast enough it'll miss messages...

   :param database:
   :return:
   '''
   if database is None:
      if bottle.request.query.database:
         database = bottle.request.query.database
   assert database is not None
   prefix = 'messages:'
   pub_key = "{prefix}{database}:keychanges".format(prefix=prefix, database=database)
   ps = redis_instance.pubsub(ignore_subscribe_messages = True)
   ps.subscribe(pub_key)

   bottle.response.content_type = 'application/json'

   fd = ps.connection._sock.fileno();
   while 1: # blocking
      rlist,_,_ = select.select([fd], [], [], 0)  # or replace 0 with None to block
      if rlist:
         for rfd in rlist:
            if fd == rfd:
               x = ps.get_message()
               if x:
                  k = x['data']
                  ks = k.split(':')
                  d = {'hostname': ks[-2]}
                  d.update(redis_instance.hgetall(k))
                  return json.dumps(d) # format....
      time.sleep(0.01) # ... be nice


@bottle.route('/')
@bottle.route('/<path:path>')
def static(path = ''):
   if path == '': path = 'index.html'
   return bottle.static_file(path, root=os.path.split(__file__)[0]+'/html')

def main():
    bottle.run(host = "0.0.0.0", port=9090, server="gevent", debug=True)

if __name__ == '__main__':
    main()
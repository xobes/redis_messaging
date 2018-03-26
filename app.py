import bottle
import json

from connector import get_messages, post_message

from bottle import Bottle, route, run, get, post, request, HTTPError, response

def body_to_json(request):
   b = request._get_body_string()
   if not b:
      return None
   try:
      return json.loads(b)
   except (ValueError, TypeError):
      raise HTTPError(400, 'Invalid JSON')

app = Bottle()

@app.route('/hello')
def hello():
    return "Hello World!"

@app.get('/db/<database:re:[a-zA-Z_0-9]+>/messages')
@app.get('/messages')
def get_messages_api(database = None):
   if database is None:
      if request.query.database:
         database = request.query.database
   assert database is not None
   kwargs = dict(database = database) # required
   for r in ['hostname', 'program', 'event', 'level']:
      if request.query.get(r):
         kwargs.update({r: request.query.get(r)})

   response.content_type = 'application/json'
   return json.dumps(get_messages(**kwargs))


@app.post('/db/<database:re:[a-zA-Z_0-9]+>/messages')
@app.post('/messages')
def get_messages_api(database = None):
   json_data = body_to_json(request)
   if database is None:
      database = json_data.get('database')
   if database is None: raise HTTPError(400, 'database is required')

   message = json_data.get('message')
   if message is None: raise HTTPError(400, 'message is required')

   username = 'TODO:username'
   hostname = 'TODO:hostname'

   kwargs = dict(database = database,
                 username = username,
                 hostname = hostname,
                 message = message,
                )
   for r in ['hostname', 'program', 'event', 'level']:
      if json_data.get(r):
         kwargs.update({r: json_data.get(r)})

   return post_message(**kwargs)

app.run(host='localhost', port=8080, debug=True)
import redis
import time

r = redis.StrictRedis(host='192.168.1.2', port=6379, db=0)

_DEFAULT_MAX_MESSAGES = 200
_DEFAULT_TTL_SECONDS = 30 * 24 * 60 * 60 # days * h/d * m/h * s/m => days in seconds
message_levels = ('DEBUG','INFO','WARN','ERROR','CRITICAL')

def post_message(database,
                 hostname,
                 message,
                 username,
                 program = None,
                 event = None,
                 level = 'INFO',
                ):
   if level not in message_levels:
      raise Exception("level must be one of {}".format(message_levels))

   message_time = time.time()
   timekey = int(message_time * 1000) # ms, integer -- like javascript

   prefix = 'messages:'
   key = "{prefix}{database}:m:{hostname}:{timekey}".format(
         prefix = prefix,
         database=database,
         hostname=hostname,
         timekey=timekey,
      )
   settings_key = "{prefix}{database}:settings".format(prefix = prefix,database=database)
   messages_key = "{prefix}{database}:messages".format(prefix = prefix,database=database)
   pub_key = "{prefix}{database}:keychanges".format(prefix = prefix,database=database)

   data = dict(
      message = str(message),
      username = str(username),
      timestamp = message_time,
      level = level,
   )
   if program is not None: data.update(dict(program=str(program)))
   if event is not None: data.update(dict(event=str(event)))

   p = r.pipeline()
   p.hget(settings_key, 'max_messages') # how many keys can wew have?
   p.hmset(key, data) # log the message
   p.expire(key, _DEFAULT_TTL_SECONDS) # set the message to expire
   p.rpush(messages_key, key) # track the new key
   p.llen(messages_key) # how many keys do we have now?
   p.publish(pub_key, key) # let others know about the key we just made #FUTURE ENHANCEMENTS!
   values = p.execute()
   # ---------------------------------------------------------
   # clean up the keyspace:
   max_messages = values[0]
   num_messages = values[-2] # one before the publish...
   if max_messages is None:
      max_messages = _DEFAULT_MAX_MESSAGES
   if num_messages > max_messages:
      p = r.pipeline()
      for i in range(num_messages - max_messages):
         p.lpop(messages_key) # pop n messages
      values = p.execute()
      p = r.pipeline()
      for k in values:
         p.delete(k) # delete the keys that we're no longer tracking, overflowed!
      p.execute()
   # end if
   #---------------------------------------------------------

def get_messages(database,
                 hostname = None,
                 program = None,
                 event = None,
                 level = "INFO", # default INFO
                ):
   if level not in message_levels:
      raise Exception("level must be one of {}".format(message_levels))

   messages = []

   prefix = 'messages:'

   # filter on hostname
   pattern = "{prefix}{database}:m:".format(prefix=prefix,database=database)
   if hostname is  None:
      pattern += "*"
   else:
      pattern += "{}:*".format(hostname)

   # print pattern

   p = r.pipeline()
   for k in r.scan_iter(match=pattern, count=100):
      # print k
      p.hgetall(k)
      ks = k.split(':')
      messages.append({
                       # 'key':k,
                       'hostname': ks[-2],
                       })
   values = p.execute()
   for i in range(len(values)):
      messages[i].update(values[i])
   # end for

   # remove messages that weren't found
   messages = [m for m in messages if m.get('timestamp') != None]

   if program: # filter on program
      messages = [m for m in messages if m.get('program') == str(program)]

   if event:  # filter on program
      messages = [m for m in messages if m.get('event') == str(event)]

   if level:  # filter on program
      messages = [m for m in messages if message_levels.index(m.get('level')) >= message_levels.index(str(level))]

   return sorted(messages, key=lambda m: float(m['timestamp']))

if __name__ == "__main__":
   print "use test.py..."
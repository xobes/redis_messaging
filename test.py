import random
from connector import *

if __name__ == "__main__":
   db = random.sample([
      'testing1',
      'testing2',
      'testing3',
      'testing4',
      'testing5',
      'testing6',
      'testing7',
   ], 1)[0]

   print "posting..."
   post_message(db, 'asdf', 'one', username = 'first')

   def f(i):
      if random.randint(0,5) > 1:
         return random.randint(0,2)
      else:
         return None
   def g(i):
      if random.randint(0,5) > 1:
         return random.randint(0,5)
      else:
         return None
   def h(i):
      return random.sample(message_levels,1)[0]

   for i in range(100):
      post_message(db, 'qwer', 'message %s'%(i),
                   username = 'username',
                   program = f(i),
                   event = g(i),
                   level = h(i),
                  )

   print "getting..."
   m = get_messages(db)
   for i in m:
      print i
   print "len(m) = {}".format(len(m))

   print "getting asdf..."
   m = get_messages(db, hostname="asdf")
   for i in m:
      print i
   print "len(m) = {}".format(len(m))

   x = f(i)
   print "getting program {}...".format(x)
   m = get_messages(db,program = x)
   for i in m:
      print i
   print "len(m) = {}".format(len(m))

   y = g(i)
   print "getting event {}...".format(y)
   m = get_messages(db, event=y)
   for i in m:
      print i
   print "len(m) = {}".format(len(m))


   print "getting program {}, event {}...".format(x,y)
   m = get_messages(db, program=x, event=y)
   for i in m:
      print i
   print "len(m) = {}".format(len(m))
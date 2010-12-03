import datetime
import web, time, re

STRING = 'The next episode of South Park will air on \x0300%s\x03.'

def southpark (phenny, input):
	today = time.localtime()
	src = web.get('http://en.wikipedia.org/wiki/List_of_South_Park_episodes')
	parts = src.split('Season 15 (2011)')
	cont = parts.pop()
	parts = cont.split('Shorts and unaired episodes')
	cont = parts[0]
	tds = cont.split('<td>')
	data = None
	for i in range(len(tds)):
		m = re.match('^[A-Z][a-z]{2,8} \d{1,2}, \d{4}', tds[i])
		if m is None:
			continue
		else:
			dt = time.strptime(m.group(), "%B %d, %Y")
			if dt < today:
				continue
			else:
				phenny.say(STRING % m.group())
				break

# time.strptime("30 Nov 00", "%d %b %y")
# http://www.comedycentral.com/tv_schedule/index.jhtml?seriesId=11600&forever=please
southpark.commands = ['southpark']

if __name__ == '__main__':
	print __doc__.strip()

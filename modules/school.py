#!/usr/bin/env python
"""
school.py - Jenni Class Schedule Module
Copyright 2010-2011, Michael Yanovich, yanovich.net

More info:
 * Jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
"""



import web, re

#r_link = re.compile(r'(?ims)<td>.*</td>')

r_link = re.compile(r'(?ims)<td><a\shref\="\S+">[)(\'\,\%\&\:\;\-\"\s\w]+</a></td><td>\d+</td></tr>')
r_link2 = re.compile(r'(?ims)<td><a\shref\="\S+">[)(\'\,\%\&\:\;\-\"\s\w]+</a></td>')

r_link4 = re.compile(r'(?ims)<p class="inset">.*\r<br>')

r_findtitle = re.compile(r'(?ims)<span\sclass\=\"roster\-name\">[)(\'\,\%\&\:\;\-\"\s\w]+</span>')

r_findreq = re.compile(r'(?ims)\r<br>.*<h3>')

#def classes(jenni, input):
#    """ shows classes at OSU  """
#    pass
'''
    info = input.group(2)
    info = info.split()
    if len(info) > 3 or len(info) < 3:
        jenni.say("Please enter information in the following format: .class UNIVERSITY_CODE DEPARTMENT_NAME COURSE_NUMBER")
        return
    uni = str(info[0])
    clname = str(info[1])
    clnum = str(info[2])

#===================================================================
# The following assums the campus and can only be used at OSU
#~ url = "http://" + uni + ".schedulizer.com/class/" + "Columbus%40" + clname + "%40" + clnum + "/"
#~ url = str(url)
#~ page = web.get(url)
#~ soup = BeautifulSoup(page)
#~ description = soup.find("p", {"class":"inset"})
#~ description = str(description)
#~ description = description.split("\n")
#~ req = description[1]
#~ both = description[0].split("</b><br /><br />")
#~ title = both[0]
#~ description_class = both[1]
#~
#~ class_name = re.sub("<p class=\"inset\"><b>", "Title: ", str(title))
#~
#~ title = re.sub(r'<[^>]*?>', '', str(title))
#~ description_class = re.sub(r'<[^>]*?>', '', str(description_class))
#~ req = re.sub(r'<[^>]*?>', '', str(req))
#~
#~ title = "Title: " + title
#~ description_class = "Description: " + description_class
#~
#~ jenni.say(title)
#~ jenni.say(description_class)
#~ jenni.say("Offered: " + req)
#===================================================================

    #Find the department
    url = "http://" + uni + ".schedulizer.com/add/departments/"
    page = web.get(url)
    #soup = BeautifulSoup(page)
    #listtd = soup.findAll("td")
    departments = r_link.findall(page)

    clname = clname.upper()
    clname2 = "(" + clname + ")"
    for item in departments:
        item = str(item)
        if clname2 in item:
            found = item
            break
    found_url = re.findall(r'".*"', str(found))
    found_url = str(found_url[0])
    found_url = found_url[1:-1]

    #Find the course information
    class_url = "http://" + uni + ".schedulizer.com" + found_url
    class_page = web.get(class_url)
    #soup2 = BeautifulSoup(class_page)
    #listtd2 = soup2.findAll("td")
    listtd2 = r_link2.findall(class_page)
    course = clname + " " + clnum
    course = str(course)
    course = ">" + course + "<"
    #jenni.say("Starting to look for course information")
    #jenni.say("course: " + course)
    found_course = ""
    for each in listtd2:
        each = str(each)
        if course in each:
            found_course = each
            #jenni.say(found_course)
    if not found_course:
        jenni.say("Sorry I could not find that course.")
        return

    found_course_url = re.findall(r'".*"', str(found_course))
    found_course_url = found_course_url[0]
    found_course_url = found_course_url[1:-1]
    course_url = "http://" + uni + ".schedulizer.com" + str(found_course_url)
    course_url = str(course_url)
    #jenni.say("course_url: " + str(course_url))
    course_page = web.get(course_url)
    #soup3 = BeautifulSoup(course_page)

    #description = soup3.find("p", {"class":"inset"})

    description_class = r_link4.findall(course_page)[0][36:-5]

    #if uni == "osu":
    #    req = description[1]
    # Made it this far
    #both = description[0].split("<p class="inset"><b></b><br /><br />")
    #title = both[0]
    #description_class = both[1]

    # I can find the course description, but not the title and anything below ,yet
    #2011

    title = r_findtitle.findall(course_page)[0][26:-7]
    title = unicode(title)

    #class_name = re.sub("<p class=\"inset\"><b>", "Title: ", str(title))

    #title = re.sub(r'<[^>]*?>', '', str(title))
    #description_class = re.sub(r'<[^>]*?>', '', str(description_class))
    if uni == "osu":
        #req = re.sub(r'<[^>]*?>', '', str(req))
        req = r_findreq.findall(course_page)[0][5:-8]
        req = req.replace("<br>", " ")



    title = "Title: " + str(title)
    description_class = "Description: " + str(description_class)

    jenni.say(str(title))
    jenni.say(str(description_class))
    if uni == "osu":
        jenni.say("Offered: " + str(req))
'''
#classes.commands = ['class']
#classes.priority = 'high'


if __name__ == '__main__':
    print __doc__.strip()


#!/usr/bin/env python
"""
school.py - Class Schedule Module
Author: Michael S. Yanovich http://opensource.cse.ohio-state.edu/
Jenni (About): http://inamidst.com/phenny/
"""

'''
import web, re

r_link = re.compile(r'(?ims)<td>.*</td>')

def classes(jenni, input):

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
    soup = BeautifulSoup(page)
    listtd = soup.findAll("td")
    clname = clname.upper()
    clname2 = "(" + clname + ")"
    for item in listtd:
        item = str(item)
        if clname2 in item:
            found = item
            break
    found_url = re.findall(r'".*"', str(found))	
    found_url = str(found_url[0])
    found_url = found_url[1:-1] 
    #jenni.say("Found department page")

    #Find the course information
    class_url = "http://" + uni + ".schedulizer.com" + found_url
    class_page = web.get(class_url)
    soup2 = BeautifulSoup(class_page)
    listtd2 = soup2.findAll("td")
    course = clname + " " + clnum
    course = str(course)
    course = ">" + course + "<"
    #jenni.say("Starting to look for course information")
    #jenni.say("course: " + course)
    for each in listtd2:
        each = str(each)
        if course in each:
            found_course = each
            #jenni.say(found_course)
        else:
            jenni.say("Sorry I can not find that class.")
            return

    found_course_url = re.findall(r'".*"', str(found_course))
    found_course_url = found_course_url[0]
    found_course_url = found_course_url[1:-1]
    course_url = "http://" + uni + ".schedulizer.com" + str(found_course_url)
    course_url = str(course_url)
    #jenni.say("course_url: " + str(course_url))
    course_page = web.get(course_url)
    soup3 = BeautifulSoup(course_page)

    description = soup3.find("p", {"class":"inset"})
    description = str(description)
    description = description.split("\n")
    if uni == "osu":
        req = description[1]

    both = description[0].split("</b><br /><br />")
    title = both[0]
    description_class = both[1]

    class_name = re.sub("<p class=\"inset\"><b>", "Title: ", str(title))

    title = re.sub(r'<[^>]*?>', '', str(title))
    description_class = re.sub(r'<[^>]*?>', '', str(description_class))
    if uni == "osu":
        req = re.sub(r'<[^>]*?>', '', str(req))

    title = "Title: " + str(title)
    description_class = "Description: " + str(description_class)

    jenni.say(str(title))
    jenni.say(str(description_class))
    if uni == "osu":
        jenni.say("Offered: " + str(req))

classes.commands = ['class']
classes.priority = 'high'

'''

if __name__ == '__main__': 
    print __doc__.strip()


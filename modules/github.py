
import time

def post(phenny,input):
    from github2.client import Github
    #github = Github(username="myano", api_token=input.github_api_key)

    #text = input.group()
    #user_title = input.nick + " - " + str(time.time())
    #new_issue = github.issues.open("myano/phenny_osu", title=user_title, body=text)
    #phenny.say("Succesfully posted idea to: http://github.com/myano/phenny_osu/issues#issue/" + str(new_issue.number))
    # phenny.say("I see you trying to make a suggestion!")
post.rule = '.*(phenny|$nickname)\:?\s(could|should).*'

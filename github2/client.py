from github2.request import GithubRequest
from github2.issues import Issues
from github2.repositories import Repositories
from github2.users import Users
from github2.commits import Commits

class Github(object):

    def __init__(self, username=None, api_token=None, debug=False):
        self.debug = debug
        self.request = GithubRequest(username=username, api_token=api_token,
                                     debug=self.debug)
        self.issues = Issues(self.request)
        self.users = Users(self.request)
        self.repos = Repositories(self.request)
        self.commits = Commits(self.request)

    def project_for_user_repo(self, user, repo):
        return "/".join([user, repo])

    def get_blob_info(self, project, tree_sha, path):
        blob = self.request.get("blob/show", project, tree_sha, path)
        return blob.get("blob")

    def get_tree(self, project, tree_sha):
        tree = self.request.get("tree/show", project, tree_sha)
        return tree.get("tree", [])

    def get_network_meta(self, project):
        return self.request.raw_request("/".join([self.request.github_url,
                                                  project,
                                                  "network_meta"] ), {})

    def get_network_data(self, project, nethash, start=None, end=None):
        return self.request.raw_request("/".join([self.request.github_url,
                                                  project,
                                                  "network_data_chunk"]),
                                                  {"nethash": nethash,
                                                   "start": start,
                                                   "end": end})

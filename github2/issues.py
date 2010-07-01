from github2.core import GithubCommand, BaseData, Attribute, DateAttribute

class Issue(BaseData):
    position = Attribute("The position of this issue in a list.")
    number = Attribute("The issue number (unique for project).")
    votes = Attribute("Number of votes for this issue.")
    body = Attribute("The full description for this issue.")
    title = Attribute("Issue title.")
    user = Attribute("The username of the user that created this issue.")
    state = Attribute("State of this issue. Can be ``open`` or ``closed``.")
    labels = Attribute("Labels associated with this issue.")
    created_at = DateAttribute("The date this issue was created.")
    closed_at = DateAttribute("The date this issue was closed.")
    updated_at = DateAttribute("The date when this issue was last updated.")

    def __repr__(self):
        return "<Issue: %s>" % self.title


class Comment(BaseData):
    created_at = DateAttribute("The date this comment was created.")
    updated_at = DateAttribute("The date when this comment was last updated.")
    body = Attribute("The full text of this comment.")
    id = Attribute("The comment id.")
    user = Attribute("The username of the user that created this comment.")

    def __repr__(self):
        return "<Comment: %s>" % self.body


class Issues(GithubCommand):
    domain = "issues"

    def list(self, project, state="open"):
        """Get all issues for project' with state'.

        ``project`` is a string with the project owner username and repository
        name separated by ``/`` (e.g. ``ask/pygithub2``).
        ``state`` can be either ``open`` or ``closed``.
        """
        return self.get_values("list", project, state, filter="issues",
                               datatype=Issue)

    def show(self, project, number):
        """Get all the data for issue by issue-number."""
        return self.get_value("show", project, str(number),
                              filter="issue", datatype=Issue)

    def open(self, project, title, body):
        """Open up a new issue."""
        issue_data = {"title": title, "body": body}
        return self.get_value("open", project, post_data=issue_data,
                              filter="issue", datatype=Issue)

    def close(self, project, number):
        return self.get_value("close", project, str(number), filter="issue",
                              datatype=Issue)

    def add_label(self, project, number, label):
        return self.make_request("label/add", project, label, str(number),
                                 filter="labels")

    def remove_label(self, project, number, label):
        return self.make_request("label/remove", project, label, str(number),
                                 filter="labels")

    def comment(self, project, number, comment):
        """Comment on an issue."""
        comment_data = {'comment': comment}
        return self.make_request("comment", project, str(number),
                                 post_data=comment_data,
                                 filter='comment')

    def comments(self, project, number):
        """View comments on an issue."""
        return self.get_values("comments", project, str(number),
                               filter="comments", datatype=Comment)

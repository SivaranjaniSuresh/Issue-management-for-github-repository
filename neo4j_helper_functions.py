import logging

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable


class Neo4jGitHub:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    ####################################################################################################################################
    ### Create Nodes
    ####################################################################################################################################

    def create_issue(
        self, owner, repo_name, issue_number, issue_description, issue_body
    ):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._create_issue,
                    owner,
                    repo_name,
                    issue_number,
                    issue_description,
                    issue_body,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _create_issue(
        tx, owner, repo_name, issue_number, issue_description, issue_body
    ):
        query = (
            "MERGE (i:Issue {Owner: $owner, RepoName: $repo_name, IssueNumber: $issue_number}) "
            "ON CREATE SET i.IssueDescription = $issue_description, i.IssueBody = $issue_body"
        )
        tx.run(
            query,
            owner=owner,
            repo_name=repo_name,
            issue_number=issue_number,
            issue_description=issue_description,
            issue_body=issue_body,
        )

    def create_user(self, github_id):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(self._create_user, github_id)
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _create_user(tx, github_id):
        query = "MERGE (u:User {GithubId: $github_id})"
        tx.run(query, github_id=github_id)

    def create_reaction(self, reaction_name):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(self._create_reaction, reaction_name)
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _create_reaction(tx, reaction_name):
        query = "MERGE (r:Reaction {ReactionName: $reaction_name})"
        tx.run(query, reaction_name=reaction_name)

    def create_label(self, label_type):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(self._create_label, label_type)
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _create_label(tx, label_type):
        query = "MERGE (l:Label {LabelType: $label_type})"
        tx.run(query, label_type=label_type)

    def create_milestone(self, milestone_type):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(self._create_milestone, milestone_type)
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _create_milestone(tx, milestone_type):
        query = "MERGE (m:Milestone {MilestoneType: $milestone_type})"
        tx.run(query, milestone_type=milestone_type)

    def create_comment(self, comment_id, comment_body):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(self._create_comment, comment_id, comment_body)
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _create_comment(tx, comment_id, comment_body):
        query = "MERGE (c:Comment {CommentId: $comment_id}) ON CREATE SET c.CommentBody = $comment_body"
        tx.run(query, comment_id=comment_id, comment_body=comment_body)

    ####################################################################################################################################
    ### Create Relationships
    ####################################################################################################################################

    def create_issue_creator_relationship(
        self, user_github_id, issue_owner, issue_repo_name, issue_number
    ):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._create_issue_creator_relationship,
                    user_github_id,
                    issue_owner,
                    issue_repo_name,
                    issue_number,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _create_issue_creator_relationship(
        tx, user_github_id, issue_owner, issue_repo_name, issue_number
    ):
        query = (
            "MATCH (u:User {GithubId: $user_github_id}), "
            "(i:Issue {Owner: $issue_owner, RepoName: $issue_repo_name, IssueNumber: $issue_number}) "
            "MERGE (u)-[rel:CREATED]->(i) "
            "ON CREATE SET rel.uid = u.GithubId + '-' + i.Owner + '-' + i.RepoName + '-' + toString(i.IssueNumber)"
        )
        tx.run(
            query,
            user_github_id=user_github_id,
            issue_owner=issue_owner,
            issue_repo_name=issue_repo_name,
            issue_number=issue_number,
        )

    def create_issue_assigner_relationship(
        self,
        assigner_github_id,
        assignee_github_id,
        issue_owner,
        issue_repo_name,
        issue_number,
    ):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._create_issue_assigner_relationship,
                    assigner_github_id,
                    assignee_github_id,
                    issue_owner,
                    issue_repo_name,
                    issue_number,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _create_issue_assigner_relationship(
        tx,
        assigner_github_id,
        assignee_github_id,
        issue_owner,
        issue_repo_name,
        issue_number,
    ):
        query = (
            "MATCH (u1:User {GithubId: $assigner_github_id}), "
            "(u2:User {GithubId: $assignee_github_id}), "
            "(i:Issue {Owner: $issue_owner, RepoName: $issue_repo_name, IssueNumber: $issue_number}) "
            "MERGE (u1)<-[rel:ASSIGNED_ON_ISSUE_BY]-(u2) "
            "ON CREATE SET rel.uid = u1.GithubId + '-' + u2.GithubId + '-' + i.Owner + '-' + i.RepoName + '-' + toString(i.IssueNumber), rel.Timestamp = timestamp() "
            "MERGE (u2)-[rel2:ASSIGNED_TO]->(i) "
            "ON CREATE SET rel2.uid = u2.GithubId + '-' + i.Owner + '-' + i.RepoName + '-' + toString(i.IssueNumber), rel2.Timestamp = timestamp()"
        )
        tx.run(
            query,
            assigner_github_id=assigner_github_id,
            assignee_github_id=assignee_github_id,
            issue_owner=issue_owner,
            issue_repo_name=issue_repo_name,
            issue_number=issue_number,
        )

    def user_reacted_on_issue(
        self, github_id, issue_owner, issue_repo_name, issue_number, reaction_name
    ):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._create_user_reaction_relationship,
                    github_id,
                    issue_owner,
                    issue_repo_name,
                    issue_number,
                    reaction_name,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _create_user_reaction_relationship(
        tx, github_id, issue_owner, issue_repo_name, issue_number, reaction_name
    ):
        query = (
            "MATCH (u:User {GithubId: $github_id}), "
            "(i:Issue {Owner: $issue_owner, RepoName: $issue_repo_name, IssueNumber: $issue_number}) "
            "MERGE (u)-[rel:REACTED_TO_ISSUE]->(i) "
            "ON CREATE SET rel.uid = u.GithubId + '-' + i.Owner + '-' + i.RepoName + '-' + toString(i.IssueNumber) + '-' + $reaction_name, "
            "rel.ReactionName = $reaction_name, rel.Timestamp = timestamp()"
        )
        tx.run(
            query,
            github_id=github_id,
            issue_owner=issue_owner,
            issue_repo_name=issue_repo_name,
            issue_number=issue_number,
            reaction_name=reaction_name,
        )

    def user_added_milestone(
        self, github_id, issue_owner, issue_repo_name, issue_number, milestone_type
    ):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._create_user_milestone_relationship,
                    github_id,
                    issue_owner,
                    issue_repo_name,
                    issue_number,
                    milestone_type,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _create_user_milestone_relationship(
        tx, github_id, issue_owner, issue_repo_name, issue_number, milestone_type
    ):
        query = (
            "MATCH (u:User {GithubId: $github_id}), "
            "(i:Issue {Owner: $issue_owner, RepoName: $issue_repo_name, IssueNumber: $issue_number}) "
            "MERGE (u)-[rel:ADDED_MILESTONE]->(i) "
            "ON CREATE SET rel.uid = u.GithubId + '-' + i.Owner + '-' + i.RepoName + '-' + toString(i.IssueNumber) + '-' + $milestone_type, "
            "rel.MilestoneType = $milestone_type, rel.Timestamp = timestamp()"
        )
        tx.run(
            query,
            github_id=github_id,
            issue_owner=issue_owner,
            issue_repo_name=issue_repo_name,
            issue_number=issue_number,
            milestone_type=milestone_type,
        )

    def issue_has_label(self, issue_owner, issue_repo_name, issue_number, label_type):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._create_issue_label_relationship,
                    issue_owner,
                    issue_repo_name,
                    issue_number,
                    label_type,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _create_issue_label_relationship(
        tx, issue_owner, issue_repo_name, issue_number, label_type
    ):
        query = (
            "MATCH (i:Issue {Owner: $issue_owner, RepoName: $issue_repo_name, IssueNumber: $issue_number}), "
            "(l:Label {LabelType: $label_type}) "
            "MERGE (i)-[rel:HAS_LABEL]->(l) "
            "ON CREATE SET rel.uid = i.Owner + '-' + i.RepoName + '-' + toString(i.IssueNumber) + '-' + l.LabelType"
        )
        tx.run(
            query,
            issue_owner=issue_owner,
            issue_repo_name=issue_repo_name,
            issue_number=issue_number,
            label_type=label_type,
        )

    def user_commented_on_issue(
        self, github_id, issue_owner, issue_repo_name, issue_number, comment_id
    ):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._create_user_comment_relationship,
                    github_id,
                    issue_owner,
                    issue_repo_name,
                    issue_number,
                    comment_id,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _create_user_comment_relationship(
        tx, github_id, issue_owner, issue_repo_name, issue_number, comment_id
    ):
        query = (
            "MATCH (u:User {GithubId: $github_id}), "
            "(i:Issue {Owner: $issue_owner, RepoName: $issue_repo_name, IssueNumber: $issue_number}), "
            "(c:Comment {CommentId: $comment_id}) "
            "MERGE (u)-[rel:COMMENTED]->(c) "
            "ON CREATE SET rel.uid = u.GithubId + '-' + i.Owner + '-' + i.RepoName + '-' + toString(i.IssueNumber) + '-' + toString(c.CommentId), rel.Timestamp = timestamp() "
            "MERGE (c)<-[rel2:HAS_COMMENT]-(i) "
            "ON CREATE SET rel2.uid = c.CommentId + '-' + i.Owner + '-' + i.RepoName + '-' + toString(i.IssueNumber), rel2.Timestamp = timestamp()"
        )
        tx.run(
            query,
            github_id=github_id,
            issue_owner=issue_owner,
            issue_repo_name=issue_repo_name,
            issue_number=issue_number,
            comment_id=comment_id,
        )

    def user_reacted_on_comment(self, github_id, comment_id, reaction_type):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._create_user_comment_reaction_relationship,
                    github_id,
                    comment_id,
                    reaction_type,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _create_user_comment_reaction_relationship(
        tx, github_id, comment_id, reaction_type
    ):
        query = (
            "MATCH (u:User {GithubId: $github_id}), "
            "(c:Comment {CommentId: $comment_id}) "
            "MERGE (u)-[rel:REACTED_TO_COMMENT]->(c) "
            "ON CREATE SET rel.uid = u.GithubId + '-' + toString(c.CommentId) + '-' + $reaction_type, "
            "rel.ReactionName = $reaction_type, rel.Timestamp = timestamp()"
        )
        tx.run(
            query,
            github_id=github_id,
            comment_id=comment_id,
            reaction_type=reaction_type,
        )

    ####################################################################################################################################
    ### Remove Nodes
    ####################################################################################################################################

    def remove_issue(self, owner, repo_name, issue_number):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._remove_issue,
                    owner,
                    repo_name,
                    issue_number,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _remove_issue(tx, owner, repo_name, issue_number):
        query = (
            "MATCH (i:Issue {Owner: $owner, RepoName: $repo_name, IssueNumber: $issue_number}) "
            "DETACH DELETE i"
        )
        tx.run(
            query,
            owner=owner,
            repo_name=repo_name,
            issue_number=issue_number,
        )

    def remove_user(self, github_id):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(self._remove_user, github_id)
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _remove_user(tx, github_id):
        query = "MATCH (u:User {GithubId: $github_id}) DETACH DELETE u"
        tx.run(query, github_id=github_id)

    def remove_reaction(self, reaction_name):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(self._remove_reaction, reaction_name)
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _remove_reaction(tx, reaction_name):
        query = "MATCH (r:Reaction {ReactionName: $reaction_name}) DETACH DELETE r"
        tx.run(query, reaction_name=reaction_name)

    def remove_label(self, label_type):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(self._remove_label, label_type)
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _remove_label(tx, label_type):
        query = "MATCH (l:Label {LabelType: $label_type}) DETACH DELETE l"
        tx.run(query, label_type=label_type)

    def remove_milestone(self, milestone_type):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(self._remove_milestone, milestone_type)
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _remove_milestone(tx, milestone_type):
        query = "MATCH (m:Milestone {MilestoneType: $milestone_type}) DETACH DELETE m"
        tx.run(query, milestone_type=milestone_type)

    def remove_comment(self, comment_id):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(self._remove_comment, comment_id)
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _remove_comment(tx, comment_id):
        query = """
        MATCH (c:Comment {CommentId: $comment_id})
        DETACH DELETE c
        """
        tx.run(query, comment_id=comment_id)

    ####################################################################################################################################
    ### Remove Relationships
    ####################################################################################################################################

    def remove_issue_creator_relationship(
        self, user_github_id, issue_owner, issue_repo_name, issue_number
    ):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._remove_issue_creator_relationship,
                    user_github_id,
                    issue_owner,
                    issue_repo_name,
                    issue_number,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _remove_issue_creator_relationship(
        tx, user_github_id, issue_owner, issue_repo_name, issue_number
    ):
        query = (
            "MATCH (u:User {GithubId: $user_github_id})-[rel:CREATED]->(i:Issue {Owner: $issue_owner, RepoName: $issue_repo_name, IssueNumber: $issue_number}) "
            "DELETE rel"
        )
        tx.run(
            query,
            user_github_id=user_github_id,
            issue_owner=issue_owner,
            issue_repo_name=issue_repo_name,
            issue_number=issue_number,
        )

    def remove_issue_assigner_relationship(
        self,
        assigner_github_id,
        assignee_github_id,
        issue_owner,
        issue_repo_name,
        issue_number,
    ):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._remove_issue_assigner_relationship,
                    assigner_github_id,
                    assignee_github_id,
                    issue_owner,
                    issue_repo_name,
                    issue_number,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _remove_issue_assigner_relationship(
        tx,
        assigner_github_id,
        assignee_github_id,
        issue_owner,
        issue_repo_name,
        issue_number,
    ):
        query = (
            "MATCH (u1:User {GithubId: $assigner_github_id})<-[rel:ASSIGNED_ON_ISSUE_BY]-(u2:User {GithubId: $assignee_github_id}) "
            "WHERE rel.uid = u1.GithubId + '-' + u2.GithubId + '-' + $issue_owner + '-' + $issue_repo_name + '-' + toString($issue_number) "
            "DELETE rel "
            "WITH u2 "
            "MATCH (u2)-[rel2:ASSIGNED_TO]->(i:Issue {Owner: $issue_owner, RepoName: $issue_repo_name, IssueNumber: $issue_number}) "
            "WHERE rel2.uid = u2.GithubId + '-' + i.Owner + '-' + i.RepoName + '-' + toString(i.IssueNumber) "
            "DELETE rel2"
        )
        tx.run(
            query,
            assigner_github_id=assigner_github_id,
            assignee_github_id=assignee_github_id,
            issue_owner=issue_owner,
            issue_repo_name=issue_repo_name,
            issue_number=issue_number,
        )

    def remove_user_reaction_relationship(
        self, github_id, issue_owner, issue_repo_name, issue_number, reaction_name
    ):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._remove_user_reaction_relationship,
                    github_id,
                    issue_owner,
                    issue_repo_name,
                    issue_number,
                    reaction_name,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _remove_user_reaction_relationship(
        tx, github_id, issue_owner, issue_repo_name, issue_number, reaction_name
    ):
        query = (
            "MATCH (u:User {GithubId: $github_id})-[rel:REACTED_TO_ISSUE]->(i:Issue {Owner: $issue_owner, RepoName: $issue_repo_name, IssueNumber: $issue_number}) "
            "WHERE rel.ReactionName = $reaction_name "
            "DELETE rel"
        )

        tx.run(
            query,
            github_id=github_id,
            issue_owner=issue_owner,
            issue_repo_name=issue_repo_name,
            issue_number=issue_number,
            reaction_name=reaction_name,
        )

    def remove_user_milestone_relationship(
        self, github_id, issue_owner, issue_repo_name, issue_number, milestone_type
    ):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._remove_user_milestone_relationship,
                    github_id,
                    issue_owner,
                    issue_repo_name,
                    issue_number,
                    milestone_type,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _remove_user_milestone_relationship(
        tx, github_id, issue_owner, issue_repo_name, issue_number, milestone_type
    ):
        query = (
            "MATCH (u:User {GithubId: $github_id})-[rel:ADDED_MILESTONE]->(i:Issue {Owner: $issue_owner, RepoName: $issue_repo_name, IssueNumber: $issue_number}) "
            "WHERE rel.MilestoneType = $milestone_type "
            "DELETE rel"
        )
        tx.run(
            query,
            github_id=github_id,
            issue_owner=issue_owner,
            issue_repo_name=issue_repo_name,
            issue_number=issue_number,
            milestone_type=milestone_type,
        )

    def remove_issue_label_relationship(
        self, issue_owner, issue_repo_name, issue_number, label_type
    ):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._remove_issue_label_relationship,
                    issue_owner,
                    issue_repo_name,
                    issue_number,
                    label_type,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _remove_issue_label_relationship(
        tx, issue_owner, issue_repo_name, issue_number, label_type
    ):
        query = (
            "MATCH (i:Issue {Owner: $issue_owner, RepoName: $issue_repo_name, IssueNumber: $issue_number})-[rel:HAS_LABEL]->(l:Label {LabelType: $label_type}) "
            "DELETE rel"
        )
        tx.run(
            query,
            issue_owner=issue_owner,
            issue_repo_name=issue_repo_name,
            issue_number=issue_number,
            label_type=label_type,
        )

    def user_removed_comment(
        self, github_id, issue_owner, issue_repo_name, issue_number, comment_id
    ):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._remove_user_comment_relationship,
                    github_id,
                    issue_owner,
                    issue_repo_name,
                    issue_number,
                    comment_id,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _remove_user_comment_relationship(
        tx, github_id, issue_owner, issue_repo_name, issue_number, comment_id
    ):
        query = (
            "MATCH (u:User {GithubId: $github_id})-[rel:COMMENTED]->(c:Comment {CommentId: $comment_id}) "
            "WHERE rel.uid = u.GithubId + '-' + $issue_owner + '-' + $issue_repo_name + '-' + toString($issue_number) + '-' + toString(c.CommentId) "
            "DELETE rel "
            "WITH c "
            "MATCH (c)<-[rel2:HAS_COMMENT]-(i:Issue {Owner: $issue_owner, RepoName: $issue_repo_name, IssueNumber: $issue_number}) "
            "WHERE rel2.uid = c.CommentId + '-' + i.Owner + '-' + i.RepoName + '-' + toString(i.IssueNumber) "
            "DELETE rel2"
        )
        tx.run(
            query,
            github_id=github_id,
            issue_owner=issue_owner,
            issue_repo_name=issue_repo_name,
            issue_number=issue_number,
            comment_id=comment_id,
        )

    def user_removed_reaction(self, github_id, comment_id, reaction_type):
        try:
            with self.driver.session(database="neo4j") as session:
                session.execute_write(
                    self._remove_user_comment_reaction_relationship,
                    github_id,
                    comment_id,
                    reaction_type,
                )
        except ServiceUnavailable as e:
            logging.error(f"ServiceUnavailable exception occurred: {e}")

    @staticmethod
    def _remove_user_comment_reaction_relationship(
        tx, github_id, comment_id, reaction_type
    ):
        query = (
            "MATCH (u:User {GithubId: $github_id})-[rel:REACTED_TO_COMMENT]->(c:Comment {CommentId: $comment_id}) "
            "WHERE rel.ReactionName = $reaction_type "
            "DELETE rel"
        )
        tx.run(
            query,
            github_id=github_id,
            comment_id=comment_id,
            reaction_type=reaction_type,
        )

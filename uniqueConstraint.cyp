CREATE CONSTRAINT issue_unique 
FOR (i:Issue) 
REQUIRE (i.Owner, i.RepoName, i.IssueNumber) IS NODE KEY

CREATE CONSTRAINT user_unique 
FOR (u:User) 
REQUIRE u.GithubId IS UNIQUE

CREATE CONSTRAINT reaction_unique 
FOR (r:Reaction) 
REQUIRE r.ReactionName IS UNIQUE

CREATE CONSTRAINT label_unique 
FOR (l:Label) 
REQUIRE l.LabelType IS UNIQUE

CREATE CONSTRAINT milestone_unique 
FOR (m:Milestone) 
REQUIRE m.MilestoneType IS UNIQUE

CREATE CONSTRAINT comment_id_unique
FOR (c:Comment)
REQUIRE c.CommentId IS UNIQUE


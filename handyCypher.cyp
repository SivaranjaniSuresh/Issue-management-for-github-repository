## Delete All Nodes, and Relationships
MATCH (n)
OPTIONAL MATCH (n)-[r]-()
DELETE n, r

## Remove All Nodes, and Relationships
MATCH (n)
RETURN n

## retrieves all 1st-degree outgoing relationships and both 1st and 2nd-degree incoming relationships for a specific issue node
MATCH (issue:Issue {Owner: 'BigDataIA-Spring2023-Team-04', RepoName: 'BigDataIA-Assignment-03', IssueNumber: 6})
MATCH (issue)-[out_rel]->(out_node)
MATCH (in_node1)-[in_rel1]->(issue)
OPTIONAL MATCH (in_node2)-[in_rel2]->(in_node1)
RETURN issue, out_rel, out_node, in_node1, in_rel1, in_node2, in_rel2
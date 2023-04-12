## Delete All Nodes, and Relationships
MATCH (n)
OPTIONAL MATCH (n)-[r]-()
DELETE n, r

## Remove All Nodes, and Relationships
MATCH (n)
RETURN n
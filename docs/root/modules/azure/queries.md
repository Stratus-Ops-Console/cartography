# Azure Queries

## Find Users with the Owner Role

```cypher
MATCH (user:EntraUser)-[:HAS_ROLE_ASSIGNMENT]->(assignment:AzureRoleAssignment)
      -[:ROLE_ASSIGNED]->(role:AzureRoleDefinition)
WHERE role.role_name = "Owner"
RETURN user.email, assignment.scope
```

## Find Principals with Storage Write Access

```cypher
MATCH (assignment:AzureRoleAssignment)-[:ROLE_ASSIGNED]->(role:AzureRoleDefinition)
      -[:HAS_PERMISSIONS]->(permissions:AzurePermissions)
WHERE any(
  action IN permissions.actions
  WHERE action CONTAINS "Microsoft.Storage" AND action CONTAINS "write"
)
RETURN assignment.principal_id, assignment.principal_type, role.role_name,
       assignment.scope
```

## Find High-Privilege Service Principals

```cypher
MATCH (principal:EntraServicePrincipal)-[:HAS_ROLE_ASSIGNMENT]->
      (assignment:AzureRoleAssignment)-[:ROLE_ASSIGNED]->
      (role:AzureRoleDefinition)
WHERE role.role_name IN ["Owner", "Contributor", "User Access Administrator"]
RETURN principal.display_name, role.role_name, assignment.scope
```

## List Deployed AI Models per Foundry Account

```cypher
MATCH (account:AzureAIFoundryAccount)-[:HAS_DEPLOYMENT]->
      (deployment:AzureAIFoundryDeployment)
RETURN account.name, deployment.name, deployment.model_name,
       deployment.model_version, deployment.sku_name,
       deployment.rai_policy_name
```

## Find AI Foundry Accounts That Still Accept API-Key Auth

```cypher
MATCH (account:AzureAIFoundryAccount)
WHERE account.disable_local_auth IS NULL OR account.disable_local_auth = false
RETURN account.name, account.kind, account.endpoint,
       account.public_network_access
```

## What Can This AI Foundry Project's Identity Access?

```cypher
MATCH (project:AzureAIFoundryProject)-[:ASSUMES]->(role:AzureRoleDefinition)
RETURN project.display_name, role.role_name
```

## Find Publicly Reachable Container Apps

```cypher
MATCH (env:AzureContainerAppsEnvironment)-[:HAS_APP]->(app:AzureContainerApp)
WHERE app.ingress_external = true
  AND (env.internal_load_balancer IS NULL OR env.internal_load_balancer = false)
RETURN app.name, app.fqdn, app.target_port, app.allow_insecure
```

## Find Static-Secret Connections Reachable from AI Foundry Projects

```cypher
MATCH (project:AzureAIFoundryProject)-[:HAS_CONNECTION]->
      (conn:AzureAIFoundryConnection)
WHERE conn.auth_type IN ["ApiKey", "AccountKey", "AccessKey", "SAS", "PAT",
                         "CustomKeys", "UsernamePassword"]
RETURN project.display_name, conn.name, conn.category, conn.auth_type,
       conn.target
```

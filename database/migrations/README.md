
# Database migrations

Store each database change in a separate, numbered SQL file.

Examples:
- 001_create_products.sql
- 002_add_product_description.sql
- 003_add_product_status.sql

Before applying a migration:
1. Review the SQL.
2. Back up the database.
3. Test against a development or staging database.
4. Apply the migration once.
5. Record which migration was applied.

Do not edit an already-applied production migration.

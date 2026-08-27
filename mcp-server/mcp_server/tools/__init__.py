"""MCP tools for the Financial Manager server."""

from . import auth, invoices, mutations, queries

# (module, name) pairs - explicit registry so tools are easy to audit.
ALL_TOOLS = [
    # Authentication (must be called first by each user session)
    (auth, "login"),
    (auth, "logout"),
    (auth, "whoami"),
    # Queries
    (queries, "get_summary"),
    (queries, "get_statistics"),
    (queries, "list_sales"),
    (queries, "get_sale"),
    (queries, "list_purchases"),
    (queries, "get_purchase"),
    (queries, "list_customers"),
    (queries, "list_suppliers"),
    (queries, "list_companies"),
    (queries, "list_departments"),
    (queries, "list_types"),
    # Mutations
    (mutations, "create_sale"),
    (mutations, "update_sale"),
    (mutations, "delete_sale"),
    (mutations, "create_purchase"),
    (mutations, "update_purchase"),
    (mutations, "delete_purchase"),
    (mutations, "create_customer"),
    (mutations, "create_supplier"),
    (mutations, "create_company"),
    (mutations, "create_department"),
    (mutations, "create_type"),
    # Invoices
    (invoices, "generate_invoices_batch"),
]

__all__ = ["ALL_TOOLS"]

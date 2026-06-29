app_name = "tag_naming"
app_title = "Tag Naming"
app_publisher = "ai@tagdyn.com"
app_description = "Custom naming series for TAG manufacturing documents"
app_email = "ai@tagdyn.com"
app_license = "mit"

doc_events = {
    "Sales Order": {
        "before_insert": "tag_naming.tag_naming.naming.sales_order_before_insert",
    },
    "Project": {
        "before_insert": "tag_naming.tag_naming.naming.project_before_insert",
    },
    "Work Order": {
        "before_insert": "tag_naming.tag_naming.naming.work_order_before_insert",
    },
    "Stock Entry": {
        "before_insert": "tag_naming.tag_naming.naming.stock_entry_before_insert",
    },
    "Purchase Order": {
        "before_insert": "tag_naming.tag_naming.naming.purchase_order_before_insert",
    },
    "Material Request": {
        "before_insert": "tag_naming.tag_naming.naming.material_request_before_insert",
    },
}

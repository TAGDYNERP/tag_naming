import re
import frappe
from frappe.model.naming import getseries


# ── helpers ──────────────────────────────────────────────────────────────────

def _extract_tag_num(name):
    """Return the zero-padded TAG number from 'TAG 0500 for Acme' → '0500'."""
    m = re.match(r"^TAG (\d+)", name or "")
    return m.group(1) if m else None


def _parse_wo(wo_name):
    """Parse 'TAG 0500 P001' → ('0500', '001'). Returns (None, None) if no match."""
    m = re.match(r"^TAG (\d+) P(\d+)$", wo_name or "")
    if m:
        return m.group(1), m.group(2)
    return None, None


def _primary_wo_for_project(project_name):
    """Return the earliest non-cancelled Work Order linked to a project, or None."""
    return frappe.db.get_value(
        "Work Order",
        {"project": project_name, "docstatus": ["!=", 2]},
        "name",
        order_by="creation asc",
    )


# ── doc event handlers ────────────────────────────────────────────────────────

def _set_name(doc, name):
    """Set doc.name and flag it so set_new_name()/autoname does not overwrite it."""
    doc.name = name
    doc.flags.name_set = True


def sales_order_before_insert(doc, method=None):
    """All new Sales Orders get a sequential TAG #### name."""
    if doc.get("amended_from"):
        return  # Frappe appends -1, -2 … automatically
    num = getseries("TAG", 4)
    _set_name(doc, f"TAG {num}")


def project_before_insert(doc, method=None):
    """
    Projects linked to a TAG Sales Order inherit its number:
      TAG 0500 for {Customer}
    Projects without a TAG SO are left untouched (standard naming).
    """
    if doc.get("amended_from"):
        return

    so = doc.get("sales_order") or ""
    if not so.startswith("TAG "):
        return

    tag_num = _extract_tag_num(so)
    if not tag_num:
        return

    sales_type = doc.get("custom_sales_type") or ""
    new_name = f"TAG {tag_num} for {sales_type}" if sales_type else f"TAG {tag_num}"
    # Project autoname = field:project_name — keep them in sync
    doc.project_name = new_name
    _set_name(doc, new_name)


def work_order_before_insert(doc, method=None):
    """
    Work Orders under a TAG project get a per-project sequence:
      TAG 0500 P001, TAG 0500 P002, …
    flags.name_set = True prevents tag_manufacturing's autoname from overwriting.
    """
    if doc.get("amended_from"):
        return

    project = doc.get("project") or ""
    tag_num = _extract_tag_num(project)
    if not tag_num:
        return  # No TAG project — let tag_manufacturing's autoname run normally

    p_num = getseries(f"TAG {tag_num} P", 3)
    _set_name(doc, f"TAG {tag_num} P{p_num}")


def stock_entry_before_insert(doc, method=None):
    """
    Stock Entries linked to a TAG Work Order get a per-WO sequence:
      TAG 0500 P001 SE001, …
    """
    if doc.get("amended_from"):
        return

    wo = doc.get("work_order") or ""
    tag_num, p_num = _parse_wo(wo)
    if not tag_num:
        return

    se_num = getseries(f"{wo} SE", 3)
    _set_name(doc, f"{wo} SE{se_num}")


def purchase_order_before_insert(doc, method=None):
    """
    Purchase Orders linked to a TAG project get a per-WO PO sequence:
      TAG 0500 P001 PO001
    Falls back to project-level counter if no WO is identifiable.
    """
    if doc.get("amended_from"):
        return

    project = doc.get("project") or ""
    tag_num = _extract_tag_num(project)
    if not tag_num:
        return

    wo = _primary_wo_for_project(project)
    wo_tag, wo_p = _parse_wo(wo)
    if wo and wo_tag:
        po_num = getseries(f"{wo} PO", 3)
        _set_name(doc, f"{wo} PO{po_num}")
    else:
        po_num = getseries(f"TAG {tag_num} PO", 3)
        _set_name(doc, f"TAG {tag_num} PO{po_num}")


def material_request_before_insert(doc, method=None):
    """
    Material Requests linked to a TAG Work Order (or TAG project):
      TAG 0500 P001 MR001
    """
    if doc.get("amended_from"):
        return

    # Prefer direct WO link on the MR header
    wo = doc.get("work_order") or ""
    if wo.startswith("TAG "):
        tag_num, p_num = _parse_wo(wo)
        if tag_num:
            mr_num = getseries(f"{wo} MR", 3)
            _set_name(doc, f"{wo} MR{mr_num}")
            return

    # Fallback: project on the MR header
    project = doc.get("project") or ""
    tag_num = _extract_tag_num(project)
    if not tag_num:
        return

    wo = _primary_wo_for_project(project)
    wo_tag, wo_p = _parse_wo(wo)
    if wo and wo_tag:
        mr_num = getseries(f"{wo} MR", 3)
        _set_name(doc, f"{wo} MR{mr_num}")
    else:
        mr_num = getseries(f"TAG {tag_num} MR", 3)
        _set_name(doc, f"TAG {tag_num} MR{mr_num}")

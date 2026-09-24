import io, json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils import timezone

# PDF
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
import os


from django.db import models
from .models import LandRecord, LandOwner


# ── Font setup — Bengali (NotoSansBengali) + bold variant ───────────────────
_fonts_registered = False

def _register_bengali_fonts():
    """Register NotoSansBengali Regular + Bold for ReportLab canvas use.
    Falls back to DejaVu → FreeSans → Helvetica if unavailable."""
    global _fonts_registered
    if _fonts_registered:
        return

    candidates = [
        # NotoSansBengali (best Bengali support)
        ('/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf',
         '/usr/share/fonts/truetype/noto/NotoSansBengali-Bold.ttf'),
        # Lohit Bengali (apt fonts-beng)
        ('/usr/share/fonts/truetype/lohit-bengali/Lohit-Bengali.ttf', None),
        # DejaVu (partial Bengali)
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        # FreeSans
        ('/usr/share/fonts/truetype/freefont/FreeSans.ttf',
         '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf'),
        # macOS
        ('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', None),
    ]

    for reg_path, bold_path in candidates:
        if os.path.exists(reg_path):
            try:
                pdfmetrics.registerFont(TTFont('BnRegular', reg_path))
                if bold_path and os.path.exists(bold_path):
                    pdfmetrics.registerFont(TTFont('BnBold', bold_path))
                else:
                    # Use regular for bold too
                    pdfmetrics.registerFont(TTFont('BnBold', reg_path))
                _fonts_registered = True
                return
            except Exception:
                continue

    # Last resort — Helvetica (no Bengali, but won't crash)
    _fonts_registered = True


def _font():
    """Return (regular_font_name, bold_font_name) tuple."""
    _register_bengali_fonts()
    if _fonts_registered and 'BnRegular' in pdfmetrics.getRegisteredFontNames():
        return 'BnRegular', 'BnBold'
    return 'Helvetica', 'Helvetica-Bold'


# ── helpers ───────────────────────────────────────────────────────────────────
def _all_owners_json(record):
    """Full nested tree JSON for the JS tree picker (all levels)."""
    roots = record.get_root_owners()
    return json.dumps([o.to_dict() for o in roots], ensure_ascii=False)


# ── Land Record CRUD ──────────────────────────────────────────────────────────

def land_list(request):
    return render(request, 'lands/land_list.html',
                  {'records': LandRecord.objects.all()})


def land_create(request):
    if request.method == 'POST':
        d = request.POST
        rec = LandRecord.objects.create(
            file_no=d['file_no'], date=d['date'], area=d['area'],
            land_dag_no=d['land_dag_no'], description=d.get('description', ''),
        )
        messages.success(request, f'Land record "{rec.file_no}" created.')
        return redirect('tracker:detail', pk=rec.pk)
    return render(request, 'lands/land_form.html',
                  {'action': 'Create', 'today': timezone.now().date()})


def land_detail(request, pk):
    record = get_object_or_404(LandRecord, pk=pk)
    roots  = record.get_root_owners()
    return render(request, 'lands/land_detail.html', {
        'record':    record,
        'tree_json': json.dumps([o.to_dict() for o in roots], ensure_ascii=False),
        'root_owners': roots,
    })


def land_update(request, pk):
    record = get_object_or_404(LandRecord, pk=pk)
    if request.method == 'POST':
        d = request.POST
        record.file_no = d['file_no']; record.date = d['date']
        record.area = d['area'];       record.land_dag_no = d['land_dag_no']
        record.description = d.get('description', '')
        record.save()
        messages.success(request, 'Land record updated.')
        return redirect('tracker:detail', pk=record.pk)
    return render(request, 'lands/land_form.html',
                  {'action': 'Update', 'record': record, 'today': timezone.now().date()})


def land_delete(request, pk):
    record = get_object_or_404(LandRecord, pk=pk)
    if request.method == 'POST':
        fn = record.file_no; record.delete()
        messages.success(request, f'Land record "{fn}" deleted.')
        return redirect('tracker:list')
    return render(request, 'lands/land_confirm_delete.html', {'record': record})


# ── Owner CRUD ────────────────────────────────────────────────────────────────

def owner_add(request, land_pk):
    record = get_object_or_404(LandRecord, pk=land_pk)

    if request.method == 'POST':
        data = request.POST
        mode = data.get('mode', 'single')

        # shared parent (used by single/bulk, not join)
        parent = None
        pid = data.get('parent_id') or None
        if pid:
            parent = get_object_or_404(LandOwner, pk=pid, land=record)

        # ── BULK ─────────────────────────────────────────────────────────────
        if mode == 'bulk':
            names       = data.getlist('bulk_name')
            notes       = data.getlist('bulk_note')
            relations   = data.getlist('bulk_relation')
            step_labels = data.getlist('bulk_step_label')
            created = []
            for i, name in enumerate(names):
                name = name.strip()
                if not name: continue
                created.append(LandOwner.objects.create(
                    land=record, parent=parent, name=name,
                    note=notes[i]       if i < len(notes)       else '',
                    step_label=step_labels[i] if i < len(step_labels) else '',
                    relation=relations[i] if i < len(relations)   else '',
                    order=i,
                ))
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'count': len(created)})
            messages.success(request, f'{len(created)} owner(s) added.')
            return redirect('tracker:detail', pk=land_pk)

        # ── JOIN BELOW — new node is CHILD of ALL selected nodes ─────────────
        # Primary parent (FK) = first selected node.
        # Every other selected node is stored as an extra parent link
        # (LandOwnerExtraParent) so the SVG can draw arrows from each.
        if mode == 'join_below':
            from .models import LandOwnerExtraParent
            parent_pks_raw = data.get('join_parents', '')
            parent_pks = [
                int(p.strip()) for p in parent_pks_raw.split(',')
                if p.strip().isdigit()
            ]
            if len(parent_pks) < 2:
                messages.error(request, 'Select at least 2 parent nodes.')
                return redirect('tracker:detail', pk=land_pk)

            # Validate all selected PKs belong to this record
            parent_nodes = list(
                LandOwner.objects.filter(pk__in=parent_pks, land=record)
            )
            if len(parent_nodes) < 2:
                messages.error(request, 'Select at least 2 valid parent nodes.')
                return redirect('tracker:detail', pk=land_pk)

            # Sort by the order the user submitted them
            pk_order = {pk: i for i, pk in enumerate(parent_pks)}
            parent_nodes.sort(key=lambda n: pk_order.get(n.pk, 999))

            primary_parent = parent_nodes[0]
            extra_parents  = parent_nodes[1:]

            # New child node under primary parent
            max_order = (
                LandOwner.objects.filter(land=record, parent=primary_parent)
                                 .aggregate(m=models.Max('order'))['m'] or -1
            )
            new_node = LandOwner.objects.create(
                land=record,
                parent=primary_parent,
                name=data.get('name', '').strip(),
                note=data.get('note', ''),
                step_label=data.get('step_label', ''),
                relation=data.get('relation', ''),
                order=max_order + 1,
            )

            # Store extra parent links
            for ep in extra_parents:
                LandOwnerExtraParent.objects.get_or_create(
                    child=new_node, parent=ep
                )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'owner': new_node.to_dict()})
            parent_names = ' + '.join(n.name for n in parent_nodes)
            messages.success(
                request,
                f'Node "{new_node.name}" created below {parent_names}.'
            )
            return redirect('tracker:detail', pk=land_pk)

        # ── JOIN (legacy — kept for owner_form.html tab) ──────────────────
        # The new node must appear ABOVE the selected nodes in the tree.
        #
        # Algorithm:
        #   1. Find the common parent of all selected nodes (None = root).
        #   2. The new join node inherits the MINIMUM order of the selected
        #      nodes so it sorts before them at the same sibling level.
        #   3. Siblings that were BEFORE the selected nodes keep their orders.
        #   4. Siblings that were AFTER the selected nodes get order shifted up
        #      by 1 to make room for the new join node.
        #   5. The selected nodes are re-parented under the new join node and
        #      get fresh orders 0, 1, 2 … inside it.
        if mode == 'join':
            child_pks_raw = data.get('join_children', '')
            child_pks = [
                int(p.strip()) for p in child_pks_raw.split(',')
                if p.strip().isdigit()
            ]
            if not child_pks:
                messages.error(request, 'No nodes selected for join.')
                return redirect('tracker:owner_add', land_pk=land_pk)

            # Fetch selected nodes (evaluated now so we can read their state)
            selected_nodes = list(
                LandOwner.objects.filter(pk__in=child_pks, land=record)
                                 .order_by('order', 'created_at')
            )
            if len(selected_nodes) < 2:
                messages.error(request, 'Select at least 2 nodes to join.')
                return redirect('tracker:owner_add', land_pk=land_pk)

            # 1. Find common parent
            parent_ids = set(n.parent_id for n in selected_nodes)
            if len(parent_ids) == 1:
                common_parent_id = parent_ids.pop()
                common_parent = (
                    LandOwner.objects.get(pk=common_parent_id, land=record)
                    if common_parent_id else None
                )
            else:
                # Different branches → new node becomes a root
                common_parent = None

            # 2. New node takes the minimum order among selected siblings
            min_order = min(n.order for n in selected_nodes)

            # 3 & 4. Shift orders of non-selected siblings that come AFTER
            #        the insertion point, to make a clean gap.
            selected_pk_set = set(n.pk for n in selected_nodes)
            if common_parent is None:
                siblings = LandOwner.objects.filter(
                    land=record, parent__isnull=True
                ).exclude(pk__in=selected_pk_set).order_by('order', 'created_at')
            else:
                siblings = LandOwner.objects.filter(
                    land=record, parent=common_parent
                ).exclude(pk__in=selected_pk_set).order_by('order', 'created_at')

            # Re-number non-selected siblings: those before min_order stay,
            # those at/after get +1 gap for the new node.
            for sib in siblings:
                if sib.order >= min_order:
                    sib.order += 1
                    sib.save(update_fields=['order'])

            # 5. Create the new join node at min_order (above selected nodes)
            new_node = LandOwner.objects.create(
                land=record,
                parent=common_parent,
                name=data.get('name', '').strip(),
                note=data.get('note', ''),
                step_label=data.get('step_label', ''),
                relation=data.get('relation', ''),
                order=min_order,          # ← sits exactly where selected were
            )

            # 6. Re-parent selected nodes under new join node, fresh order
            for idx, node in enumerate(selected_nodes):
                node.parent = new_node
                node.order  = idx
                node.save(update_fields=['parent', 'order'])

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'owner': new_node.to_dict()})
            messages.success(
                request,
                f'Join node "{new_node.name}" created above '
                f'{len(selected_nodes)} node(s).'
            )
            return redirect('tracker:detail', pk=land_pk)

        # ── SINGLE ───────────────────────────────────────────────────────────
        owner = LandOwner.objects.create(
            land=record, parent=parent,
            name=data['name'], note=data.get('note', ''),
            step_label=data.get('step_label', ''),
            relation=data.get('relation', ''),
            order=int(data.get('order', 0)),
        )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'owner': owner.to_dict()})
        messages.success(request, f'Owner "{owner.name}" added.')
        return redirect('tracker:detail', pk=land_pk)

    # ── GET ───────────────────────────────────────────────────────────────────
    pid = request.GET.get('parent_id')
    parent = get_object_or_404(LandOwner, pk=pid, land=record) if pid else None

    return render(request, 'lands/owner_form.html', {
        'record':         record,
        'parent':         parent,
        'action':         'Add',
        'all_owners_json': _all_owners_json(record),   # full nested tree
    })


def owner_update(request, land_pk, owner_pk):
    record = get_object_or_404(LandRecord, pk=land_pk)
    owner  = get_object_or_404(LandOwner, pk=owner_pk, land=record)
    if request.method == 'POST':
        d = request.POST
        owner.name = d['name']; owner.note = d.get('note', '')
        owner.step_label = d.get('step_label', '')
        owner.relation   = d.get('relation', '')
        owner.order      = int(d.get('order', 0))
        owner.save()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'owner': owner.to_dict()})
        messages.success(request, f'Owner "{owner.name}" updated.')
        return redirect('tracker:detail', pk=land_pk)
    return render(request, 'lands/owner_form.html',
                  {'record': record, 'owner': owner, 'action': 'Update'})


def owner_delete(request, land_pk, owner_pk):
    record = get_object_or_404(LandRecord, pk=land_pk)
    owner  = get_object_or_404(LandOwner, pk=owner_pk, land=record)
    if request.method == 'POST':
        name = owner.name; owner.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        messages.success(request, f'Owner "{name}" and all heirs deleted.')
        return redirect('tracker:detail', pk=land_pk)
    return render(request, 'lands/owner_confirm_delete.html',
                  {'record': record, 'owner': owner})


# ── AJAX tree ─────────────────────────────────────────────────────────────────

def tree_json(request, land_pk):
    record = get_object_or_404(LandRecord, pk=land_pk)
    return JsonResponse({'tree': [o.to_dict() for o in record.get_root_owners()]})


# ── PDF export ────────────────────────────────────────────────────────────────
# Visual tree on canvas with full Bengali font support.

def _build_pdf_buffer(record):
    """
    Landscape A4 PDF:
      1. Bismillah + title heading
      2. LandRecord metadata table
      3. Visual ownership tree — coloured boxes + bezier arrows
    All text rendered with NotoSansBengali so Bengali is displayed correctly.
    Returns (BytesIO, font_regular_name).
    """
    font_reg, font_bold = _font()

    buf  = io.BytesIO()
    W, H = landscape(A4)
    c    = rl_canvas.Canvas(buf, pagesize=(W, H))

    # ── colour palette per depth ──────────────────────────────────────────────
    DEPTH_FILLS = [
        (0.18, 0.42, 0.31),   # 0  dark green
        (0.12, 0.30, 0.55),   # 1  dark blue
        (0.49, 0.23, 0.93),   # 2  purple
        (0.71, 0.33, 0.04),   # 3  amber
        (0.06, 0.47, 0.43),   # 4  teal
        (0.75, 0.09, 0.36),   # 5  pink
    ]
    def depth_fill(d): return DEPTH_FILLS[d % len(DEPTH_FILLS)]

    # ── layout constants ──────────────────────────────────────────────────────
    ML = 1.4 * cm;  MR = 1.4 * cm
    MT = H - 1.4 * cm          # top y (canvas y increases upward)
    MB = 1.2 * cm

    BW   = 3.8 * cm    # box width
    BH   = 1.05 * cm   # box height
    GAPX = 0.55 * cm   # horizontal gap between siblings
    GAPY = 1.55 * cm   # vertical gap between levels

    # helper: draw string clipped to max_chars
    def bn(text, max_ch=40):
        """Return text safely truncated."""
        if not text: return ""
        return text if len(text) <= max_ch else text[:max_ch-1] + "…"

    # ── 1. HEADER ─────────────────────────────────────────────────────────────
    y = MT

    c.setFont(font_bold, 13)
    c.setFillColorRGB(0.49, 0.23, 0.93)
    c.drawCentredString(W / 2, y, "বিসমিল্লাহির রাহমানির রাহিম")
    y -= 0.6 * cm

    c.setFont(font_bold, 12)
    c.setFillColorRGB(0.12, 0.23, 0.37)
    c.drawCentredString(W / 2, y,
        f"ভূমি মালিকানা রেকর্ড  —  {record.file_no}")
    y -= 0.3 * cm

    c.setStrokeColorRGB(0.12, 0.23, 0.37)
    c.setLineWidth(1.2)
    c.line(ML, y, W - MR, y)
    y -= 0.45 * cm

    # ── 2. METADATA TABLE ─────────────────────────────────────────────────────
    meta = [
        ("ফাইল নং",       record.file_no),
        ("তারিখ",         record.date.strftime("%d-%m-%Y") if record.date else "—"),
        ("এলাকা",         record.area),
        ("দাগ নং",        record.land_dag_no),
    ]
    if record.description:
        meta.append(("বিবরণ", record.description[:100]))

    col_w   = (W - ML - MR) / 2
    row_h   = 0.56 * cm
    label_w = col_w * 0.30
    val_w   = col_w - label_w

    pairs = [(meta[i], meta[i+1] if i+1 < len(meta) else ("", ""))
             for i in range(0, len(meta), 2)]

    for left, right in pairs:
        # left label
        c.setFillColorRGB(0.88, 0.92, 1.0)
        c.rect(ML, y - row_h, label_w, row_h, fill=1, stroke=0)
        c.setFillColorRGB(0.12, 0.23, 0.37)
        c.setFont(font_bold, 7.5)
        c.drawString(ML + 3, y - row_h + 4, left[0])
        # left value
        c.setFillColorRGB(0.08, 0.08, 0.08)
        c.setFont(font_reg, 8)
        c.drawString(ML + label_w + 4, y - row_h + 4, bn(str(left[1]), 50))
        # grid
        c.setStrokeColorRGB(0.78, 0.83, 0.92)
        c.setLineWidth(0.3)
        c.rect(ML, y - row_h, col_w, row_h, fill=0, stroke=1)

        # right side
        if right[0]:
            rx = ML + col_w
            c.setFillColorRGB(0.88, 0.92, 1.0)
            c.rect(rx, y - row_h, label_w, row_h, fill=1, stroke=0)
            c.setFillColorRGB(0.12, 0.23, 0.37)
            c.setFont(font_bold, 7.5)
            c.drawString(rx + 3, y - row_h + 4, right[0])
            c.setFillColorRGB(0.08, 0.08, 0.08)
            c.setFont(font_reg, 8)
            c.drawString(rx + label_w + 4, y - row_h + 4, bn(str(right[1]), 50))
            c.setStrokeColorRGB(0.78, 0.83, 0.92)
            c.setLineWidth(0.3)
            c.rect(rx, y - row_h, col_w, row_h, fill=0, stroke=1)

        y -= row_h

    y -= 0.45 * cm

    # Section heading
    c.setFont(font_bold, 9)
    c.setFillColorRGB(0.12, 0.23, 0.37)
    c.drawString(ML, y, "উত্তরাধিকার / মালিকানা গাছ  (Ownership Tree)")
    y -= 0.28 * cm
    c.setStrokeColorRGB(0.58, 0.63, 0.72)
    c.setLineWidth(0.5)
    c.line(ML, y, W - MR, y)
    y -= 0.45 * cm

    tree_top = y

    # ── 3. TREE LAYOUT ────────────────────────────────────────────────────────
    all_nodes = []

    def _walk(owner, depth):
        node = {
            "id":              owner.id,
            "name":            owner.name or "",
            "note":            owner.note or "",
            "step_label":      owner.step_label or "",
            "relation":        owner.relation or "",
            "parent_id":       owner.parent_id,
            "depth":           depth,
            "extra_parent_ids": [],
        }
        try:
            node["extra_parent_ids"] = list(
                owner.extra_parent_links.values_list("parent_id", flat=True)
            )
        except Exception:
            pass
        all_nodes.append(node)
        for child in owner.children.all().order_by("order", "created_at"):
            _walk(child, depth + 1)
        return node

    for r in record.get_root_owners():
        _walk(r, 0)

    if not all_nodes:
        c.setFont(font_reg, 10)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(W / 2, tree_top - 1.5 * cm,
                            "কোনো মালিক যোগ করা হয়নি।  (No owners yet)")
        c.save(); buf.seek(0)
        return buf, font_reg

    # Group by depth and assign x/y
    by_depth = {}
    for n in all_nodes:
        by_depth.setdefault(n["depth"], []).append(n)

    usable_x = W - ML - MR
    for depth, level in sorted(by_depth.items()):
        count   = len(level)
        total_w = count * BW + (count - 1) * GAPX
        start_x = ML + max(0, (usable_x - total_w) / 2)
        for i, n in enumerate(level):
            n["_x"] = start_x + i * (BW + GAPX)
            n["_y"] = tree_top - depth * (BH + GAPY)

    by_id = {n["id"]: n for n in all_nodes}

    # ── 4. DRAW EDGES ─────────────────────────────────────────────────────────
    def arrowhead(x, y, amber=False, size=3.5):
        c.saveState()
        c.translate(x, y)
        c.setFillColorRGB(0.96, 0.62, 0.04) if amber else c.setFillColorRGB(0.55, 0.60, 0.70)
        p = c.beginPath()
        p.moveTo(0, 0); p.lineTo(-size/2, size); p.lineTo(size/2, size); p.close()
        c.drawPath(p, stroke=0, fill=1)
        c.restoreState()

    def draw_edge(x1, y1, x2, y2, dashed=False, amber=False):
        if amber:
            c.setStrokeColorRGB(0.96, 0.62, 0.04)
        else:
            c.setStrokeColorRGB(0.55, 0.60, 0.70)
        c.setLineWidth(1.1)
        c.setDash([4, 3] if dashed else [])
        mid_y = (y1 + y2) / 2
        p = c.beginPath()
        p.moveTo(x1, y1)
        p.curveTo(x1, mid_y, x2, mid_y, x2, y2)
        c.drawPath(p, stroke=1, fill=0)
        c.setDash([])
        arrowhead(x2, y2, amber=amber)

    for n in all_nodes:
        if n["parent_id"] and n["parent_id"] in by_id:
            p = by_id[n["parent_id"]]
            draw_edge(p["_x"]+BW/2, p["_y"],
                      n["_x"]+BW/2, n["_y"]+BH,
                      dashed=False, amber=False)
        for ep_id in n.get("extra_parent_ids", []):
            if ep_id in by_id:
                p = by_id[ep_id]
                draw_edge(p["_x"]+BW/2, p["_y"],
                          n["_x"]+BW/2, n["_y"]+BH,
                          dashed=True, amber=True)

    # ── 5. DRAW NODE BOXES ────────────────────────────────────────────────────
    RADIUS = 0.22 * cm

    for n in all_nodes:
        x, yb  = n["_x"], n["_y"]
        fill   = depth_fill(n["depth"])
        is_join = bool(n.get("extra_parent_ids"))

        # Box
        c.setFillColorRGB(*fill)
        if is_join:
            c.setStrokeColorRGB(0.96, 0.62, 0.04); c.setLineWidth(2.0)
        else:
            c.setStrokeColorRGB(*[f * 0.68 for f in fill]); c.setLineWidth(0.8)
        c.roundRect(x, yb, BW, BH, RADIUS, fill=1, stroke=1)

        # Note badge top-right
        if n["note"].strip():
            c.setFillColorRGB(1, 1, 1)
            c.circle(x + BW - 4*mm, yb + BH - 4*mm, 2.8*mm, fill=1, stroke=0)
            c.setFillColorRGB(*fill)
            c.setFont(font_bold, 5)
            c.drawCentredString(x + BW - 4*mm, yb + BH - 4*mm - 1.5, "N")

        # Join badge top-left
        if is_join:
            c.setFillColorRGB(0.96, 0.62, 0.04)
            c.circle(x + 4*mm, yb + BH - 4*mm, 2.8*mm, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.setFont(font_bold, 5)
            c.drawCentredString(x + 4*mm, yb + BH - 4*mm - 1.5, "J")

        # ── Name text (Bengali) ───────────────────────────────────────────────
        c.setFillColorRGB(1, 1, 1)
        sub = n["relation"] or n["step_label"]
        name_y = yb + BH/2 + (3.5 if sub else 1.5)

        # name — bold Bengali
        name_txt = bn(n["name"], 18)
        c.setFont(font_bold, 7.5)
        c.drawCentredString(x + BW/2, name_y, name_txt)

        # sub-label — relation or step (regular Bengali, smaller)
        if sub:
            c.setFont(font_reg, 6.5)
            c.setFillColorRGB(1, 1, 0.82)
            c.drawCentredString(x + BW/2, yb + BH/2 - 5, bn(sub, 22))

    # ── 6. FOOTER ─────────────────────────────────────────────────────────────
    c.setFont(font_reg, 7)
    c.setFillColorRGB(0.55, 0.55, 0.55)
    gen = timezone.now().strftime("%d %B %Y, %H:%M")
    c.drawRightString(W - MR, MB,
        f"তৈরির সময়: {gen}  —  BTP Land Tracker")
    c.drawString(ML, MB, "পৃষ্ঠা ১")

    c.save()
    buf.seek(0)
    return buf, font_reg


def land_pdf_view(request, pk):
    """Open PDF inline in the browser."""
    record = get_object_or_404(LandRecord, pk=pk)
    buf, _ = _build_pdf_buffer(record)
    fname  = f"land_{record.file_no.replace(' ','_')}.pdf"
    resp   = HttpResponse(buf, content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="{fname}"'
    return resp


def land_pdf_download(request, pk):
    """Force-download the PDF."""
    record = get_object_or_404(LandRecord, pk=pk)
    buf, _ = _build_pdf_buffer(record)
    fname  = f"land_{record.file_no.replace(' ','_')}.pdf"
    resp   = HttpResponse(buf, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="{fname}"'
    return resp

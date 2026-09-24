from django.db import models
from django.utils import timezone


class LandRecord(models.Model):
    """Main land record with file metadata."""
    file_no     = models.CharField(max_length=100, unique=True, verbose_name="File No")
    date        = models.DateField(default=timezone.now, verbose_name="Date")
    area        = models.CharField(max_length=200, verbose_name="Area / Location")
    mouza_name  = models.CharField(max_length=100, verbose_name="Mouza Name", blank=True, default="")
    cs_dag_no = models.CharField(max_length=100, verbose_name="CS Dag No", blank=True, default="")
    sa_dag_no  = models.CharField(max_length=100, verbose_name="SA Dag No", blank=True, default="")
    rs_dag_no  = models.CharField(max_length=100, verbose_name="RS Dag No", blank=True, default="")
    ct_dag_no  = models.CharField(max_length=100, verbose_name="CT Dag No", blank=True, default="")
    description = models.TextField(blank=True, verbose_name="Description")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Land Record"
        verbose_name_plural = "Land Records"

    def __str__(self):
        return f"{self.file_no} - {self.area}"

    def get_root_owners(self):
        return self.owners.filter(parent__isnull=True).order_by('order')


class LandOwner(models.Model):
    """Hierarchical owner/inheritor node — supports unlimited nesting."""
    land   = models.ForeignKey(LandRecord, on_delete=models.CASCADE, related_name='owners')
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.CASCADE, related_name='children'
    )
    name       = models.CharField(max_length=300, verbose_name="Owner Name")
    dagno      = models.CharField(max_length=300, blank=True, default="")
    share      = models.CharField(max_length=300, blank=True, default="")
    note       = models.TextField(blank=True, verbose_name="Note / Description")
    step_label = models.CharField(max_length=200, blank=True, verbose_name="Step Label")
    relation   = models.CharField(max_length=200, blank=True, verbose_name="Relation")
    order      = models.PositiveIntegerField(default=0, verbose_name="Display Order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Land Owner"
        verbose_name_plural = "Land Owners"

    def __str__(self):
        return f"{self.name} ({self.land.file_no})"

    def get_depth(self):
        depth, node = 0, self
        while node.parent:
            depth += 1
            node = node.parent
        return depth

    def get_ancestors(self):
        ancestors, node = [], self.parent
        while node:
            ancestors.insert(0, node)
            node = node.parent
        return ancestors

    def to_dict(self):
        """Serialize to dict for JSON tree rendering.
        Includes extra_parent_ids for multi-parent join nodes."""
        extra_ids = list(
            self.extra_parent_links.values_list('parent_id', flat=True)
        )
        return {
            'id':               self.id,
            'name':             self.name,
            'dagno':            self.dagno,
            'share':             self.share,
            'note':             self.note,
            'step_label':       self.step_label,
            'relation':         self.relation,
            'order':            self.order,
            'parent_id':        self.parent_id,
            'extra_parent_ids': extra_ids,   # ← additional parent links
            'depth':            self.get_depth(),
            'children': [
                child.to_dict()
                for child in self.children.all().order_by('order')
            ],
        }


class LandOwnerExtraParent(models.Model):
    """
    Extra parent links for Join Root nodes.
    Primary parent lives in LandOwner.parent (FK).
    Additional parents (2nd, 3rd …) are stored here.
    """
    child  = models.ForeignKey(
        LandOwner, on_delete=models.CASCADE, related_name='extra_parent_links'
    )
    parent = models.ForeignKey(
        LandOwner, on_delete=models.CASCADE, related_name='extra_child_links'
    )

    class Meta:
        unique_together = ('child', 'parent')
        verbose_name = "Extra Parent Link"

    def __str__(self):
        return f"{self.parent.name} → {self.child.name}"

"""A material template."""
from taurus.entity.object import MaterialRun
from taurus.entity.object.material_spec import MaterialSpec
from taurus.entity.template.base_template import BaseTemplate
from taurus.entity.template.has_property_templates import HasPropertyTemplates


class MaterialTemplate(BaseTemplate, HasPropertyTemplates):
    """Template for Materials: MaterialSpec and MaterialRun, containing property templates."""

    typ = "material_template"

    def __init__(self, name=None, description=None, properties=None, uids=None, tags=None):
        BaseTemplate.__init__(self, name, description, uids, tags)
        HasPropertyTemplates.__init__(self, properties)

    def validate(self, material):
        """Check that a material satisfies all property templates."""
        if not isinstance(material, (MaterialRun, MaterialSpec)):
            raise ValueError("MaterialTemplate can only be applied to Materials")
        self.validate_properties(material)
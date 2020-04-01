import inspect

from gemd.entity.attribute.condition import Condition
from gemd.entity.attribute.parameter import Parameter
from gemd.entity.attribute.property import Property
from gemd.entity.attribute.property_and_conditions import PropertyAndConditions
from gemd.entity.base_entity import BaseEntity
from gemd.entity.bounds.categorical_bounds import CategoricalBounds
from gemd.entity.bounds.composition_bounds import CompositionBounds
from gemd.entity.bounds.integer_bounds import IntegerBounds
from gemd.entity.bounds.real_bounds import RealBounds
from gemd.entity.file_link import FileLink
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object import ProcessRun, MaterialRun, MeasurementRun
from gemd.entity.object.ingredient_run import IngredientRun
from gemd.entity.object.ingredient_spec import IngredientSpec
from gemd.entity.object.material_spec import MaterialSpec
from gemd.entity.object.measurement_spec import MeasurementSpec
from gemd.entity.object.process_spec import ProcessSpec
from gemd.entity.source.performed_source import PerformedSource
from gemd.entity.template.condition_template import ConditionTemplate
from gemd.entity.template.material_template import MaterialTemplate
from gemd.entity.template.measurement_template import MeasurementTemplate
from gemd.entity.template.parameter_template import ParameterTemplate
from gemd.entity.template.process_template import ProcessTemplate
from gemd.entity.template.property_template import PropertyTemplate
from gemd.entity.value.discrete_categorical import DiscreteCategorical
from gemd.entity.value.empirical_formula import EmpiricalFormula
from gemd.entity.value.nominal_categorical import NominalCategorical
from gemd.entity.value.nominal_composition import NominalComposition
from gemd.entity.value.nominal_integer import NominalInteger
from gemd.entity.value.nominal_real import NominalReal
from gemd.entity.value.normal_real import NormalReal
from gemd.entity.value.uniform_integer import UniformInteger
from gemd.entity.value.uniform_real import UniformReal
from gemd.json import GEMDEncoder
from gemd.util import flatten, substitute_links, set_uuids
import json as json_builtin


class GEMDJson(object):
    """
    Class that provides json load/dump functionality that is compatible with gemd objects.

    The serialization and deserialization strategy implemented by this class is described in
    :ref:`Serialization In Depth`
    """

    _clazzes = [
        MaterialTemplate, MeasurementTemplate, ProcessTemplate,
        MaterialSpec, MeasurementSpec, ProcessSpec, IngredientSpec,
        ProcessRun, MaterialRun, MeasurementRun, IngredientRun,
        Property, Condition, Parameter, PropertyAndConditions,
        PropertyTemplate, ConditionTemplate, ParameterTemplate,
        RealBounds, IntegerBounds, CategoricalBounds, CompositionBounds,
        NominalComposition, EmpiricalFormula,
        NominalReal, UniformReal, NormalReal, DiscreteCategorical, NominalCategorical,
        UniformInteger, NominalInteger,
        FileLink, PerformedSource
    ]

    _link_type = LinkByUID

    def __init__(self):
        self._clazz_index = {}
        # build index from the class's typ member to the class itself
        for clazz in self._clazzes:
            self._clazz_index[clazz.typ] = clazz

    def dumps(self, obj, **kwargs):
        """
        Serialize a gemd object, or container of them, into a json-formatting string.

        Parameters
        ----------
        obj: DictSerializable or List[DictSerializable]
            The object(s) to serialize to a string.
        **kwargs: keyword args, optional
            Optional keyword arguments to pass to `json.dumps()`.

        Returns
        -------
        str
            A string version of the serialized objects.

        """
        # create a top level list of [flattened_objects, link-i-fied return value]
        res = {"object": obj}
        additional = flatten(res)
        res = substitute_links(res)
        res["context"] = additional
        return json_builtin.dumps(res, cls=GEMDEncoder, sort_keys=True, **kwargs)

    def loads(self, json_str, **kwargs):
        """
        Deserialize a json-formatted string into a gemd object.

        Parameters
        ----------
        json_str: str
            A string representing the serialized objects, like what is produced by :func:`dumps`.
        **kwargs: keyword args, optional
            Optional keyword arguments to pass to `json.loads()`.

        Returns
        -------
        DictSerializable or List[DictSerializable]
            Deserialized versions of the objects represented by `json_str`, with links turned
            back into pointers.

        """
        # Create an index to hold the objects by their uid reference
        # so we can replace links with pointers
        index = {}
        raw = json_builtin.loads(
            json_str, object_hook=lambda x: self._load_and_index(x, index, True), **kwargs)
        # the return value is in the 2nd position.
        return raw["object"]

    def load(self, fp, **kwargs):
        """
        Load serialized string representation of an object from a file.

        Parameters
        ----------
        fp: file
            File to read.
        **kwargs: keyword args, optional
            Optional keyword arguments to pass to `json.loads()`.

        Returns
        -------
        DictSerializable or List[DictSerializable]
            Deserialized object(s).

        """
        return self.loads(fp.read(), **kwargs)

    def dump(self, obj, fp, **kwargs):
        """
        Dump an object to a file, as a serialized string.

        Parameters
        ----------
        obj: DictSerializable or List[DictSerializable]
            Object(s) to dump
        fp: file
            File to write to.
        **kwargs: keyword args, optional
            Optional keyword arguments to pass to `json.dumps()`.

        Returns
        -------
        None

        """
        fp.write(self.dumps(obj, **kwargs))
        return

    def copy(self, obj):
        """
        Copy an object by dumping and then loading it.

        Parameters
        ----------
        obj: DictSerializable
            Object to copy

        Returns
        -------
        DictSerializable
            A copy of `obj`.

        """
        return self.loads(self.dumps(obj))

    def raw_dumps(self, obj, **kwargs):
        """
        Serialize the object as-is, which could be as a nested object.

        Parameters
        ----------
        obj:
            Object to dump
        **kwargs: keyword args, optional
            Optional keyword arguments to pass to `json.dumps()`.

        Returns
        -------
        str
            A serialized string of `obj`, which could be nested

        """
        return json_builtin.dumps(obj, cls=GEMDEncoder, sort_keys=True, **kwargs)

    def thin_dumps(self, obj, **kwargs):
        """
        Serialize a "thin" version of an object in which pointers are replaced by links.

        Parameters
        ----------
        obj:
            Object to dump
        **kwargs: keyword args, optional
            Optional keyword arguments to pass to `json.dumps()`.

        Returns
        -------
        str
            A serialized string of `obj`, with link_by_uid in place of pointers to other objects.

        """
        set_uuids(obj)
        res = substitute_links(obj)
        return json_builtin.dumps(res, cls=GEMDEncoder, sort_keys=True, **kwargs)

    def raw_loads(self, json_str, **kwargs):
        """
        Deserialize a json-formatted string with no context into a gemd object as-is.

        Parameters
        ----------
        json_str: str
            A string representing the serialized objects, like what is produced by :func:`dumps`.
        **kwargs: keyword args, optional
            Optional keyword arguments to pass to `json.loads()`.

        Returns
        -------
        DictSerializable or List[DictSerializable]
            Deserialized versions of the objects represented by `json_str`

        """
        # Create an index to hold the objects by their uid reference
        # so we can replace links with pointers
        index = {}
        return json_builtin.loads(
            json_str, object_hook=lambda x: self._load_and_index(x, index), **kwargs)

    def register_classes(self, classes):
        """
        Register additional classes to the custom deserialization object hook.

        This allows for additional DictSerializable subclasses to be registered to the class index
        that is used to decode the type strings.  Existing keys are overwritten, allowing classes
        in the gemd package to be subclassed and overridden in the class index by their
        subclass.

        :param classes: a dict mapping the type string to the class
        :return: None
        """
        if not isinstance(classes, dict):
            raise ValueError("Must be given a dict from str -> class")
        non_string_keys = [x for x in classes.keys() if not isinstance(x, str)]
        if len(non_string_keys) > 0:
            raise ValueError(
                "The keys must be strings, but got {} as keys".format(non_string_keys))
        non_class_values = [x for x in classes.values() if not inspect.isclass(x)]
        if len(non_class_values) > 0:
            raise ValueError(
                "The values must be classes, but got {} as values".format(non_class_values))

        self._clazz_index.update(classes)

    def _load_and_index(self, d, object_index, substitute=False):
        """
        Load the class based on the type string and index it, if a BaseEntity.

        This function is used as the object hook when deserializing gemd objects

        :param d: dictionary to try to load into a registered class instance
        :param object_index: to add the object to if it is a BaseEntity
        :param substitute: whether to substitute LinkByUIDs when they are found in the index
        :return: the deserialized object, or the input dict if it wasn't recognized
        """
        if "type" not in d:
            return d
        typ = d.pop("type")

        if typ in self._clazz_index:
            clz = self._clazz_index[typ]
            obj = clz.from_dict(d)
        elif typ == self._link_type.typ:
            obj = self._link_type.from_dict(d)
            if substitute and (obj.scope.lower(), obj.id) in object_index:
                return object_index[(obj.scope.lower(), obj.id)]
            return obj
        else:
            raise TypeError("Unexpected base object type: {}".format(typ))

        if isinstance(obj, BaseEntity):
            for (scope, uid) in obj.uids.items():
                object_index[(scope.lower(), uid)] = obj
        return obj
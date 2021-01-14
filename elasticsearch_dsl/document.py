#  Licensed to Elasticsearch B.V. under one or more contributor
#  license agreements. See the NOTICE file distributed with
#  this work for additional information regarding copyright
#  ownership. Elasticsearch B.V. licenses this file to you under
#  the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.

from six import add_metaclass, iteritems

from .field import Field
from .mapping import Mapping
from .utils import ObjectBase


class MetaField(object):
    def __init__(self, *args, **kwargs):
        self.args, self.kwargs = args, kwargs


class DocumentMeta(type):
    def __new__(cls, name, bases, attrs):
        # DocumentMeta filters attrs in place
        attrs["_doc_type"] = DocumentOptions(name, bases, attrs)
        return super(DocumentMeta, cls).__new__(cls, name, bases, attrs)


class DocumentOptions(object):
    def __init__(self, name, bases, attrs):
        meta = attrs.pop("Meta", None)

        # create the mapping instance
        self.mapping = getattr(meta, "mapping", Mapping())

        # register all declared fields into the mapping
        for name, value in list(iteritems(attrs)):
            if isinstance(value, Field):
                self.mapping.field(name, value)
                del attrs[name]

        # add all the mappings for meta fields
        for name in dir(meta):
            if isinstance(getattr(meta, name, None), MetaField):
                params = getattr(meta, name)
                self.mapping.meta(name, *params.args, **params.kwargs)

        # document inheritance - include the fields from parents' mappings
        for b in bases:
            if hasattr(b, "_doc_type") and hasattr(b._doc_type, "mapping"):
                self.mapping.update(b._doc_type.mapping, update_only=True)

    @property
    def name(self):
        return self.mapping.properties.name


@add_metaclass(DocumentMeta)
class InnerDoc(ObjectBase):
    """
    Common class for inner documents like Object or Nested
    """

    @classmethod
    def from_es(cls, data, data_only=False):
        if data_only:
            data = {"_source": data}
        return super(InnerDoc, cls).from_es(data)


from ._sync import Document, IndexMeta

__all__ = [
    "Document",
    "DocumentMeta",
    "DocumentOptions",
    "InnerDoc",
    "IndexMeta",
    "MetaField",
]

try:
    from ._async import AsyncDocument, AsyncIndexMeta  # noqa: F401

    __all__.extend(["AsyncDocument", "AsyncIndexMeta"])
except ImportError:
    pass

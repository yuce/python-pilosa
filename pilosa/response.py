from .exceptions import PilosaError
from .internal import public_pb2 as internal


class BitmapResult:

    def __init__(self, bits=None, attributes=None):
        self.bits = bits or []
        self.attributes = attributes or {}

    @classmethod
    def from_internal(cls, obj):
        return cls(list(obj.Bits), _convert_protobuf_attrs_to_dict(obj.Attrs))


class CountResultItem:

    def __init__(self, id, count):
        self.id = id
        self.count = count


class QueryResult:

    def __init__(self, bitmap=None, count_items=None, count=0):
        self.bitmap = bitmap or BitmapResult()
        self.count_items = count_items or []
        self.count = count

    @classmethod
    def from_internal(cls, obj):
        count_items = []
        for pair in obj.Pairs:
            count_items.append(CountResultItem(pair.Key, pair.Count))
        return cls(BitmapResult.from_internal(obj.Bitmap), count_items, obj.N)


class ProfileItem:

    def __init__(self, id, attributes):
        self.id = id
        self.attributes = attributes

    @classmethod
    def from_internal(cls, obj):
        return cls(obj.ID, _convert_protobuf_attrs_to_dict(obj.Attrs))


class QueryResponse(object):

    def __init__(self, results=None, profiles=None, error_message=""):
        self.results = results or []
        self.profiles = profiles or []
        self.error_message = error_message

    @classmethod
    def from_protobuf(cls, bin):
        response = internal.QueryResponse()
        response.ParseFromString(bin)
        results = [QueryResult.from_internal(r) for r in response.Results]
        profiles = [ProfileItem.from_internal(p) for p in response.ColumnAttrSets]
        error_message = response.Err
        return cls(results, profiles, error_message)

    @property
    def result(self):
        return self.results[0] if self.results else None

    @property
    def profile(self):
        return self.profiles[0] if self.profiles else None


def _convert_protobuf_attrs_to_dict(attrs):
    protobuf_attrs_to_dict = [
        None,
        lambda a: a.StringValue,
        lambda a: a.IntValue,
        lambda a: a.BoolValue,
        lambda a: a.FloatValue,
    ]
    d = {}
    attr = None  # to get the attr with invalid type
    try:
        for attr in attrs:
            value = protobuf_attrs_to_dict[attr.Type](attr)
            d[attr.Key] = value
    except (IndexError, TypeError):
        raise PilosaError("Invalid protobuf attribute type: %s" % attr.Type)
    return d

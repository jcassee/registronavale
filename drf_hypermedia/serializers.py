import copy

from django.db import models
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.reverse import reverse
from rest_framework.utils.serializer_helpers import ReturnDict

from registronavale import profiles
from registronavale import relations


class HalSerializer(serializers.Serializer):
    class Meta:
        view_name = None
        profile = None

    def __init__(self, instance=None, data=empty, include_embedded=True, **kwargs):
        self.include_embedded = include_embedded
        super(HalSerializer, self).__init__(instance, data, **kwargs)

    def get_initial(self):
        initial = super(HalSerializer, self).get_initial()
        return self.to_representation(initial)

    def to_representation(self, instance, include_embedded=True):
        ret = super(HalSerializer, self).to_representation(instance)

        links = self.get_links(self.context['request'], instance)
        if links is None:
            links = {}
        if relations.SELF not in links and getattr(self.Meta, 'view_name', None) is not None:
            if hasattr(self.Meta, 'model'):
                lookup_field = getattr(self.Meta, 'lookup_field', 'pk')
                kwargs = {lookup_field: getattr(instance, lookup_field)}
            else:
                kwargs = None
            links[relations.SELF] = {'href': reverse(self.Meta.view_name, kwargs=kwargs, request=self.context['request'])}
        if relations.PROFILE not in links and getattr(self.Meta, 'profile', None) is not None:
            links[relations.PROFILE] = {'href': self.Meta.profile}
        ret['_links'] = links

        if include_embedded and self.include_embedded:
            embedded = self.get_embedded(self.context['request'], instance)
            if embedded:
                ret['_embedded'] = embedded

        return ret

    def get_links(self, request, instance=None):
        return None

    def get_embedded(self, request, instance=None):
        return None


class HalCollectionSerializer(HalSerializer):
    child = None

    def __init__(self, *args, **kwargs):
        self.child = kwargs.pop('child', copy.deepcopy(self.child))
        super(HalCollectionSerializer, self).__init__(*args, **kwargs)
        self.child.bind(field_name='', parent=self)

    def get_links(self, request, instance=None):
        return {
            relations.PROFILE: {
                'href': profiles.COLLECTION,
            },
            relations.SELF: {
                'href': request.build_absolute_uri(),
            },
        }

    def get_embedded(self, request, instance=None):
        iterable = instance.all() if isinstance(instance, models.Manager) else instance
        elements = [self.child.to_representation(item, include_embedded=False) for item in iterable]
        if elements:
            return {
                'item': elements
            }
        else:
            return None
